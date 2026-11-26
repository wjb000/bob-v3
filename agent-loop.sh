#!/bin/bash
cd ~/Desktop/bob-v3-repo
export OLLAMA_API_BASE=http://127.0.0.1:11434

while true; do
  echo "=== $(date) ==="
  git stash push -m "agent-temp" || true
  git pull --rebase || true
  git stash pop || true

  aider --model ollama_chat/qwen3-coder:30b \
        --map-tokens 0 \
        --file IMPROVEMENTS.md \
        --file README.md \
        --file ASSEMBLY.md \
        --file VERIFY.md \
        --file BOM.md \
        --file PRINT.md \
        --message "Work on the next unchecked item in IMPROVEMENTS.md. Make one small reversible improvement ONLY in the files already added. Do not open any other files. Mark the item done only if the change is clean." \
        --yes \
        --no-auto-commits

  git add -A
  git commit -m "Agent: next improvement from IMPROVEMENTS.md" || true
  git push origin main || true

  echo "Sleeping 30 seconds..."
  sleep 30
done
