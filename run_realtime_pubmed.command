#!/bin/bash
cd "$(dirname "$0")" || exit 1
exec ./run_voice_pubmed_bot.command --realtime "$@"
