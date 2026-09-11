#!/bin/bash
# Double-click this file in Finder to start the voice PubMed bot.
#
# First run only: macOS will pop up a "Terminal wants to use the microphone"
# prompt — someone sighted needs to click "Allow" once. After that Andrew can
# launch it himself by double-clicking this file; the permission sticks to
# Terminal.app until it is revoked in System Settings > Privacy & Security.
#
# Put the Muse API key in a file named ".env" next to this one:
#     MODEL_API_KEY=your-key-here
# Without it the bot still runs, on the basic (Google) recognizer.

cd "$(dirname "$0")" || exit 1

if [ -f .env ]; then
    set -a
    # shellcheck disable=SC1091
    . ./.env
    set +a
fi

exec python3 voice_pubmed_bot.py "$@"
