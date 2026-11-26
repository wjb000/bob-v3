#!/bin/bash
cd ~/Desktop/bob-v3-repo
export OLLAMA_API_BASE=http://127.0.0.1:11434

while true; do
  echo "=== $(date) ==="
  git pull --rebase || true

  aider --model ollama_chat/qwen3-coder:30b \
        --file IMPROVEMENTS.md \
        --message "Work on the next unchecked item in IMPROVEMENTS.md. Make one small, reversible improvement. Update any relevant docs or site-facing text. Mark the item done only if the change is clean. Do not rewrite large sections or break existing files." \
        --yes

  git add -A
  git commit -m "Agent: next improvement from IMPROVEMENTS.md" || true
  git push origin main || true

  echo "Sleeping 10 minutes..."
  sleep 600
done
