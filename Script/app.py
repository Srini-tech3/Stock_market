from flask import Flask, render_template, request, jsonify
import os
import json
from collections import Counter
import subprocess
import sys

app = Flask(__name__)

@app.route("/")
@app.route("/dashboard")
def dashboard():

    strategies=[]

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    json_path = os.path.abspath(
        os.path.join(BASE_DIR, "..", "Output", "result.json")
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
    script_path = os.path.join(
        os.path.dirname(__file__),
        "main.py"
    )
    try:
        result = subprocess.run(
            [
                sys.executable,
                script_path,
                "--expiry",
                expiry
            ],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            return jsonify({
                "success": False,
                "error": result.stderr
            }), 500
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

if __name__=="__main__":
    app.run(debug=True)