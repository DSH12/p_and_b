import sys
import re
import configparser
import urllib.parse
import urllib.request
import discord
from discord.ext import commands
from utils import *
import asyncio
from subprocess import Popen
import random
import numpy
import sounddevice as sd


class Bot:
    client = None
    voice_client = None
    text_channel = None
    player = None
    player_yt = None
    p_dl = None
    speak = False
    curr_song = None

    def __init__(self, dc):
        self.client = dc


bot = Bot(discord.Client())

if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')

q_file = "queue.dat"
yt_url_pattern = re.compile("^http(s)?:/\/(?:www\.)?youtube.com\/watch\?(?=.*v=\w+)(?:\S+)?$")
server_id = ''
token = ''
remove_file(q_file)

sd.default.device = 2  # change to desired device
sd.default.channels = 2
sd.default.dtype = 'int16'
sd.default.latency = 'low'
sd.default.samplerate = 48000


class PCMStream:
    def __init__(self):
        self.stream = sd.InputStream()
        self.stream.start()

    def read(self, num_bytes):
        # frame is 4 bytes
        frames = int(num_bytes / 4)
        data = self.stream.read(frames)[0]

        return data.tobytes()


@bot.client.event
async def on_message(message):
    msg = []
    if message.content.startswith('@@'):
        msg = message.content.split()
        try:
            if 'youtube' in msg[1] and not bot.speak:
                if bot.player:
                    song_url = ''
                    if yt_url_pattern.match(msg[1]):
                        song_url = msg[1]
                        try:
                            this_song = fetch_song(song_url)
                        except Exception as e:
                            return
                        # player.change_voice(bot.client.voice_client_in(bot.client.get_server('224886395427094528')))
                        bot.player.queue(this_song)
            elif 'fas' in [msg[1]]:
                if bot.speak:
                    bot.player.stop()
                    if bot.client.is_voice_connected(bot.client.get_server(server_id)):
                        bot.voice_client.disconnect()
                    del bot.voice_client
                    del bot.player

                if not bot.client.is_voice_connected(bot.client.get_server(server_id)):
                    await bot.client.join_voice_channel(bot.client.get_channel(message.author.voice.voice_channel.id))
                else:
                    await bot.client.move_member(list(filter(lambda x: x.id == bot.client.user.id,
                                                             bot.client.get_all_members()))[0],
                                                 bot.client.get_channel(message.author.voice.voice_channel.id))
                if not bot.voice_client or bot.speak:

                    bot.voice_client = bot.client.voice_client_in(bot.client.get_server(server_id))
                    bot.player = Player(bot.client, voice_client=bot.voice_client)
                    bot.p_dl = Popen(["python", "yt_downloader.py"])
                else:
                    voice_client = bot.client.voice_client_in(bot.client.get_server(server_id))
                    bot.player.change_voice(voice_client)
                bot.speak = False
            elif 'skip' in [msg[1]]:
                if bot.player and not bot.speak:
                    bot.player.skip()
            elif 'volume' in [msg[1]]:
                if bot.player:
                    if bot.player.get_playlist():
                        try:
                            float(msg[2])
                            bot.player.change_volume(float(msg[2]))
                        except Exception as e:
                            print("Not a float")
            elif 'душитель' in [msg[1].lower()]:
                await bot.client.send_message(message.channel,
                                              'Душитель: {0}'.format(random.choice(list(
                                                  filter(lambda x: x.id != bot.client.user.id,
                                                         bot.client.get_all_members()))).name))
            elif 'purge' in [msg[1]]:
                if len(list(filter(lambda x: x.name == 'nazi', message.author.roles))) > 0:
                    try:
                        int(msg[2])
                        await bot.client.purge_from(message.channel, limit=int(msg[2]))
                    except Exception as e:
                        print('Wrong value')
            elif 'test' in [msg[1]]:
                bot.player.check_vars()
            elif 'rgg' in [msg[1]]:
                try:
                    with open('rgg\\' + msg[2] + '.txt', 'r') as f:
                        await bot.client.send_message(message.channel,
                                                      'Играй в {0} на {1}'.format(random.choice(f.readlines()).rstrip(),
                                                                                  msg[2]))
                except Exception as e:
                    print(e)
            elif 'speak' in [msg[1]]:
                if not bot.speak and bot.player:
                    bot.player.stop()
                    if bot.client.is_voice_connected(bot.client.get_server(server_id)):
                        bot.voice_client.disconnect()
                    del bot.voice_client
                    del bot.p_dl
                    del bot.player
                    remove_file(q_file)
                if not bot.client.is_voice_connected(bot.client.get_server(server_id)):
                    await bot.client.join_voice_channel(bot.client.get_channel(message.author.voice.voice_channel.id))
                else:
                    await bot.client.move_member(
                        list(filter(lambda x: x.id == bot.client.user.id, bot.client.get_all_members()))[0],
                        bot.client.get_channel(message.author.voice.voice_channel.id))
                bot.voice_client = bot.client.voice_client_in(bot.client.get_server(server_id))
                bot.player = bot.voice_client.create_stream_player(PCMStream())
                bot.player.start()
                bot.speak = True
        except Exception as e:
            print(e)


# @bot.client.event
async def background_loop():
    await bot.client.wait_until_ready()
    ch = bot.client.get_channel('368512789549023243')
    await bot.client.change_presence(game=discord.Game(name=''))
    while not bot.client.is_closed:
        for Member in bot.client.get_all_members():
            Roles = Member.roles
            if len(list(filter(lambda x: x.name == 'DOG', Roles))) > 0:
                if not bot.client.is_voice_connected(bot.client.get_server(server_id)):
                    await bot.client.join_voice_channel(ch)
                await bot.client.move_member(Member, ch)
        try:
            if bot.player and not bot.speak:
                if bot.player.get_playlist():
                    if bot.curr_song != bot.player.get_playlist()[0]:
                        bot.curr_song = bot.player.get_playlist()[0]
                        await bot.client.change_presence(game=discord.Game(name=bot.curr_song.title))
                else:
                    await bot.client.change_presence(game=discord.Game(name=''))
        except Exception as e:
            print(e)
        await asyncio.sleep(10)


@bot.client.event
async def on_ready():
    print('Logged in as')
    print(bot.client.user.name)
    print(bot.client.user.id)
    print('------')


bot.client.loop.create_task(background_loop())
bot.client.run(token)
