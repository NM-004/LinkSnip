from flask import Flask, request, redirect, jsonify, render_template_string
import redis
import string
import random
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

CHARS = string.ascii_letters + string.digits

def generate_code(length=6):
    return "".join(random.choices(CHARS, k=length))

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LinkSnip — Shorten Smarter</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0a0f;
    --surface: #13131a;
    --border: #2a2a3a;
    --accent: #00ff87;
    --accent2: #7c3aed;
    --text: #e8e8f0;
    --muted: #6b6b80;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Syne', sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    background-image: radial-gradient(ellipse at 20% 50%, rgba(124,58,237,0.08) 0%, transparent 60%),
                      radial-gradient(ellipse at 80% 20%, rgba(0,255,135,0.05) 0%, transparent 50%);
  }
  .logo {
    font-size: 3rem;
    font-weight: 800;
    letter-spacing: -2px;
    margin-bottom: 0.25rem;
  }
  .logo span { color: var(--accent); }
  .tagline { color: var(--muted); font-family: 'Space Mono', monospace; font-size: 0.8rem; margin-bottom: 3rem; }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2.5rem;
    width: 100%;
    max-width: 560px;
  }
  label { display: block; font-size: 0.75rem; font-weight: 700; letter-spacing: 2px; color: var(--muted); margin-bottom: 0.5rem; text-transform: uppercase; }
  input[type=url] {
    width: 100%;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    color: var(--text);
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    padding: 0.85rem 1rem;
    outline: none;
    transition: border-color 0.2s;
    margin-bottom: 1rem;
  }
  input[type=url]:focus { border-color: var(--accent); }
  button {
    width: 100%;
    background: var(--accent);
    color: #000;
    border: none;
    border-radius: 8px;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    padding: 0.9rem;
    cursor: pointer;
    transition: opacity 0.2s, transform 0.1s;
  }
  button:hover { opacity: 0.9; }
  button:active { transform: scale(0.99); }
  .result {
    display: none;
    margin-top: 1.5rem;
    background: var(--bg);
    border: 1px solid var(--accent);
    border-radius: 8px;
    padding: 1rem;
    font-family: 'Space Mono', monospace;
    font-size: 0.9rem;
    word-break: break-all;
    color: var(--accent);
    cursor: pointer;
    position: relative;
  }
  .result .copy-hint { font-size: 0.65rem; color: var(--muted); margin-top: 0.35rem; }
  .error { color: #ff4f4f; font-size: 0.8rem; margin-top: 0.5rem; display: none; }
  .stats { margin-top: 1.5rem; display: flex; gap: 1rem; }
  .stat { flex: 1; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 1rem; text-align: center; }
  .stat-num { font-size: 1.5rem; font-weight: 800; color: var(--accent2); }
  .stat-label { font-size: 0.7rem; color: var(--muted); font-family: 'Space Mono', monospace; text-transform: uppercase; letter-spacing: 1px; }
  footer { margin-top: 2rem; color: var(--muted); font-size: 0.75rem; font-family: 'Space Mono', monospace; }
</style>
</head>
<body>
<div class="logo">Link<span>Snip</span></div>
<p class="tagline">// url shortener · built with devops</p>
<div class="card">
  <label for="url">Paste your long URL</label>
  <input type="url" id="url" placeholder="https://example.com/very/long/path..." />
  <button onclick="shorten()">Snip it →</button>
  <p class="error" id="err">Please enter a valid URL.</p>
  <div class="result" id="result">
    <div id="short-url"></div>
    <div class="copy-hint">Click to copy</div>
  </div>
  <div class="stats" id="stats" style="display:none">
    <div class="stat"><div class="stat-num" id="total-links">—</div><div class="stat-label">Total Links</div></div>
    <div class="stat"><div class="stat-num" id="total-clicks">—</div><div class="stat-label">Total Clicks</div></div>
  </div>
</div>
<footer>v1.0.0 · Docker · Kubernetes · CI/CD</footer>
<script>
async function shorten() {
  const url = document.getElementById('url').value.trim();
  const err = document.getElementById('err');
  const result = document.getElementById('result');
  err.style.display = 'none'; result.style.display = 'none';
  if (!url || !/^https?:\\/\\//.test(url)) { err.style.display = 'block'; return; }
  const res = await fetch('/api/shorten', { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({url}) });
  const data = await res.json();
  if (data.code) {
    const finalUrl = window.location.origin + '/' + data.code;
    document.getElementById('short-url').textContent = finalUrl;
    result.style.display = 'block';
    result.onclick = () => { navigator.clipboard.writeText(finalUrl); result.style.borderColor = '#7c3aed'; setTimeout(()=>result.style.borderColor='var(--accent)',1000); };
    loadStats();
  }
}
async function loadStats() {
  const res = await fetch('/api/stats');
  const data = await res.json();
  document.getElementById('total-links').textContent = data.total_links;
  document.getElementById('total-clicks').textContent = data.total_clicks;
  document.getElementById('stats').style.display = 'flex';
}
loadStats();
document.getElementById('url').addEventListener('keydown', e => { if (e.key === 'Enter') shorten(); });
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/shorten", methods=["POST"])
def shorten():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "Missing URL"}), 400
    url = data["url"].strip()
    if not url.startswith(("http://", "https://")):
        return jsonify({"error": "Invalid URL"}), 400
    code = generate_code()
    while r.exists(f"url:{code}"):
        code = generate_code()
    r.set(f"url:{code}", url)
    r.set(f"clicks:{code}", 0)
    r.incr("stats:total_links")
    logger.info(f"Shortened {url} → {code}")
    base = BASE_URL if BASE_URL and "example.com" not in BASE_URL else request.host_url.rstrip("/")
    return jsonify({"short_url": f"{base}/{code}", "code": code})

@app.route("/<code>")
def redirect_url(code):
    url = r.get(f"url:{code}")
    if not url:
        return jsonify({"error": "Not found"}), 404
    r.incr(f"clicks:{code}")
    r.incr("stats:total_clicks")
    return redirect(url)

@app.route("/api/stats")
def stats():
    total_links = int(r.get("stats:total_links") or 0)
    total_clicks = int(r.get("stats:total_clicks") or 0)
    return jsonify({"total_links": total_links, "total_clicks": total_clicks})

@app.route("/health")
def health():
    try:
        r.ping()
        return jsonify({"status": "healthy", "redis": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
