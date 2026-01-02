from flask import Flask, request, jsonify
import subprocess, json

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
	return jsonify({"ok": True})

@app.route("/mcp", methods=["POST"])
def mcp():
	payload = request.get_json(force=True, silent=True) or {}
	cmd = ["uv", "--directory", ".", "run", "zendesk"]
	proc = subprocess.Popen(
		cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
	)
	out, err = proc.communicate(json.dumps(payload))
	return jsonify({"stdout": out, "stderr": err})

if __name__ == "__main__":
	app.run(host="127.0.0.1", port=5001)
