from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, render_template, request

from logic.estimate import calculate_estimate

load_dotenv(".env")

ALLOWED_COMPLEXITY = {"low", "medium", "high"}

app = Flask(__name__)


@app.get("/")
def index():
    return jsonify(
        {
            "message": "Estimation Agent Core API",
            "endpoints": ["/health", "/estimate"],
        }
    ), 200


def render_html(project_name, summary, scope, result):
    return render_template(
        "estimate.html",
        project_name=project_name,
        summary=summary,
        scope=scope,
        result=result,
    )


@app.get("/health")
def health():
    resp = jsonify({"status": "ok"})
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp, 200


def cors_preflight():
    resp = make_response("", 204)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.route("/estimate", methods=["POST", "OPTIONS"])
def estimate():
    if request.method == "OPTIONS":
        return cors_preflight()

    data = request.get_json(silent=True) or {}

    try:
        screen_count = int(data.get("screen_count", 0))
    except Exception:
        return (
            jsonify(
                {
                    "status": "error",
                    "estimated_amount": 0,
                    "currency": "JPY",
                    "message": "screen_count must be an integer",
                }
            ),
            400,
        )
    if screen_count <= 0:
        return (
            jsonify(
                {
                    "status": "error",
                    "estimated_amount": 0,
                    "currency": "JPY",
                    "message": "screen_count must be > 0",
                }
            ),
            400,
        )

    complexity = (data.get("complexity") or "medium").strip()
    if complexity not in ALLOWED_COMPLEXITY:
        return (
            jsonify(
                {
                    "status": "error",
                    "estimated_amount": 0,
                    "currency": "JPY",
                    "message": f"complexity must be one of {sorted(ALLOWED_COMPLEXITY)}",
                }
            ),
            400,
        )

    # 見積金額を算出
    result = calculate_estimate(screen_count, complexity)
    estimated_amount = result["estimated_amount"]
    breakdown = result["breakdown"]
    config_version = result["config_version"]
    warnings = result["warnings"]
    assumptions = result["assumptions"]

    resp = jsonify(
        {
            "status": "ok",
            "estimated_amount": estimated_amount,
            "currency": "JPY",
            "message": None,
            "breakdown": breakdown,
            "config_version": config_version,
            "warnings": warnings,
            "assumptions": assumptions,
        }
    )
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp, 200


if __name__ == "__main__":
    app.run(port=8001, debug=True)
