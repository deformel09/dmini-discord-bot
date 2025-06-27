# Discord Bot

Bot d-mini discord

## Установка и настройка

### Требования
- Node.js >= 16.0.0
- Yarn >= 1.22.0
- Python 3.x
- pip

### Быстрая настройка

```bash
# Клонирование проекта
git clone <repository-url>
cd discordbot

# Установка зависимостей и настройка окружения
yarn setup
```

### Команды Yarn

```bash
# Установка зависимостей Python
yarn install-deps

# Настройка окружения (.env файл)
yarn env

# Запуск бота в production режиме
yarn start

# Остановка бота
yarn stop

# Перезапуск бота
yarn restart

# Запуск в режиме разработки
yarn dev

# Просмотр логов
yarn logs

# Очистка временных файлов
yarn clean
```

### Ручная настройка

1. **Создание виртуального окружения Python:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Установка зависимостей:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Настройка переменных окружения:**
   ```bash
   cp .env.example .env
   # Отредактируйте .env файл
   ```

## Структура проекта

```
discordbot/
├── cogs/
├── sh/                 # Shell скрипты для управления
│   ├── run.sh         # Запуск бота
│   ├── stop.sh        # Остановка бота
│   └── restart.sh     # Перезапуск бота
├── logs/              # Логи бота
├── package.json       # Конфигурация yarn
├── requirements.txt   # Python зависимости
└── main.py           # Основной файл бота
```

## Разработка

Для разработки используйте:
```bash
yarn dev  # Запуск в режиме разработки
```

## Логи

Логи сохраняются в `logs/bot.log`. Для просмотра в реальном времени:
```bash
yarn logs
``` 