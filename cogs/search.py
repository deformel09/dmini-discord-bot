import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio

# Настройки для поиска на YouTube
search_options = {
    'quiet': True,
    'no_warnings': True,
    'extractaudio': False,
    'format': 'best',
    'noplaylist': True,
    'extract_flat': True,
    'force_json': True,
    'geo_bypass': True,
    'socket_timeout': 15,
    'retries': 3,
    'ignoreerrors': True,
    'extractor_args': {
        'youtube': {
            'player_client': ['android'],
            'player_skip': ['webpage'],
        }
    }
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
        print(f"🔍 Поиск: {query}")  # Для отладки

        try:
            # Создаем поисковый запрос
            search_query = f"ytsearch10:{query}"

            # Настройки для поиска
            ytdl_opts = search_options.copy()

            with youtube_dl.YoutubeDL(ytdl_opts) as ytdl:
                search_results = await interaction.client.loop.run_in_executor(
                    None, lambda: ytdl.extract_info(search_query, download=False)
                )

            print(f"📊 Результаты поиска: {search_results}")  # Для отладки

            if not search_results:
                await interaction.followup.send("❌ Ошибка при выполнении поиска!")
                return

            # Проверяем есть ли результаты
            entries = search_results.get('entries', [])
            if not entries:
                await interaction.followup.send("❌ Ничего не найдено!")
                return

            # Фильтруем результаты (убираем None)
            results = [entry for entry in entries if entry is not None][:10]

            if not results:
                await interaction.followup.send("❌ Не удалось получить результаты поиска!")
                return

            print(f"✅ Найдено {len(results)} треков")  # Для отладки

            # Создаем embed и view для навигации
            embed = self.create_search_embed(query, results, 0)
            view = SearchNavigationView(results, query, self.search_cog)

            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            print(f"❌ Ошибка поиска: {e}")  # Для отладки
            await interaction.followup.send(f"❌ Ошибка при поиске: {str(e)}")

    def create_search_embed(self, query, results, selected_index):
        embed = discord.Embed(
            title=f"🔍 Результаты поиска: {query}",
            color=discord.Color.blue()
        )

        description_lines = []
        for i, result in enumerate(results):
            title = result.get('title', 'Неизвестно')
            duration = result.get('duration', 0)
            uploader = result.get('uploader', 'Неизвестный канал')

            # Форматируем длительность
            if duration and duration > 0:
                minutes, seconds = divmod(duration, 60)
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "Неизвестно"

            # Выделяем выбранный трек
            if i == selected_index:
                line = f"**{i + 1}. {title}** \n📺 {uploader} | ⏱️ {duration_str} ◀️"
            else:
                line = f"{i + 1}. {title} \n📺 {uploader} | ⏱️ {duration_str}"

            description_lines.append(line)

        embed.description = f"Найдено {len(results)} треков:\n\n" + "\n".join(description_lines)
        embed.set_footer(text=f"Выбран трек {selected_index + 1} из {len(results)}")

        return embed


class SearchNavigationView(discord.ui.View):
    def __init__(self, results, query, search_cog):
        super().__init__(timeout=300)
        self.results = results
        self.query = query
        self.search_cog = search_cog
        self.selected_index = 0

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
        # Получаем URL для воспроизведения
        video_url = f"https://www.youtube.com/watch?v={selected_track.get('id', '')}"
        title = selected_track.get('title', 'Неизвестно')

        music_cog = interaction.client.get_cog('Music')
        if music_cog:
            try:
                # Создаем фейковый контекст для команды play
                class FakeContext:
                    def __init__(self, interaction):
                        self.author = interaction.user
                        self.guild = interaction.guild
                        self.channel = interaction.channel
                        self.voice_client = interaction.guild.voice_client
                        self.bot = interaction.client

                ctx = FakeContext(interaction)
                await music_cog.play(ctx, url=video_url)
                await interaction.response.send_message(f"▶️ Воспроизводится: **{title}**", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ Ошибка воспроизведения: {str(e)}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Музыкальный модуль не найден!", ephemeral=True)

    @discord.ui.button(label='➕ В очередь', style=discord.ButtonStyle.primary)
    async def queue_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        selected_track = self.results[self.selected_index]
        video_url = f"https://www.youtube.com/watch?v={selected_track.get('id', '')}"
        title = selected_track.get('title', 'Неизвестно')

        music_cog = interaction.client.get_cog('Music')
        if music_cog:
            try:
                guild_id = interaction.guild.id
                if not hasattr(music_cog, 'queues'):
                    music_cog.queues = {}
                if guild_id not in music_cog.queues:
                    music_cog.queues[guild_id] = []
                music_cog.queues[guild_id].append(video_url)

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

        description_lines = []
        for i, result in enumerate(self.results):
            title = result.get('title', 'Неизвестно')
            duration = result.get('duration', 0)
            uploader = result.get('uploader', 'Неизвестный канал')

            if duration and duration > 0:
                minutes, seconds = divmod(duration, 60)
                duration_str = f"{minutes}:{seconds:02d}"
            else:
                duration_str = "Неизвестно"

            if i == self.selected_index:
                line = f"**{i + 1}. {title}** \n📺 {uploader} | ⏱️ {duration_str} ◀️"
            else:
                line = f"{i + 1}. {title} \n📺 {uploader} | ⏱️ {duration_str}"

            description_lines.append(line)

        embed.description = f"Найдено {len(self.results)} треков:\n\n" + "\n".join(description_lines)
        embed.set_footer(text=f"Выбран трек {self.selected_index + 1} из {len(self.results)}")

        return embed


class SearchButton(discord.ui.View):
    def __init__(self, search_cog):
        super().__init__(timeout=60)
        self.search_cog = search_cog

    @discord.ui.button(label='🔍 Открыть поиск', style=discord.ButtonStyle.primary)
    async def open_search(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = SearchModal(self.search_cog)
        await interaction.response.send_modal(modal)


class Search(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="search", description="Поиск треков на YouTube")
    async def search(self, ctx):
        """Открывает кнопку для поиска треков"""
        view = SearchButton(self)
        await ctx.send("🔍 Нажмите кнопку для открытия поиска:", view=view)


async def setup(bot):
    await bot.add_cog(Search(bot))