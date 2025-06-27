import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

if not TOKEN:
    print("❌ Токен бота не найден!")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix='d.',
    intents=intents,
    help_command=None
)

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user.name} подключился!')
    print(f'ID: {bot.user.id}')

async def load_cogs():
    if os.path.exists('./cogs'):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('__'):
                try:
                    await bot.load_extension(f'cogs.{filename[:-3]}')
                    print(f'✅ {filename[:-3]} загружен')
                except Exception as e:
                    print(f'❌ Ошибка {filename[:-3]}: {e}')

@bot.event
async def setup_hook():
    """Вызывается при инициализации бота"""
    await load_cogs()

if __name__ == '__main__':
    try:
        # Используем bot.run() вместо asyncio.run()
        bot.run(TOKEN, reconnect=True)
    except KeyboardInterrupt:
        print("🛑 Остановлено пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")