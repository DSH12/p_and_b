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

client = discord.Client()

if not discord.opus.is_loaded():
    discord.opus.load_opus('opus')

voice_client = None
text_channel = None
player = None
p_dl = None
speak = False
q_file = "queue.dat"
yt_url_pattern = re.compile("^http(s)?:/\/(?:www\.)?youtube.com\/watch\?(?=.*v=\w+)(?:\S+)?$")
yt_color = 0xc4302b

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

@client.event
async def on_message(message):
    global voice_client
    global player
    global p_dl
    msg = []
    if message.content.startswith('@@'):
        msg = message.content.split()
        try:
            if 'youtube' in msg[1]:
                # await client.move_member(list(filter(lambda x: x.id == client.user.id, client.get_all_members()))[0],
                #                          client.get_channel('224886395427094529'))
                song_url = ''
                if yt_url_pattern.match(msg[1]):
                    song_url = msg[1]
                    try:
                        this_song = fetch_song(song_url)
                    except Exception as e:
                        return
                    #player.change_voice(client.voice_client_in(client.get_server('')))
                    player.queue(this_song)
            elif 'fas' in [msg[1]]:
                if not client.is_voice_connected(client.get_server('')):
                    await client.join_voice_channel(client.get_channel(message.author.voice.voice_channel.id))
                else:
                     await client.move_member(list(filter(lambda x: x.id == client.user.id, client.get_all_members()))[0],
                                         client.get_channel(message.author.voice.voice_channel.id))
                if not voice_client:
                    voice_client = client.voice_client_in(client.get_server(''))
                    player = Player(client, voice_client=voice_client)
                    p_dl = Popen(["python", "yt_downloader.py"])
                else:
                    voice_client = client.voice_client_in(client.get_server(''))
                    player.change_voice(voice_client)
            elif 'skip' in [msg[1]]:
                if player:
                    player.skip()
            elif 'volume' in [msg[1]]:
                if player:
                    if player.get_playlist():
                        try:
                            float(msg[2])
                            player.change_volume(float(msg[2]))
                        except Exception as e:
                            print("Not a float")
            elif 'душитель' in [msg[1].lower()]:
                await client.send_message(message.channel, 'Душитель: {0}'.format(random.choice(list(filter(lambda x: x.id != client.user.id, client.get_all_members()))).name))
            elif 'purge' in [msg[1]]:
                if len(list(filter(lambda x: x.name == 'nazi', message.author.roles))) > 0:
                    try:
                        int(msg[2])
                        await client.purge_from(message.channel, limit=int(msg[2]))
                    except Exception as e:
                        print('Wrong value')
            elif 'test' in [msg[1]]:
                player.check_vars()
            elif 'rgg' in [msg[1]]:
                try:
                    with open('rgg\\'+msg[2] + '.txt', 'r') as f:
                        await client.send_message(message.channel, 'Играй в {0} на {1}'.format(random.choice(f.readlines()).rstrip(), msg[2]))
                except Exception as e:
                    print(e)
            elif 'speak' in [msg[1]]:
                if not client.is_voice_connected(client.get_server('')):
                    await client.join_voice_channel(client.get_channel(message.author.voice.voice_channel.id))
                else:
                     await client.move_member(list(filter(lambda x: x.id == client.user.id, client.get_all_members()))[0],
                                         client.get_channel(message.author.voice.voice_channel.id))
                voice_client = client.voice_client_in(client.get_server(''))
                player = voice_client.create_stream_player(PCMStream())
                player.start()
        except Exception as e:
            print(e)


#@client.event
async def background_loop():
    global curr_song
    await client.wait_until_ready()
    ch = client.get_channel('368512789549023243')
    await client.change_presence(game=discord.Game(name=''))
    while not client.is_closed:
        Members = client.get_all_members()
        for i in Members:
            Roles = []
            Roles.append(i.roles)
            # print(i)
            for j in Roles:
                for k in j:
                    if k.name == 'DOG':
                        # print('{0} has role {1}'.format(i, k))
                        if not client.is_voice_connected(client.get_server('')):
                            await client.join_voice_channel(ch)
                        await client.move_member(i, ch)
        try:
            if player:
                if player.get_playlist():
                    if curr_song != player.get_playlist()[0]:
                        curr_song = player.get_playlist()[0]
                        await client.change_presence(game=discord.Game(name=curr_song.title))
                else:
                    await client.change_presence(game=discord.Game(name=''))
        except Exception as e:
            print(e)
        await asyncio.sleep(10)




def get_song_embed(song):
    if len(song.description) > 200:
        em = discord.Embed(title=" ", description=song.description[:200] + "...", colour=yt_color, url=song.url)
    else:
        em = discord.Embed(title=" ", description=song.description, colour=yt_color, url=song.url)
    em.set_author(name=song.title, url=song.url)
    em.add_field(name="Duration", value=song.duration_string, inline=True)
    em.set_thumbnail(url=song.thumbnail)
    em.add_field(name="Views", value=song.views, inline=True)
    em.add_field(name="Likes", value=song.likes, inline=True)
    em.add_field(name="Dislikes", value=song.dislikes, inline=True)
    em.set_footer(text=song.source, icon_url=yt_icon)
    return em

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

client.loop.create_task(background_loop())
client.run('')