# coding: utf-8



import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import pandas as pd
import os
import sys
import datetime
import logging

# Global Variables
# Hardcoded filepath for testing and dev purposes
file = os.path.join('.', 'out', 'latest.log')


def readGameLog(file):
    '''
    This function reads a Minecraft log file (with RTSCraft logging enabled), and puts
    the data into pandas dataframes for quick processing and graphing.

    Input is a filepath (filename if in cwd).
    Returns ecodat, builddat, and troopdat dataframes of economy, buildings, and troop
    info from the match.
    '''
    # Initialize the data array
    data = pd.DataFrame(dtype=float)

    temp1 = []
    temp2 = []
    temp3 = []
    building_columns = []
    units_columns = []
    with open(file) as f:
        for line in f.readlines():
            # If it's a line with eco stat data (they are all flagged)
            if 'ECOSTATS' in line:
                # Cut off the preceding bits we dont care about
                cache1 = line.split(sep='ECOSTATS: ,')[1]
                temp1.append(cache1.split(sep=','))
            # Same for buildings data
            elif 'BUILDINGSTATS:' in line:
                cache2 = line.split(sep='BUILDINGSTATS: ,')[1]
                temp2.append(cache2.split(sep=','))
            # Same for troop data
            elif 'UNITSTATUS:' in line:
                cache3 = line.split(sep='UNITSTATUS: ,')[1]
                temp3.append(cache3.split(sep=','))
            # At the beginning of the match, each player joins a team
            # TODO: Grab the player names in the match.
            elif 'BUILDINGSTATS-HEADER:' in line:
                building_columns = line.split(sep='HEADER:')[1].split(sep=',')
                building_columns = [v.strip() for v in building_columns]
            elif 'UNITSTATUS-HEADER:' in line:
                units_columns = line.split(sep='HEADER:')[1].split(sep=',')
                units_columns = [v.strip() for v in units_columns]

                
                
                
    ecodat = data.append(temp1)
    ecodat.columns=['Time', 'Team',
                    'Food_Prod', 'Lumber_Prod', 'Stone_Prod', 'Iron_Prod', 'Gold_Prod', 'Diamond_Prod', 'Emerald_Prod',
                    'Food'     , 'Lumber'     , 'Stone'     , 'Iron'     , 'Gold'     , 'Diamonds'    , 'Emeralds'
                   ]


    ecodat.Time = pd.to_datetime(ecodat.Time)
    ecodat.Time = ecodat.Time.apply(lambda x: x.time())
    ecodat.Team = ecodat.Team.astype(str)
    for col in list(ecodat.columns)[2:]:
        ecodat[col] = ecodat[col].astype(int)
    logging.info('Econ: \n{}'.format(ecodat.dtypes))

    builddat = data.append(temp2)
    builddat.columns = building_columns
    builddat.Timestamp = pd.to_datetime(builddat.Timestamp)
    builddat.Timestamp = builddat.Timestamp.apply(lambda x: x.time())
    builddat.TeamName = builddat.TeamName.astype(str)
    for col in list(builddat.columns)[2:]:
        builddat[col] = builddat[col].astype(int)
    logging.info('Buildings: \n{}'.format(builddat.dtypes))


    unitdat = data.append(temp3)
    unitdat.columns = units_columns
    unitdat.Timestamp = pd.to_datetime(unitdat.Timestamp)
    unitdat.Timestamp = unitdat.Timestamp.apply(lambda x: x.time())
    unitdat.TeamName = unitdat.TeamName.astype(str)
    for col in list(unitdat.columns)[2:]:
        unitdat[col] = unitdat[col].astype(int)

    logging.info('Troops: \n{}'.format(ecodat.dtypes))

    return ecodat, builddat, unitdat



def wasInMatch(df, team):
    '''
    This function checks the eco dataframe provided, and returns a boolean of whether the provided team,
    was or was not playing.
    '''
    # Copy the data for this team only
    df = df.loc[df.Team == team].copy()
    
    if df.Food_Prod.sum() == 0:
        return False
    else:
        return True
    
    

def teamResourcePlot(df, team='red', p=True):
    '''
    Creates a resource plot for a team. Valid team names are: red, blue, green, yellow.
    If p is True include production rates for all resources on the plot.
    
    Returns a matplotlib figure and axes and plots the figure.
    '''
    # Copy the data for this team only
    df = df.loc[df.Team == team].copy()
    
    # Drop the uninteresting bits.
    # For now, start plotting after the townhall is placed (when production initializes)
    # The townhall generates some food, so as long as it is positive, the team is still in play.
    df = df.loc[df.Food >= 0].copy()
    
    # Set time to be index for automatic plots crossed with time
    df.set_index(df.Time, inplace=True)
    
    if p:
        fig, axes = plt.subplots(nrows=2, ncols=1, figsize=(19,14) )
        ax1 = df.plot(ax=axes[0], y=['Food', 'Lumber', 'Stone', 'Iron', 'Gold', 'Diamonds', 'Emeralds'], color=['orange', 'g', 'k', 'grey', 'gold', 'cyan', 'lime'])
        ax2 = df.plot(ax=axes[1], y=['Food_Prod', 'Lumber_Prod', 'Stone_Prod', 'Iron_Prod', 'Gold_Prod', 'Diamond_Prod'], color=['orange', 'g', 'k', 'grey', 'gold', 'cyan'], style=':')
        
        ax1.set_title('{} Team Resources\n'.format(team.title()), fontsize=24)
        ax1.set_xlabel(None)
        
        # ax1.xaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=10))      # 10 major ticks overall
        # ax2.xaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=10))      # 10 major ticks overall
       
        ax1.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
        ax2.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
        
        # ax1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M:%S'))
        # ax2.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M:%S'))

        ax1.grid(alpha=0.3, linestyle=':', linewidth=1.5)
        ax1.grid(alpha=0.5, linestyle=':', linewidth=1.25, which='minor')

        ax2.grid(alpha=0.3, linestyle=':', linewidth=1.5)
        ax2.grid(alpha=0.5, linestyle=':', linewidth=1.25, which='minor')
       
        ax2.set_title('Production Rates')

    else:
        ax1 = df.plot(y=['Food', 'Lumber', 'Stone', 'Iron', 'Gold'], figsize=(19,7), title='{} Team Resources'.format(team.title()))
        fig = ax1.get_figure()
    
    return fig, ax1


def ecoIndexPlot(df, w=[1, 1.2, 0.7, 0.85, 1.35, 1.2]):
    '''
    This function creates a plot representing the Economic Power of each team during the match.
    The economic index is calculated as the sum of each resource production, times its stored amount, times its weight.
    The sum is then divided a factor for ease of plotting.
    
    Returns a matplotlib figure and axes, and plots the figure. 
    '''
    df['Econ'] = (   w[0]*df.Food_Prod*df.Food      + \
                     w[1]*df.Lumber_Prod*df.Lumber  + \
                     w[2]*df.Stone_Prod*df.Stone    + \
                     w[3]*df.Iron_Prod*df.Iron      + \
                     w[4]*df.Gold_Prod*df.Gold      + \
                     w[5]*df.Diamond_Prod*df.Diamonds \
                )/(5000*len(w))
    df.set_index(df.Time, inplace=True)
    # Trim the df before the townhall is placed.
    df = df.loc[df.Food_Prod >= 5].copy()

    # initiate the plot
    fig, ax = plt.subplots(figsize=(19,7))

    # group the df by team, and add each one to the axes with the appropriate color
    for name, group in df.groupby(df.Team):
        group.Econ.plot(ax=ax, color=name[:1],label=name)


    ax.legend()
    ax.set_title('Economic Power', fontsize=24)
    ax.text(0.005, 0.3, s='weights={}'.format(w), transform=ax.transAxes)
    # ax.xaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=10))      # 10 major ticks overall
    ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    # ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M:%S'))
    ax.grid(alpha=0.3, linestyle=':', linewidth=1.5)
    ax.grid(alpha=0.5, linestyle=':', linewidth=1.25, which='minor')
    
    return fig, ax


def teamTroopPlot(df, team='red'):
    '''
    Creates a troop plot for a team. Valid team names are: red, blue, green, yellow.
    
    Returns a matplotlib figure and axes, and plots the figure.
    '''
    # Copy the data for this team only
    df = df.loc[df.TeamName == team].copy()
    # Set time to be index for automatic plots crossed with time
    df.set_index(df.Timestamp, inplace=True)
    
    fig, ax = plt.subplots(figsize=(19,7))
    ax = df.plot(ax=ax, y=list(df.columns)[2:])
    
    ax.set_title('{} Team Troops\n'.format(team.title()), fontsize=24)
    ax.set_xlabel(None)

    # ax.xaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=10))      # 10 major ticks overall
    ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    # ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M:%S'))
    ax.grid(alpha=0.3, linestyle=':', linewidth=1.5)
    ax.grid(alpha=0.5, linestyle=':', linewidth=1.25, which='minor')
    
    return fig, ax


def troopIndexPlot(df):
    '''
    This function creates a plot representing the Military Power of each team during the match.
    The military power is calculated as the sum of 
    '''
    # Index formula
    # (backslashes just signify continuation on the next line.)
    df['Power'] = df.Minion + df.Archer            +\
                  df.Lancer + df.Pikeman           +\
                  df.Trebuchet                     +\
                  df.Knight + df['AdvancedKnight'] +\
                  df.Longbowmen + df.Crossbowmen   +\
                  df.Sapper
    df.set_index(df.Timestamp, inplace=True)

    # initiate the plot
    fig, ax = plt.subplots(figsize=(19,7))

    # group the df by team, and add each one to the axes with the appropriate color
    for name, group in df.groupby(df.TeamName):
        group.Power.plot(ax=ax, color=name[:1], label=name)


    ax.legend()
    ax.set_title('Military Power', fontsize=24)
    # ax.text(0.005, 0.3, s='weights={}'.format(w), transform=ax.transAxes)
    # ax.xaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=10))      # 10 major ticks overall
    ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    # ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%H:%M:%S'))
    ax.grid(alpha=0.3, linestyle=':', linewidth=1.5)
    ax.grid(alpha=0.5, linestyle=':', linewidth=1.25, which='minor')
    
    return fig, ax


###############################
###     MAIN PROGRAM        ###
###############################

# This section will run, only if directly called from the terminal (python gameStats.py)
if __name__ == "__main__":
    print('=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')
    print('Python version ' + sys.version)
    print('Numpy version ' + np.version.version)
    print('Pandas version ' + pd.__version__)
    print('MatplotLib version ' + matplotlib.__version__)
    print('=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=')
    logging.info('Program start.')

    ecodat, builddat, unitdat = readGameLog('latest.log')
    fig, ax = ecoIndexPlot(ecodat)
    fig.savefig('0_Econ_Summary.png')


    for team in ['red', 'blue', 'yellow', 'green']:
        if wasInMatch(ecodat, team):
            fig, ax = teamResourcePlot(ecodat, team=team, p=True)
            fig.savefig('{}_Resources.png'.format(team))

            fig, ax = teamTroopPlot(unitdat, team=team)
            fig.savefig('{}_Troops.png'.format(team))

        
    fig, ax = troopIndexPlot(unitdat)
    fig.savefig('1_Military_Summary.png')