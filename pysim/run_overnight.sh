#!/bin/zsh
# Launch the held-out LLM evaluation so it survives closing the terminal and
# the Mac does not sleep while it runs. Keep the Mac plugged in, lid open.
#
#   ./run_overnight.sh            start (or resume)
#   tail -f results/llm_sweep.log follow progress
#   pkill -f llm_sweep.py         stop (relaunch later to resume)

set -e
cd "$(dirname "$0")"
OLLAMA=/opt/homebrew/opt/ollama/bin/ollama

# Ollama is only needed for the local model.
if [[ "$*" != *agent-sdk* ]] && ! curl -s --max-time 3 http://localhost:11434/api/version >/dev/null; then
  echo "Starting Ollama server..."
  OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 nohup "$OLLAMA" serve > results/ollama.log 2>&1 &
  until curl -s --max-time 2 http://localhost:11434/api/version >/dev/null; do sleep 1; done
fi

if pgrep -f "llm_sweep.py" >/dev/null; then
  echo "llm_sweep.py is already running."
  exit 1
fi

# -i: no idle sleep, -m: no disk sleep, -s: no system sleep (on AC power)
# Extra arguments are passed to llm_sweep.py, e.g.:
#   ./run_overnight.sh --backend agent-sdk --model claude-fable-5-1 --planners hybrid llm_c2
nohup caffeinate -i -m -s .venv/bin/python llm_sweep.py "$@" >> results/llm_sweep.log 2>&1 &
echo "Started (pid $!). Follow with: tail -f results/llm_sweep.log"
