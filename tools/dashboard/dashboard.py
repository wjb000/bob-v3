#!/usr/bin/env python3
"""Simple local dashboard for Bob v3 agent control."""
import subprocess
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

REPO = os.path.expanduser("~/Desktop/bob-v3-repo")
os.chdir(REPO)

def run(cmd, timeout=30):
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout, cwd=REPO
        )
        return {"ok": result.returncode == 0, "out": result.stdout[-4000:], "err": result.stderr[-2000:]}
    except Exception as e:
        return {"ok": False, "out": "", "err": str(e)}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open("tools/dashboard/index.html", "rb") as f:
                self.wfile.write(f.read())
        elif path == "/status":
            self.json(self.get_status())
        elif path == "/improvements":
            try:
                with open("IMPROVEMENTS.md") as f:
                    self.json({"content": f.read()})
            except:
                self.json({"content": ""})
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode() if length else ""
        data = json.loads(body) if body else {}
        path = urlparse(self.path).path

        if path == "/start":
            self.json(run("nohup ./agent-loop.sh > agent-loop.log 2>&1 &"))
        elif path == "/stop":
            self.json(run("pkill -f 'agent-loop' || true; pkill -f 'aider' || true"))
        elif path == "/ollama-restart":
            self.json(run("brew services restart ollama"))
        elif path == "/rebuild":
            self.json(self.do_rebuild())
        elif path == "/start-loop":
            mode = data.get("mode", "docs")
            self.json(self.start_area_loop(mode))
        elif path == "/save-improvements":
            with open("IMPROVEMENTS.md", "w") as f:
                f.write(data.get("content", ""))
            self.json({"ok": True})
        else:
            self.json({"ok": False, "err": "unknown"})

    def get_status(self):
        log = run("git log -1 --oneline")
        ollama = run("curl -s http://127.0.0.1:11434/api/version || echo down")
        running = run("pgrep -f agent-loop >/dev/null && echo running || echo stopped")
        return {
            "commit": log["out"].strip(),
            "ollama": "up" if "version" in ollama["out"] else "down",
            "loop": running["out"].strip(),
            "log_tail": run("tail -25 agent-loop.log 2>/dev/null || echo no log")["out"]
        }

    def do_rebuild(self):
        steps = [
            "python cad/export.py",
            "python sim/build_mjcf.py",
            "python tools/make_docs.py",
            "git add -A && git commit -m 'Rebuild: CAD + docs' || true",
            "git push origin main || true"
        ]
        results = []
        for s in steps:
            results.append(run(s, timeout=180))
        return {"ok": all(r["ok"] for r in results), "steps": results}

    def start_area_loop(self, mode):
        # Kill any existing loop first
        run("pkill -f agent-loop || true")
        scripts = {
            "docs": self.make_docs_loop,
            "sim": self.make_sim_loop,
            "cad": self.make_cad_loop,
            "site": self.make_site_loop,
        }
        script = scripts.get(mode, self.make_docs_loop)()
        with open("agent-loop.sh", "w") as f:
            f.write(script)
        run("chmod +x agent-loop.sh")
        return run("nohup ./agent-loop.sh > agent-loop.log 2>&1 &")

    def make_docs_loop(self):
        return '''#!/bin/bash
cd ~/Desktop/bob-v3-repo
export OLLAMA_API_BASE=http://127.0.0.1:11434
while true; do
  echo "=== DOCS $(date) ==="
  git stash push -m "tmp" || true
  git pull --rebase || true
  git stash pop || true
  aider --model ollama_chat/qwen3-coder:30b --map-tokens 0 \\
    --file IMPROVEMENTS.md --file README.md --file ASSEMBLY.md --file VERIFY.md --file BOM.md --file PRINT.md \\
    --message "Work on the next unchecked DOCS item. Small reversible improvement only in the added files. Mark done only if clean." \\
    --yes --no-auto-commits
  git add -A && git commit -m "Agent(docs): next improvement" || true
  git push origin main || true
  sleep 30
done
'''

    def make_sim_loop(self):
        return '''#!/bin/bash
cd ~/Desktop/bob-v3-repo
export OLLAMA_API_BASE=http://127.0.0.1:11434
while true; do
  echo "=== SIM $(date) ==="
  git stash push -m "tmp" || true
  git pull --rebase || true
  git stash pop || true
  aider --model ollama_chat/qwen3-coder:30b --map-tokens 0 \\
    --file IMPROVEMENTS.md --file sim/check.py --file sim/expert.py --file VERIFY.md \\
    --message "Work on the next unchecked SIM item. Small reversible improvement only in the added files. Mark done only if clean." \\
    --yes --no-auto-commits
  git add -A && git commit -m "Agent(sim): next improvement" || true
  git push origin main || true
  sleep 30
done
'''

    def make_cad_loop(self):
        return '''#!/bin/bash
cd ~/Desktop/bob-v3-repo
export OLLAMA_API_BASE=http://127.0.0.1:11434
while true; do
  echo "=== CAD $(date) ==="
  git stash push -m "tmp" || true
  git pull --rebase || true
  git stash pop || true
  aider --model ollama_chat/qwen3-coder:30b --map-tokens 0 \\
    --file IMPROVEMENTS.md --file cad/params.py --file VERIFY.md \\
    --message "Work on the next unchecked CAD/params item. Small reversible change only in the added files. Mark done only if clean." \\
    --yes --no-auto-commits
  git add -A && git commit -m "Agent(cad): next improvement" || true
  git push origin main || true
  sleep 30
done
'''

    def make_site_loop(self):
        return '''#!/bin/bash
cd ~/Desktop/bob-v3-repo
export OLLAMA_API_BASE=http://127.0.0.1:11434
while true; do
  echo "=== SITE $(date) ==="
  git stash push -m "tmp" || true
  git pull --rebase || true
  git stash pop || true
  aider --model ollama_chat/qwen3-coder:30b --map-tokens 0 \\
    --file IMPROVEMENTS.md --file README.md --file ASSEMBLY.md --file BOM.md --file PRINT.md --file VERIFY.md \\
    --message "Work on the next unchecked SITE/presentation item. Small reversible improvement only in the added files. Mark done only if clean." \\
    --yes --no-auto-commits
  git add -A && git commit -m "Agent(site): next improvement" || true
  git push origin main || true
  sleep 30
done
'''

    def json(self, obj):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    print("Dashboard: http://127.0.0.1:8765")
    HTTPServer(("127.0.0.1", 8765), Handler).serve_forever()