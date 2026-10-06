"""Local practice dashboard. Manual status controls never edit Excel or place orders."""
import json
import math
import sys
from datetime import date
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file
from waitress import serve

from app_support import configure_logging, log_event
from config import ConfigManager, project_root
from data_provider import MarketDataError
from main import AnalysisBusy, run_analysis as execute_analysis
from journal_state import JournalStatusError, JournalStatusStore, journal_entry_ids, journal_kpis, read_journal

PROJECT_ROOT = str(project_root())
RESOURCE_DIR = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parent


def create_app(config_manager=None, analysis_runner=None):
    manager = config_manager or ConfigManager()
    runner = analysis_runner or execute_analysis
    status_store = JournalStatusStore(manager.output_dir)
    application = Flask(__name__, template_folder=str(RESOURCE_DIR / "templates"), static_folder=str(RESOURCE_DIR / "static"))
    application.config["MAX_CONTENT_LENGTH"] = 16 * 1024
    application.config["LAST_SCAN_ERROR"] = None
    configure_logging(manager.output_dir.parent)
    log_event("application_started", mode="sensibull_practice")

    @application.template_filter("number")
    def number(value, digits=2):
        try:
            value = float(value)
            return f"{value:,.{int(digits)}f}" if math.isfinite(value) else "—"
        except (TypeError, ValueError):
            return "—"

    @application.after_request
    def after_request(response):
        if not request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-store"
            log_event("dashboard_request", method=request.method, path=request.path, status=response.status_code)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    def read_result():
        file = manager.output_dir / "result.json"
        error = None
        data = {}
        if file.exists():
            try:
                with file.open(encoding="utf-8") as handle:
                    data = json.load(handle, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
                if not isinstance(data, dict):
                    raise ValueError("Result must be an object")
                for name in ("bull_put", "bear_call"):
                    rows = data.get(name, [])
                    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
                        raise ValueError("Invalid strategy records")
                    for row in rows:
                        if not all(key in row and isinstance(row[key], (int, float)) and math.isfinite(row[key])
                                   for key in ("Rank", "NetCredit", "MaxProfit", "MaxLoss", "EstimatedPOP", "ReturnOnRisk")):
                            raise ValueError("Invalid strategy metrics")
                        if row["Rank"] < 1 or row["MaxLoss"] <= 0 or row["NetCredit"] <= 0:
                            raise ValueError("Invalid strategy risk")
                if data.get("market") is not None and not isinstance(data.get("market"), dict):
                    raise ValueError("Invalid market data")
                if not isinstance(data.get("warnings", []), list):
                    raise ValueError("Invalid warnings")
                if not isinstance(data.get("option_chain", []), list) or not all(isinstance(row, dict) for row in data.get("option_chain", [])):
                    raise ValueError("Invalid option chain")
            except (OSError, ValueError, TypeError):
                data = {}
                error = "Saved result is unavailable or malformed. Run the selected CSV again."
        status = "NO SCAN"
        if data:
            status = data.get("data_status", "SAVED RESULT")
            try:
                expiry = date.fromisoformat(data["expiry_date"])
                if expiry <= date.today():
                    status = "EXPIRED SNAPSHOT"
            except (KeyError, TypeError, ValueError):
                status = "UNKNOWN EXPIRY"
        if error:
            status = "DATA ERROR"
        bull = sorted(data.get("bull_put", []), key=lambda row: row["Rank"])
        bear = sorted(data.get("bear_call", []), key=lambda row: row["Rank"])
        warnings = list(data.get("warnings", []))
        if data and not data.get("generated_at"):
            warnings.insert(0, "Saved results have no scan timestamp/source metadata. Rerun using your new CSV.")
        if status == "EXPIRED SNAPSHOT":
            warnings.insert(0, "These contracts have expired. Results are historical only; select an unexpired CSV.")
        return {"data": data, "status": status, "error": error,
                "last_scan_error": application.config["LAST_SCAN_ERROR"],
                "market": data.get("market") or {}, "warnings": warnings,
                "bull_put": bull, "bear_call": bear, "strategies": bull + bear,
                "top_bull": bull[:2], "top_bear": bear[:2],
                "snapshots": manager.available_snapshots()}

    @application.route("/")
    @application.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html", active_page="dashboard", **read_result())

    @application.route("/api/dashboard")
    def api_dashboard():
        return jsonify(read_result())

    @application.route("/api/health")
    def health():
        return jsonify(status="ok", mode="practice", order_execution=False)

    @application.route("/run-analysis", methods=["POST"])
    def run_analysis():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(success=False, error="Send a JSON object containing expiry."), 400
        expiry = body.get("expiry")
        source = body.get("market_source", "csv")
        if not isinstance(expiry, str) or not expiry or source not in ("csv", "live", "config"):
            return jsonify(success=False, error="Select an uploaded expiry and a valid market source."), 400
        try:
            selected = date.fromisoformat(expiry)
            manager.find_option_chain(selected)
        except ValueError as error:
            return jsonify(success=False, error=str(error)), 400
        try:
            payload = runner(expiry, market_source=source, config_manager=manager)
            application.config["LAST_SCAN_ERROR"] = None
            return jsonify(success=True, message="Practice scan completed.",
                           expiry=payload["expiry_date"], journal_rows_added=payload["journal_rows_added"],
                           bull_put=len(payload["bull_put"]), bear_call=len(payload["bear_call"]))
        except AnalysisBusy as error:
            message, status_code = str(error), 409
        except MarketDataError as error:
            message, status_code = str(error), 502
        except PermissionError:
            message, status_code = "Close Config.xlsx, journal_tracker.xlsx and strategy reports in Excel, then retry. Existing journal entries were not overwritten.", 409
        except (ValueError, FileNotFoundError) as error:
            message, status_code = str(error), 400
        except Exception as error:
            log_event("scan_request_failed", error_type=type(error).__name__)
            message, status_code = "Analysis failed. Check Logs/application.log and the CSV format. Previous results are retained.", 500
        application.config["LAST_SCAN_ERROR"] = message
        return jsonify(success=False, error=message), status_code

    @application.route("/journal")
    def journal():
        headers, rows, error = [], [], None
        workbook_available = True
        path = manager.output_dir / "journal_tracker.xlsx"
        try:
            headers, rows = read_journal(path)
        except ValueError as problem:
            error = str(problem)
            workbook_available = False
        entry_ids = journal_entry_ids(headers, rows)
        try:
            saved = status_store.load()
            row_statuses = [saved.get(entry_id, "open") for entry_id in entry_ids]
        except JournalStatusError as problem:
            row_statuses = ["unknown"] * len(rows)
            error = str(problem)
        return render_template("journal.html", active_page="journal", headers=headers, rows=rows,
                               entry_ids=entry_ids, row_statuses=row_statuses, open_count=row_statuses.count("open"),
                               closed_count=row_statuses.count("closed"), unknown_count=row_statuses.count("unknown"),
                               kpis=journal_kpis(headers, rows, row_statuses, workbook_available), error=error)

    @application.route("/api/journal/status", methods=["POST"])
    def update_journal_status():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return jsonify(success=False, error="Send a journal entry ID and status as JSON."), 400
        entry_id, status = body.get("entry_id"), body.get("status")
        if not isinstance(entry_id, str) or not entry_id or len(entry_id) > 100 or status not in ("open", "closed"):
            return jsonify(success=False, error="Select a valid journal entry and open/closed status."), 400
        try:
            headers, rows = read_journal(manager.output_dir / "journal_tracker.xlsx")
            entry_ids = journal_entry_ids(headers, rows)
            if entry_id not in entry_ids:
                return jsonify(success=False, error="This journal entry has changed or no longer exists. Refresh Journal and retry."), 404
            saved = status_store.set_status(entry_id, status)
            current = [saved.get(identity, "open") for identity in entry_ids]
        except JournalStatusError as problem:
            return jsonify(success=False, error=str(problem)), 409
        except ValueError as problem:
            return jsonify(success=False, error=str(problem)), 400
        except OSError:
            return jsonify(success=False, error="Unable to save the trade selection. Check Output folder permissions and retry."), 409
        log_event("journal_status_updated", status=status, entry_id=entry_id)
        return jsonify(success=True, entry_id=entry_id, status=status,
                       counts={"open": current.count("open"), "closed": current.count("closed")},
                       kpis=journal_kpis(headers, rows, current))

    @application.route("/settings")
    def settings():
        values, error = {}, None
        try:
            config = manager.load_config()
            allowed = list(ConfigManager.NUMERIC_RULES) + ["Trend", "CPRWidth", "MinimumCredit", "MinimumROR"]
            values = {key: config[key] for key in allowed if key in config}
        except (ValueError, OSError) as problem:
            error = str(problem)
        return render_template("settings.html", active_page="settings", values=values,
                               config_path=str(manager.config_file), error=error)

    @application.route("/downloads/journal")
    def download_journal():
        path = manager.output_dir / "journal_tracker.xlsx"
        if not path.exists():
            return jsonify(error="Journal has not been created yet."), 404
        return send_file(path.resolve(), as_attachment=True)

    @application.route("/downloads/results")
    def download_results():
        data = read_result()["data"]
        try:
            expiry = date.fromisoformat(data["expiry_date"]).isoformat()
        except (KeyError, TypeError, ValueError):
            return jsonify(error="Run a scan to create a strategy report."), 404
        path = manager.output_dir / f"strategy_results_{expiry}.xlsx"
        if not path.exists():
            return jsonify(error="Strategy report was not found."), 404
        return send_file(path.resolve(), as_attachment=True)

    return application


app = create_app()

if __name__ == "__main__":
    serve(app, host="127.0.0.1", port=5000)
