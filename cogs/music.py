import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio

# Настройки для youtube-dl (оптимизированы для потокового воспроизведения)
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

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -bufsize 512k'  # Настройки буферизации для плавного воспроизведения
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):  # Всегда stream=True
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url']  # Всегда используем URL для потокового воспроизведения
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    @commands.command()
    async def join(self, ctx):
        """Подключается к голосовому каналу пользователя"""
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.voice_client:
                await ctx.voice_client.move_to(channel)
            else:
                await channel.connect()
            await ctx.send(f"Подключился к каналу: {channel.name}")
        else:
            await ctx.send("Вы не подключены к голосовому каналу!")

    @commands.command()
    async def leave(self, ctx):
        """Отключается от голосового канала"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            self.queues.pop(ctx.guild.id, None)  # Очищаем очередь
            await ctx.send("Отключился от голосового канала")
        else:
            await ctx.send("Я не подключен к голосовому каналу!")

    async def play_next(self, ctx):
        queue = self.get_queue(ctx.guild.id)
        if queue:
            next_url = queue.pop(0)
            await self._play(ctx, next_url)

    async def _play(self, ctx, url):
        try:
            async with ctx.typing():
                player = await YTDLSource.from_url(url, loop=self.bot.loop)

                def after_playing(error):
                    if error:
                        print(f'Ошибка плеера: {error}')
                    asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop)

                ctx.voice_client.play(player, after=after_playing)
                await ctx.send(f'Сейчас играет: {player.title}')
        except Exception as e:
            await ctx.send(f"Произошла ошибка: {str(e)}")

    @commands.command()
    async def play(self, ctx, *, url):
        """Воспроизводит аудио из YouTube URL (потоковое)"""
        if not ctx.voice_client:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("Вы не подключены к голосовому каналу!")
                return

        # Проверяем, играет ли что-то сейчас
        if ctx.voice_client.is_playing():
            queue = self.get_queue(ctx.guild.id)
            queue.append(url)
            await ctx.send(f"Трек добавлен в очередь. Позиция в очереди: {len(queue)}")
            return

        await self._play(ctx, url)

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
                f"{i+1}. {url}" for i, url in enumerate(queue))
            await ctx.send(message)
        else:
            await ctx.send("Очередь пуста")

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Изменяет громкость плеера (0-100)"""
        if ctx.voice_client is None:
            return await ctx.send("Я не подключен к голосовому каналу.")

        if 0 <= volume <= 100:
            ctx.voice_client.source.volume = volume / 100
            await ctx.send(f"Громкость изменена на {volume}%")
        else:
            await ctx.send("Громкость должна быть между 0 и 100")

    @commands.command()
    async def pause(self, ctx):
        """Приостанавливает воспроизведение"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("Воспроизведение приостановлено")
        else:
            await ctx.send("Сейчас ничего не играет")

    @commands.command()
    async def resume(self, ctx):
        """Возобновляет воспроизведение"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("Воспроизведение возобновлено")
        else:
            await ctx.send("Воспроизведение не приостановлено")

    @commands.command()
    async def stop(self, ctx):
        """Останавливает воспроизведение и очищает очередь"""
        if ctx.voice_client:
            ctx.voice_client.stop()
            self.queues.pop(ctx.guild.id, None)  # Очищаем очередь
            await ctx.send("Воспроизведение остановлено и очередь очищена")
        else:
            await ctx.send("Я не подключен к голосовому каналу.")


async def setup(bot):
    await bot.add_cog(Music(bot))