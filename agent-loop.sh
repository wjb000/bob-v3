#!/bin/bash
cd ~/Desktop/bob-v3-repo
export OLLAMA_API_BASE=http://127.0.0.1:11434

while true; do
  echo "=== $(date) ==="
  git stash push -m "agent-temp" || true
  git pull --rebase || true
  git stash pop || true

  aider --model ollama_chat/qwen3-coder:30b \
        --file IMPROVEMENTS.md \
        --file README.md \
        --file ASSEMBLY.md \
        --file VERIFY.md \
        --message "Work on the next unchecked item in IMPROVEMENTS.md. Make one small, reversible improvement. Prefer docs, site text, VERIFY.md, or small comments. Mark the item done only if the change is clean. Do not load large CAD/STEP files." \
        --yes \
        --no-auto-commits

  git add -A
  git commit -m "Agent: next improvement from IMPROVEMENTS.md" || true
  git push origin main || true

  echo "Sleeping 10 minutes..."
  sleep 600
done
