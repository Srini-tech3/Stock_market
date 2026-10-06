from flask import Flask, render_template, request, jsonify
import os
import json
from collections import Counter
import subprocess
import sys
from waitress import serve
from main import run_analysis as execute_analysis

# -------------------------------------------------------
# Paths
# -------------------------------------------------------

# Templates and Static (inside EXE when packaged)
if getattr(sys, "frozen", False):
    RESOURCE_DIR = sys._MEIPASS
else:
    RESOURCE_DIR = os.path.dirname(os.path.abspath(__file__))

# Project Root (for Output, Logs, Input, etc.)
if getattr(sys, "frozen", False):
    PROJECT_ROOT = os.path.dirname(sys.executable)
else:
    PROJECT_ROOT = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )

TEMPLATE_DIR = os.path.join(RESOURCE_DIR, "templates")
STATIC_DIR = os.path.join(RESOURCE_DIR, "static")

app = Flask(
    __name__,
    template_folder=TEMPLATE_DIR,
    static_folder=STATIC_DIR
)

# -------------------------------------------------------
# Debug (Remove after testing)
# -------------------------------------------------------

print("=" * 80)
print("Frozen          :", getattr(sys, "frozen", False))
print("Executable      :", sys.executable)
print("RESOURCE_DIR    :", RESOURCE_DIR)
print("PROJECT_ROOT    :", PROJECT_ROOT)
print("TEMPLATE_DIR    :", TEMPLATE_DIR)
print("STATIC_DIR      :", STATIC_DIR)
print("dashboard.html  :", os.path.exists(os.path.join(TEMPLATE_DIR, "dashboard.html")))
print("style.css       :", os.path.exists(os.path.join(STATIC_DIR, "css", "style.css")))
print("result.json     :", os.path.exists(os.path.join(PROJECT_ROOT, "Output", "result.json")))
print("=" * 80)

@app.route("/")
@app.route("/dashboard")
def dashboard():
    expiry_date = ""
    strategies=[]
    summary = {
        "total_strategies": 0,
        "top_strategy": None,
        "highest_pop": 0,
        "best_ror": 0
    }
    
    json_path = os.path.join(
        PROJECT_ROOT,
        "Output",
        "result.json"
    )

    data = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}

        expiry_date = data.get("expiry_date", "")

        strategies = []

        strategies.extend(data.get("bull_put", []))
        strategies.extend(data.get("bear_call", []))
        strategies.sort(key=lambda x: x["Rank"])

        summary = {}
        if strategies:
            summary["total_strategies"] = len(strategies)
            strategy_counter = Counter(
                row["Strategy"] for row in strategies
            )
            summary["top_strategy"] = strategy_counter.most_common(1)[0][0]
            summary["highest_pop"] = max(
                row["EstimatedPOP"] for row in strategies
            )
            summary["best_ror"] = max(
                row["ReturnOnRisk"] for row in strategies
            )
        else:
            summary = {
                "total_strategies": 0,
                "top_strategy": None,
                "highest_pop": 0,
                "best_ror": 0
            }

    return render_template(
        "dashboard.html",
        active_page="dashboard",
        expiry_date=expiry_date,
        strategies=strategies,
        summary=summary
    )

@app.route("/run-analysis", methods=["POST"])
def run_analysis():
    expiry = request.json.get("expiry")

    try:
        execute_analysis(expiry)

        return jsonify({
            "success": True,
            "message": "Analysis completed."
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/journal")
def journal():
    return render_template("journal.html",active_page="journal")

@app.route("/settings")
def settings():
    return render_template("settings.html",active_page="settings")

if __name__ == "__main__":
    serve(
        app,
        host="127.0.0.1",
        port=5000
    )