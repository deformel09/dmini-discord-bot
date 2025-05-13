import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio

# Настройки для youtube-dl
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
    'extract_flat': True,
    'skip_download': True
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def join(self, ctx):
        """Подключается к голосовому каналу пользователя"""
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            await channel.connect()
            await ctx.send(f"Подключился к каналу: {channel.name}")
        else:
            await ctx.send("Вы не подключены к голосовому каналу!")

    @commands.command()
    async def leave(self, ctx):
        """Отключается от голосового канала"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Отключился от голосового канала")
        else:
            await ctx.send("Я не подключен к голосовому каналу!")

    @commands.command()
    async def play(self, ctx, *, url):
        """Воспроизводит аудио из YouTube URL"""
        if not ctx.voice_client:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("Вы не подключены к голосовому каналу!")
                return

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Ошибка плеера: {e}') if e else None)

        await ctx.send(f'Сейчас играет: {player.title}')

    @commands.command()
    async def volume(self, ctx, volume: int):
        """Изменяет громкость плеера"""
        if ctx.voice_client is None:
            return await ctx.send("Я не подключен к голосовому каналу.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Громкость изменена на {volume}%")

    @commands.command()
    async def stop(self, ctx):
        """Останавливает воспроизведение и очищает очередь"""
        if ctx.voice_client:
            ctx.voice_client.stop()
            await ctx.send("Воспроизведение остановлено")
        else:
            await ctx.send("Я не подключен к голосовому каналу.")

async def setup(bot):
    await bot.add_cog(Music(bot))