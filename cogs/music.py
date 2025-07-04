from asyncio import sleep

import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import time
from .search import SearchModal
# Ваши существующие настройки ytdl остаются без изменений
ytdl_format_options = {
    'format': 'bestaudio/best',
    'extractaudio': True,  # Только аудио
    'audioformat': 'mp3',
    'outtmpl': '-',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'extract_flat': True,
    'geo_bypass': True,
    'socket_timeout': 15,
    'retries': 10,
    'force-ipv4': True,
    'prefer_insecure': True,
    'cachedir': False,
    'age_limit': 21,
    'extractor_args': {
        'youtube': {
            'player_client': ['android'],
            'player_skip': ['webpage'],
            'skip': ['dash', 'hls']
        }
    }
}


class MusicControlView(discord.ui.View):
    def __init__(self, music_cog, ctx):
        super().__init__(timeout=None)
        self.music_cog = music_cog
        self.ctx = ctx
        self.message = None
        self.current_track = None
        self.track_duration = 0
        self.start_time = None
        self.pause_time = 0
        self.last_pause_start = None
        self.update_task = None

    @discord.ui.button(label="🔍 Поиск", style=discord.ButtonStyle.secondary, row=1)
    async def search_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Открывает модальное окно поиска из search.py"""
        modal = SearchModal(self.music_cog)
        await interaction.response.send_modal(modal)

    def create_progress_bar(self, current_seconds, total_seconds, length=20):
        """Создает текстовый прогресс-бар"""
        if total_seconds <= 0:
            return "━━━━━━━━━━━━━━━━━━━━ 0:00 / 0:00"

        progress = min(current_seconds / total_seconds, 1.0)
        filled_length = int(length * progress)

        bar = "█" * filled_length + "░" * (length - filled_length)

        current_time = self.format_time(int(current_seconds))
        total_time = self.format_time(int(total_seconds))

        return f"{bar} {current_time} / {total_time}"

    def format_time(self, seconds):
        """Форматирует время в MM:SS или HH:MM:SS"""
        if seconds < 3600:
            return f"{seconds // 60}:{seconds % 60:02d}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{hours}:{minutes:02d}:{seconds:02d}"

    def get_current_position(self):
        """Вычисляет текущую позицию воспроизведения"""
        if not self.start_time:
            return 0

        current_time = time.time()
        elapsed = current_time - self.start_time - self.pause_time

        if self.last_pause_start:
            elapsed -= (current_time - self.last_pause_start)

        return max(0, elapsed)

    async def start_progress_updates(self):
        """Запускает периодическое обновление прогресса"""
        if self.update_task:
            self.update_task.cancel()

        self.update_task = asyncio.create_task(self._update_progress_loop())

    async def _update_progress_loop(self):
        """Цикл обновления прогресса каждые 5 секунд"""
        try:
            while True:
                if (self.ctx.voice_client and
                        self.ctx.voice_client.is_playing() and
                        self.track_duration > 0):
                    await self.update_embed()
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    def stop_progress_updates(self):
        """Останавливает обновление прогресса"""
        if self.update_task:
            self.update_task.cancel()
            self.update_task = None

    async def update_embed(self, track_info=None, duration=None):
        """Обновляет embed с информацией о текущем треке и прогрессом"""
        if not self.message:
            return

        queue = self.music_cog.get_queue(self.ctx.guild.id)

        if track_info:
            self.current_track = track_info
            self.track_duration = duration or 0
            self.start_time = time.time()
            self.pause_time = 0
            self.last_pause_start = None
            await self.start_progress_updates()

        embed = discord.Embed(
            title="🎵 Музыкальный плеер",
            color=discord.Color.blue()
        )

        if self.current_track:
            embed.add_field(
                name="🎶 Сейчас играет",
                value=f"**{self.current_track}**",
                inline=False
            )

            # Добавляем прогресс-бар
            if self.track_duration > 0:
                current_pos = self.get_current_position()
                progress_bar = self.create_progress_bar(current_pos, self.track_duration)
                embed.add_field(
                    name="⏱️ Прогресс",
                    value=f"```{progress_bar}```",
                    inline=False
                )
        else:
            embed.add_field(
                name="🎶 Статус",
                value="Ничего не играет",
                inline=False
            )

        # Показываем следующий трек в очереди
        if queue:
            next_track = queue[0] if queue else "Очередь пуста"
            embed.add_field(
                name="⏭️ Следующий трек",
                value=f"`{next_track}`",
                inline=False
            )
            embed.add_field(
                name="📋 В очереди",
                value=f"{len(queue)} треков",
                inline=True
            )
        else:
            embed.add_field(
                name="📋 Очередь",
                value="Пуста",
                inline=True
            )

        # Статус плеера
        if self.ctx.voice_client:
            if self.ctx.voice_client.is_playing():
                status = "▶️ Играет"
            elif self.ctx.voice_client.is_paused():
                status = "⏸️ На паузе"
            else:
                status = "⏹️ Остановлен"
        else:
            status = "❌ Не подключен"

        embed.add_field(name="🔊 Статус", value=status, inline=True)

        try:
            await self.message.edit(embed=embed, view=self)
        except discord.NotFound:
            self.message = None
            self.stop_progress_updates()
        except Exception as e:
            print(f"Ошибка обновления embed: {e}")

    @discord.ui.button(label='⏸️ Пауза/Продолжить', style=discord.ButtonStyle.primary)
    async def pause_resume(self, interaction: discord.Interaction, button: discord.ui.Button):
        current_time = time.time()

        if self.ctx.voice_client and self.ctx.voice_client.is_playing():
            self.ctx.voice_client.pause()
            self.last_pause_start = current_time
            await interaction.response.send_message("⏸️ Музыка приостановлена", ephemeral=True)
        elif self.ctx.voice_client and self.ctx.voice_client.is_paused():
            if self.last_pause_start:
                self.pause_time += current_time - self.last_pause_start
                self.last_pause_start = None
            self.ctx.voice_client.resume()
            await interaction.response.send_message("▶️ Музыка возобновлена", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Сейчас ничего не играет", ephemeral=True)

        await self.update_embed()

    @discord.ui.button(label='⏭️ Пропустить', style=discord.ButtonStyle.secondary)
    async def skip_track(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.voice_client and self.ctx.voice_client.is_playing():
            self.ctx.voice_client.stop()
            await interaction.response.send_message("⏭️ Трек пропущен", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Сейчас ничего не играет", ephemeral=True)

    @discord.ui.button(label='📋 Очередь', style=discord.ButtonStyle.secondary)
    async def show_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        queue = self.music_cog.get_queue(self.ctx.guild.id)
        if queue:
            message = "**📋 Очередь треков:**\n" + "\n".join(
                f"{i + 1}. {url}" for i, url in enumerate(queue[:10]))
            if len(queue) > 10:
                message += f"\n... и еще {len(queue) - 10} треков"
            await interaction.response.send_message(message, ephemeral=True)
        else:
            await interaction.response.send_message("📋 Очередь пуста", ephemeral=True)

    @discord.ui.button(label='🔊 Громкость', style=discord.ButtonStyle.secondary)
    async def volume_control(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = VolumeModal(self.ctx)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='⏹️ Стоп', style=discord.ButtonStyle.danger)
    async def stop_music(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx.voice_client:
            self.stop_progress_updates()
            await self.ctx.voice_client.disconnect()
            if self.ctx.guild.id in self.music_cog.queues:
                self.music_cog.queues[self.ctx.guild.id].clear()
            if self.message:
                await self.message.delete()
                self.message = None
            await interaction.response.defer()  # скрывает индикатор загрузки
            message = await interaction.followup.send("⏹️ Музыка остановлена, бот отключен")
            await asyncio.sleep(10)
            await message.delete()

        else:
            await interaction.response.send_message("❌ Бот не подключен к каналу")

class VolumeModal(discord.ui.Modal):
    def __init__(self, ctx):
        super().__init__(title="Настройка громкости")
        self.ctx = ctx

    volume_input = discord.ui.TextInput(
        label="Громкость (0-100)",
        placeholder="Введите значение от 0 до 100",
        min_length=1,
        max_length=3
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            volume = int(self.volume_input.value)
            if 0 <= volume <= 100:
                if self.ctx.voice_client and hasattr(self.ctx.voice_client.source, 'volume'):
                    self.ctx.voice_client.source.volume = volume / 100
                    await interaction.response.send_message(f"🔊 Громкость установлена на {volume}%", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Невозможно изменить громкость", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Громкость должна быть от 0 до 100", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Введите корректное число", ephemeral=True)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
        self.current_views = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    async def _play_next(self, ctx):
        """Воспроизводит следующий трек из очереди"""
        queue = self.get_queue(ctx.guild.id)

        if queue:
            next_url = queue.pop(0)
            await self._play(ctx, next_url, from_queue=True)
        else:
            if ctx.guild.id in self.current_views:
                view = self.current_views[ctx.guild.id]
                view.stop_progress_updates()
                await view.update_embed()

    async def _play(self, ctx, url, from_queue=False):
        """Основная функция воспроизведения с получением длительности"""
        try:
            ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

            # Получаем полную информацию о треке (включая длительность)
            ytdl_info_options = ytdl_format_options.copy()
            ytdl_info_options['extract_flat'] = False

            ytdl_info = youtube_dl.YoutubeDL(ytdl_info_options)
            info = await self.bot.loop.run_in_executor(
                None, lambda: ytdl_info.extract_info(url, download=False)
            )

            if 'entries' in info:
                info = info['entries'][0]

            title = info.get('title', url)
            audio_url = info['url']
            duration = info.get('duration', 0)

            source = discord.FFmpegPCMAudio(
                audio_url,
                before_options='-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
            )

            def after_playing(error):
                if error:
                    print(f'Ошибка воспроизведения: {error}')
                else:
                    if ctx.guild.id in self.current_views:
                        view = self.current_views[ctx.guild.id]
                        view.stop_progress_updates()
                    asyncio.run_coroutine_threadsafe(self._play_next(ctx), self.bot.loop)

            ctx.voice_client.play(source, after=after_playing)

            if ctx.guild.id in self.current_views:
                view = self.current_views[ctx.guild.id]
                await view.update_embed(title, duration)

            if not from_queue:
                duration_str = self.format_time(duration) if duration > 0 else "не определена"
                message = await ctx.send(f"🎵 Начинаю воспроизведение: **{title}** ({duration_str})")
                await asyncio.sleep(10)
                await message.delete()
        except Exception as e:
            message = await ctx.send(f"❌ Ошибка воспроизведения: {e}")
            await asyncio.sleep(10)
            await message.delete()

    def format_time(self, seconds):
        """Форматирует время в MM:SS или HH:MM:SS"""
        if seconds < 3600:
            return f"{seconds // 60}:{seconds % 60:02d}"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{hours}:{minutes:02d}:{seconds:02d}"

    @commands.command()
    async def play(self, ctx, *, url):
        await ctx.message.delete()

        if not ctx.voice_client:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                return await ctx.send("❌ Вы не подключены к голосовому каналу!")

        # Если уже что-то играет — добавляем в очередь
        if ctx.voice_client.is_playing():
            queue = self.get_queue(ctx.guild.id)
            queue.append(url)
            await ctx.send(f"➕ Добавлено в очередь: `{url}`", delete_after=5)

            # Обновляем embed, если он существует
            view = self.current_views.get(ctx.guild.id)
            if view and view.message:
                await view.update_embed()
            return

        # Проверка: существует ли уже view или нужно создать
        if ctx.guild.id not in self.current_views or not self.current_views[ctx.guild.id].message:
            view = MusicControlView(self, ctx)
            self.current_views[ctx.guild.id] = view

            embed = discord.Embed(
                title="🎵 Музыкальный плеер",
                description="Загрузка...",
                color=discord.Color.blue()
            )

            view.message = await ctx.send(embed=embed, view=view)

        # Запустить воспроизведение
        await self._play(ctx, url)
    # Ваши существующие команды остаются без изменений
    @commands.command()
    async def skip(self, ctx):
        """Пропускает текущий трек"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("Трек пропущен")
        else:
            await ctx.send("Сейчас ничего не играет")

    @commands.command()
    async def queue(self, ctx):
        """Показывает текущую очередь"""
        queue = self.get_queue(ctx.guild.id)
        if queue:
            message = "**Очередь треков:**\n" + "\n".join(
                f"{i + 1}. {url}" for i, url in enumerate(queue))
            await ctx.send(message)
        else:
            await ctx.send("Очередь пуста")

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Изменяет громкость плеера (0-100)"""
        if ctx.voice_client is None:
            return await ctx.send("Я не подключен к голосовому каналу.")

        if 0 <= volume <= 100:
            if hasattr(ctx.voice_client.source, 'volume'):
                ctx.voice_client.source.volume = volume / 100
                await ctx.send(f"Громкость установлена на {volume}%")
            else:
                await ctx.send("Невозможно изменить громкость для этого источника")
        else:
            await ctx.send("Громкость должна быть от 0 до 100")


async def setup(bot):
    await bot.add_cog(Music(bot))