import discord
from discord.ext import commands

class Basic(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help", aliases=["команды", "commands"])
    async def help_command(self, ctx, command_name=None):
        """Показывает список доступных команд или информацию о конкретной команде"""
        if command_name:
            command = self.bot.get_command(command_name)
            if command:
                embed = discord.Embed(
                    title=f"Команда: {self.bot.command_prefix}{command.name}",
                    description=command.help or "Описание отсутствует",
                    color=discord.Color.blue()
                )
                if command.aliases:
                    embed.add_field(
                        name="Алиасы",
                        value=", ".join([f"`{self.bot.command_prefix}{alias}`" for alias in command.aliases]),
                        inline=False
                    )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Команда `{command_name}` не найдена.")
            return

        embed = discord.Embed(
            title="Список доступных команд",
            description=f"Используйте `{self.bot.command_prefix}помощь <команда>` для получения подробной информации.",
            color=discord.Color.blue()
        )

        for cog_name, cog in self.bot.cogs.items():
            commands_list = [f"`{self.bot.command_prefix}{cmd.name}`" for cmd in cog.get_commands() if not cmd.hidden]
            if commands_list:
                embed.add_field(name=cog_name, value=", ".join(commands_list), inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def hi(self, ctx):
        """Команда !привет - бот отвечает приветствием"""
        await ctx.send(f'Привет, {ctx.author.mention}!')

    @commands.command()
    async def info(self, ctx):
        """Команда !инфо - выводит информацию о сервере"""
        server = ctx.guild
        verification_level = str(server.verification_level).capitalize()
        boost_level = f"Уровень {server.premium_tier}" if server.premium_tier > 0 else "Нет"
        boosts = server.premium_subscription_count

        await ctx.send(f'Информация о сервере **{server.name}**:\n'
                       f'Участников: {server.member_count}\n'
                       f'Уровень проверки: {verification_level}\n'
                       f'Уровень буста: {boost_level} ({boosts} бустов)\n'
                       f'Создан: {server.created_at.strftime("%d.%m.%Y")}\n'
                       'Владелец: @deformel')

async def setup(bot):
    await bot.add_cog(Basic(bot))