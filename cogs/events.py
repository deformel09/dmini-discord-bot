import discord
from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            command_name = ctx.message.content.split()[0][len(self.bot.command_prefix):]
            await ctx.send(f"❌ Команда `{command_name}` не найдена. Используйте `{self.bot.command_prefix}help` для просмотра списка команд.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Отсутствует обязательный аргумент: {error.param.name}. Используйте `{self.bot.command_prefix}помощь {ctx.command}` для получения информации.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Неверный аргумент. Используйте `{self.bot.command_prefix}помощь {ctx.command}` для получения информации.")
        else:
            print(f"Произошла ошибка: {error}")

async def setup(bot):
    await bot.add_cog(Events(bot))