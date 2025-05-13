#!/bin/bash

cd "$(dirname "$0")/.."

if [ ! -f logs/bot.pid ]; then
    echo "Error: logs/bot.pid not found (is bot running?)"
    exit 1
fi

PID=$(cat logs/bot.pid)

if kill -0 $PID >/dev/null 2>&1; then
    kill $PID
    echo "Bot stopped (PID: $PID)"
else
    echo "Error: Process $PID not found"
fi

rm -f logs/bot.pid