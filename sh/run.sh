#!/bin/bash

# Переход в корень проекта
cd "$(dirname "$0")/.."

# Создаем папку logs если её нет
mkdir -p logs

# Проверка существующего процесса
if [ -f logs/bot.pid ]; then
    if kill -0 $(cat logs/bot.pid) >/dev/null 2>&1; then
        echo "Error: Bot is already running (PID: $(cat logs/bot.pid))"
        exit 1
    else
        rm logs/bot.pid
    fi
fi

# Запуск бота
source venv/bin/activate
nohup python main.py > logs/bot.log 2>&1 &
echo $! > logs/bot.pid

echo "Bot started (PID: $(cat logs/bot.pid))"
echo "Logs: logs/bot.log"