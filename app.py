import os
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import requests

load_dotenv()

CALC_API_BASE = os.getenv("CALC_API_BASE", "http://localhost:7071")
CALC_API_URL = f"{CALC_API_BASE.rstrip('/')}/api/calculate_estimate"

app = Flask(__name__)

def render_html(project_name, summary, scope, result):
    return f"""
<!doctype html>
<html lang="ja">
<head><meta charset="utf-8"><title>見積結果</title></head>
<body>
<h1>見積結果</h1>
<p><b>{project_name}</b></p>
<p>{summary}</p>
<p>{scope}</p>
<hr>
<ul>
  <li>画面数: {result.get('screen_count')}</li>
  <li>難易度: {result.get('complexity')}</li>
  <li>人日: {result.get('estimate_days')}</li>
  <li>概算費用: ¥{result.get('estimate_cost'):,}</li>
</ul>

</body>
</html>
"""

@app.post("/estimate")
def estimate():
    data = request.get_json() or {}
    r = requests.post(CALC_API_URL, json={
        "screen_count": data.get("screen_count", 0),
        "complexity": data.get("complexity", "medium")
    })
    html = render_html(
        data.get("project_name",""),
        data.get("summary",""),
        data.get("scope",""),
        r.json()
    )
    return html, 200, {"Content-Type": "text/html"}

if __name__ == "__main__":
    app.run(port=8001, debug=True)
