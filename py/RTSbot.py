import os
import sys
import traceback
import discord
import random
from discord.ext import commands
import gameStats

from dotenv import load_dotenv

import matplotlib.pyplot as plt
import numpy as np

############################
###   Global Variables   ###
############################
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

client = discord.Client()
channel = client.get_channel(os.getenv('BOT_CHANNEL'))
bot = commands.Bot(command_prefix='!')

WORKING_DIR = os.getcwd()
OUT_DIR = os.path.join('.', 'out')
MAP_DIR = os.path.join('..', '..', 'maps')
ACTIVE_DIR = os.path.join('..', '..', 'activemap')

ACTIVEMAP_PATH = '//home//RTS//activemap'
MAPS_PATH = '//home//RTS//maps'


########################
###   Bot Commands   ###
########################
@bot.event
async def on_error(event, *args, **kwargs):
    message = args[0] #Gets the message object
    await event.channel.send(message)
    await event.channel.send(traceback.format_exc())


@bot.command(name='nickelback', help='Better than a photograph...')
async def nickel(ctx):
    response = 'Look at this graph!'
    await ctx.send(response)

    # Data for plotting
    t = np.arange(0.0, 2.0, 0.01)
    s = 1 + np.sin(2 * np.pi * t)

    fig, ax = plt.subplots()
    ax.plot(t, s)

    ax.set(xlabel='time (s)', ylabel='voltage (mV)',
        title='About as simple as it gets, folks')
    ax.grid()
    fig.savefig(os.path.join(OUT_DIR, 'temp.png'))
    
    with open(os.path.join(OUT_DIR, 'temp.png'), 'rb') as fp:
        await ctx.send(file=discord.File(fp, 'new_filename.png'))

    os.remove(os.path.join(OUT_DIR, 'temp.png'))


@bot.command(name='gamestats', help='Creates game statistics based off the latest.log file.')
async def gamestats(ctx):
    '''
    This function returns a witty respone to notify the user that it's working,
    then processes the latest log file and sends the graphs over chat.
    '''
    responses = ['Gotcha, Chief! Just a minute here...',
                 'Processing. Please wait...',
                 'Oof, I actually have to do something now. Hang on...',
                 'You want me to do WHAT? ...Oo, I misheard you. Sure thing, just a sec...',
                 'Upgrading Windows, your PC will restart several times. Sit back and relax...',
                 'Would you like fries with that? They\'re still cooking...',
                 'Hum something loud while others stare',
                 'I need a sec, but it\'s still faster than you could draw it!',
                ]
    response = random.choice(responses)
    await ctx.send(response)

    try:
        ecodat, builddat, unitdat = gameStats.readGameLog(gameStats.file)
    except Exception as err:
        await ctx.send('Something went wrong...')
        await ctx.send(type(err))
        await ctx.send(err)
        return None

    for team in ['red', 'blue', 'yellow', 'green']:
        if gameStats.wasInMatch(ecodat, team):
            fig, ax = gameStats.teamResourcePlot(ecodat, team=team, p=True)
            fig.savefig(os.path.join(OUT_DIR, '{}_Resources.png'.format(team)))
            

            fig, ax = gameStats.teamTroopPlot(unitdat, team=team)
            fig.savefig(os.path.join(OUT_DIR, '{}_Troops.png'.format(team)))

        
    fig, ax = gameStats.ecoIndexPlot(ecodat)
    fig.savefig(os.path.join(OUT_DIR, '0_Econ_Summary.png'))

    fig, ax = gameStats.troopIndexPlot(unitdat)
    fig.savefig(os.path.join(OUT_DIR, '1_Military_Summary.png'))
    
    # List comprehension of all the png files turned into discord file objects
    graphs = [discord.File(os.path.join(OUT_DIR, '{}'.format(f))) for f in os.listdir(os.path.join(OUT_DIR)) if f.endswith('png')]
    await ctx.send(files=graphs)

    # Clean up the files after we send them in Discord.
    for team in ['red', 'blue', 'yellow', 'green']:
        if gameStats.wasInMatch(ecodat, team):
            os.remove(os.path.join(OUT_DIR, '{}_Resources.png'.format(team)))
            os.remove(os.path.join(OUT_DIR, '{}_Troops.png'.format(team)))
    
    os.remove(os.path.join(OUT_DIR, '0_Econ_Summary.png'))
    os.remove(os.path.join(OUT_DIR, '1_Military_Summary.png'))

	
def delDir(path):
	for filename in os.listdir(path):
		file_path = os.path.join(folder, filename)
		print ("deleting file " + file_path)
		if os.path.isdir(file_path):
			delDir(file_path)
			os.rmdir(file_path)
		else:
			os.remove(file_path)
			
@bot.command(name='nextmap', help='Sets the next map by name')
@commands.check(commands.has_role('RTSBot MapControl'))
async def nextmap(ctx, arg1):
	os.chdir(ACTIVEMAP_PATH)
	folder = ACTIVEMAP_PATH
	response=''
	for filename in os.listdir(folder):
		file_path = os.path.join(folder, filename)
		delDir(file_path)
		
	await ctx.send(response)
	
@bot.command(name='listmaps', help='Show a list of available maps to play.')
async def listmaps(ctx):
	'''This function returns a list of the current available maps to chat.'''
	os.chdir(MAP_DIR)
	response = ''
	for folder in os.listdir():
		response += '{}\n'.format(folder)
	await ctx.send(response)
	os.chdir(WORKING_DIR)


@bot.command(name='currentmap', help='Information about the currently loaded map.')
async def currentmap(ctx):
    '''
    This functions main purpose is to send back the image for the current map.
    This image shows an overview of the map layout and where resource nodes are.
    The image must be created by the map-maker and provided to the server admin.
    Save the image inside the map source folder (by default: serverdir/maps)
    '''
    os.chdir(ACTIVE_DIR)
    with open('description.txt') as f:
        response = ''
        for line in f.readlines():
            response += line
            response += '\n'

    await ctx.send('Map currently loaded for the server: ')
    await ctx.send(response)
    try:
        img = discord.File('map.png')
        await ctx.send(file=img)
    except:
        await ctx.send('No map.png found!')
    os.chdir(WORKING_DIR)


async def loadmap(name):
    '''
    This function clears the load slot and copies the map folder provided over, instead.
    This function is called after the "votemap" function is complete, and cannot be
    called by chat users.
    '''
    pass


@bot.command(name='votemap', help='Vote on which map to play next.')
async def votemap(ctx):
    '''
    This function initiates a vote on the map to be loaded onto the server.

    Voting is conducted with message responses.
    Voting is limited to 11 maps (discord only has 0-10 emojis)
    '''
    os.chdir(MAP_DIR)

    await ctx.send('Respond to this message with your vote, via the appropriate emoji! Other emojis won\'t count!')
    await ctx.send('Sorry...Map-voting is currently unavailable, please be patient.')

    os.chdir(WORKING_DIR)


########################
###   Main Program   ###
########################
if __name__ == "__main__":
    bot.run(TOKEN)