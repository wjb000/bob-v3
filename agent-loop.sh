#!/bin/bash
cd ~/Desktop/bob-v3-repo
export OLLAMA_API_BASE=http://127.0.0.1:11434

cycle=0

while true; do
  echo "=== $(date) ==="
  git stash push -m "agent-temp" || true
  git pull --rebase || true
  git stash pop || true

  mode=$((cycle % 4))

  if [ $mode -eq 0 ]; then
    echo "--- DOCS cycle ---"
    aider --model ollama_chat/qwen3-coder:30b \
          --map-tokens 0 \
          --file IMPROVEMENTS.md --file README.md --file ASSEMBLY.md --file VERIFY.md --file BOM.md --file PRINT.md \
          --message "Work on the next unchecked DOCS item in IMPROVEMENTS.md. Small reversible improvement only in the files already added. Mark done only if clean." \
          --yes --no-auto-commits
    commit_msg="Agent(docs): next improvement"

  elif [ $mode -eq 1 ]; then
    echo "--- SIM cycle ---"
    aider --model ollama_chat/qwen3-coder:30b \
          --map-tokens 0 \
          --file IMPROVEMENTS.md --file sim/check.py --file sim/expert.py --file VERIFY.md \
          --message "Work on the next unchecked SIM item in IMPROVEMENTS.md. Small reversible improvement only in the files already added. Mark done only if clean." \
          --yes --no-auto-commits
    commit_msg="Agent(sim): next improvement"

  elif [ $mode -eq 2 ]; then
    echo "--- CAD cycle ---"
    aider --model ollama_chat/qwen3-coder:30b \
          --map-tokens 0 \
          --file IMPROVEMENTS.md --file cad/params.py --file VERIFY.md \
          --message "Work on the next unchecked CAD/params item in IMPROVEMENTS.md. Small reversible change only in the files already added. Mark done only if clean." \
          --yes --no-auto-commits
    commit_msg="Agent(cad): next improvement"

  else
    echo "--- SITE/UI cycle ---"
    aider --model ollama_chat/qwen3-coder:30b \
          --map-tokens 0 \
          --file IMPROVEMENTS.md --file README.md --file ASSEMBLY.md --file BOM.md --file PRINT.md --file VERIFY.md \
          --message "Work on the next unchecked SITE or presentation item in IMPROVEMENTS.md. Improve clarity, status banners, or polish of the docs that feed the live site. Small reversible change only. Mark done only if clean." \
          --yes --no-auto-commits
    commit_msg="Agent(site): next improvement"
  fi

  git add -A
  git commit -m "$commit_msg" || true
  git push origin main || true

  cycle=$((cycle + 1))
  echo "Sleeping 30 seconds..."
  sleep 30
done
