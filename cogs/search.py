import discord
from discord.ext import commands
import youtube_dl

# Настройки для YouTube-DL (используем те же, что в music.py)
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}


class SearchModal(discord.ui.Modal):
    def __init__(self, search_cog):
        super().__init__(title="🔍 Поиск треков на YouTube")
        self.search_cog = search_cog

    search_input = discord.ui.TextInput(
        label="Название трека",
        placeholder="Введите название песни или исполнителя",
        min_length=1,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()

        query = self.search_input.value

        try:
            # Выполняем поиск
            search_options = ytdl_format_options.copy()
            search_options['extract_flat'] = True
            search_options['default_search'] = 'ytsearch10:'

            ytdl = youtube_dl.YoutubeDL(search_options)
            search_results = await interaction.client.loop.run_in_executor(
                None, lambda: ytdl.extract_info(query, download=False)
            )

            if not search_results or 'entries' not in search_results:
                await interaction.followup.send("❌ Ничего не найдено!")
                return

            results = search_results['entries'][:10]  # Ограничиваем 10 результатами

            # Создаем embed и view для навигации
            embed = self.create_search_embed(query, results, 0)
            view = SearchNavigationView(results, query, self.search_cog, interaction)

            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            await interaction.followup.send(f"❌ Ошибка при поиске: {str(e)}")

    def create_search_embed(self, query, results, selected_index):
        embed = discord.Embed(
            title=f"🔍 Результаты поиска: {query}",
            description=f"Найдено {len(results)} треков. Используйте кнопки для навигации.",
            color=discord.Color.blue()
        )

        # Показываем список с выделенным треком
        description_lines = []
        for i, result in enumerate(results):
            title = result.get('title', 'Неизвестно')
            duration = result.get('duration', 0)

            # Форматируем длительность
            if duration:
                minutes, seconds = divmod(duration, 60)
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "Неизвестно"

            # Выделяем выбранный трек жирным
            if i == selected_index:
                line = f"**{i + 1}. {title}** ⏱️ {duration_str} ◀️"
            else:
                line = f"{i + 1}. {title} ⏱️ {duration_str}"

            description_lines.append(line)

        embed.description = f"Найдено {len(results)} треков:\n\n" + "\n".join(description_lines)
        embed.set_footer(text=f"Выбран трек {selected_index + 1} из {len(results)}")

        return embed


class SearchNavigationView(discord.ui.View):
    def __init__(self, results, query, search_cog, interaction):
        super().__init__(timeout=300)  # 5 минут
        self.results = results
        self.query = query
        self.search_cog = search_cog
        self.interaction = interaction
        self.selected_index = 0

        # Если только один результат, отключаем кнопки навигации
        if len(results) <= 1:
            self.up_button.disabled = True
            self.down_button.disabled = True

    @discord.ui.button(label='⬆️', style=discord.ButtonStyle.secondary)
    async def up_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.selected_index > 0:
            self.selected_index -= 1
            await self.update_embed(interaction)
        else:
            await interaction.response.send_message("⬆️ Вы уже в начале списка!", ephemeral=True)

    @discord.ui.button(label='⬇️', style=discord.ButtonStyle.secondary)
    async def down_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.selected_index < len(self.results) - 1:
            self.selected_index += 1
            await self.update_embed(interaction)
        else:
            await interaction.response.send_message("⬇️ Вы уже в конце списка!", ephemeral=True)

    @discord.ui.button(label='▶️ Воспроизвести', style=discord.ButtonStyle.success)
    async def play_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        selected_track = self.results[self.selected_index]
        url = selected_track.get('url', '')
        title = selected_track.get('title', 'Неизвестно')

        # Получаем music cog для воспроизведения
        music_cog = interaction.client.get_cog('Music')
        if music_cog:
            try:
                # Создаем контекст для команды play
                ctx = await interaction.client.get_context(interaction.message)
                ctx.author = interaction.user
                ctx.guild = interaction.guild
                ctx.channel = interaction.channel

                # Воспроизводим трек
                await music_cog.play(ctx, url=url)
                await interaction.response.send_message(f"▶️ Воспроизводится: **{title}**", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ Ошибка воспроизведения: {str(e)}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Музыкальный модуль не найден!", ephemeral=True)

    @discord.ui.button(label='➕ В очередь', style=discord.ButtonStyle.primary)
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        selected_track = self.results[self.selected_index]
        url = selected_track.get('url', '')
        title = selected_track.get('title', 'Неизвестно')

        # Получаем music cog для добавления в очередь
        music_cog = interaction.client.get_cog('Music')
        if music_cog:
            try:
                # Добавляем в очередь
                guild_id = interaction.guild.id
                if guild_id not in music_cog.queues:
                    music_cog.queues[guild_id] = []
                music_cog.queues[guild_id].append(url)

                await interaction.response.send_message(f"➕ Добавлено в очередь: **{title}**", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ Ошибка добавления в очередь: {str(e)}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Музыкальный модуль не найден!", ephemeral=True)

    @discord.ui.button(label='❌ Закрыть', style=discord.ButtonStyle.danger)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="🔍 Поиск закрыт", embed=None, view=None)

    async def update_embed(self, interaction):
        embed = self.create_search_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    def create_search_embed(self):
        embed = discord.Embed(
            title=f"🔍 Результаты поиска: {self.query}",
            color=discord.Color.blue()
        )

        # Показываем список с выделенным треком
        description_lines = []
        for i, result in enumerate(self.results):
            title = result.get('title', 'Неизвестно')
            duration = result.get('duration', 0)

            # Форматируем длительность
            if duration:
                minutes, seconds = divmod(duration, 60)
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "Неизвестно"

            # Выделяем выбранный трек жирным
            if i == self.selected_index:
                line = f"**{i + 1}. {title}** ⏱️ {duration_str} ◀️"
            else:
                line = f"{i + 1}. {title} ⏱️ {duration_str}"

            description_lines.append(line)

        embed.description = f"Найдено {len(self.results)} треков:\n\n" + "\n".join(description_lines)
        embed.set_footer(text=f"Выбран трек {self.selected_index + 1} из {len(self.results)}")

        return embed


class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="search", description="Поиск треков на YouTube")
    async def search(self, ctx):
        """Открывает модальное окно для поиска треков"""
        modal = SearchModal(self)
        await ctx.interaction.response.send_modal(modal)


async def setup(bot):
    await bot.add_cog(Search(bot))