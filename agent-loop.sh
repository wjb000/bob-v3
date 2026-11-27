#!/bin/bash
cd ~/Desktop/bob-v3-repo
export OLLAMA_API_BASE=http://127.0.0.1:11434
while true; do
  echo "=== SITE $(date) ==="
  git stash push -m "tmp" || true
  git pull --rebase || true
  git stash pop || true
  aider --model ollama_chat/qwen3-coder:30b --map-tokens 0 \
    --file IMPROVEMENTS.md --file README.md --file ASSEMBLY.md --file BOM.md --file PRINT.md --file VERIFY.md \
    --message "Work on the next unchecked SITE/presentation item. Small reversible improvement only in the added files. Mark done only if clean." \
    --yes --no-auto-commits
  git add -A && git commit -m "Agent(site): next improvement" || true
  git push origin main || true
  sleep 30
done
