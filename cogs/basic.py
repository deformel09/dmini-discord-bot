import discord
from discord.ext import commands
from discord import app_commands

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Гибридная команда (и слеш, и префикс)
    @commands.hybrid_command(name="hi", description="Бот отвечает приветствием")
    async def hi(self, ctx):
        await ctx.send(f'Привет, {ctx.author.mention}!')

    # Гибридная команда с описанием
    @commands.hybrid_command(name="info", description="Информация о сервере")
    async def info(self, ctx):
        server = ctx.guild
        verification_level = str(server.verification_level).capitalize()
        boost_level = f"Уровень {server.premium_tier}" if server.premium_tier > 0 else "Нет"
        boosts = server.premium_subscription_count

        await ctx.send(
            f'Информация о сервере **{server.name}**:\n'
            f'Участников: {server.member_count}\n'
            f'Уровень проверки: {verification_level}\n'
            f'Уровень буста: {boost_level} ({boosts} бустов)\n'
            f'Создан: {server.created_at.strftime("%d.%m.%Y")}\n'
            'Владелец: @deformel'
        )

async def setup(bot):
    await bot.add_cog(Basic(bot))