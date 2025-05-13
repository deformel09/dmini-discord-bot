import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='d.', intents=intents)

async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event
async def on_ready():
    print(f'Бот {bot.user.name} успешно подключен к Discord!')
    print(f'ID бота: {bot.user.id}')

async def main():
    await load_cogs()
    await bot.start('')

if __name__ == '__main__':
    asyncio.run(main())