#https://www.reddit.com/r/Competitiveoverwatch/comments/7p0e8d/owl_api_analysis/

import requests
import pandas as pd
import json
from pandas.io.json import json_normalize

def flatten_json(y):
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + '_')
                i += 1
        else:
            out[name[:-1]] = x

    flatten(y)
    return out
    
def getOWL (url, key = 'data'):
    # Make a get request to get the latest position of the international space station from the opennotify api.
    r = requests.get(url)
    data = r.json()
    print(type(data))
    data = data[key]
    return data

#player stats

r = requests.get('https://api.overwatchleague.com/stats/players')
r = r.json()
r = r['data']

stats = pd.DataFrame(r)
teams = pd.read_csv(r'C:\Users\rjohns17\Desktop\Data Science\Python\OWL\teams.csv')
teams = teams.iloc[:,0:2]
stats['name'] = stats['name'].str.upper()

stats = pd.merge(stats, teams, left_on='name', right_on='Player', how='left')
stats = stats.drop('Player', axis=1)
stats = stats.fillna('FreeAgent')


stats['points10m'] = (stats['eliminations_avg_per_10m'] * .5) + \
                    (stats['healing_avg_per_10m']/1000) + \
                     (stats['hero_damage_avg_per_10m']/1000)
                     
stats['minutes_played'] = stats['time_played_total']/60
stats['totalPoints'] = stats['points10m'] * (stats['minutes_played']/10)

filt = stats['Fantasy Team'].isin(['Jyeran','FreeAgent'])

#matches
url = "https://api.overwatchleague.com/matches"
data = getOWL(url, 'content')


r = requests.get('https://api.overwatchleague.com/matches')
r = r.json()
match = json_normalize(r['content'])#, record_path=['teams'], meta=['name','id'])

listOmatches = []

for i in range(0,len(data)):
    dataDict = dict(data[i])
    listOmatches.append(dataDict['id'])

match = match[['id','startDate']]

match['date'] = pd.to_datetime(match['startDate'],unit='ms')

matchStage = pd.read_csv(r'C:\Users\rjohns17\Desktop\Data Science\Python\OWL\matchStages.csv')

match = pd.merge(match, matchStage)


#get player IDs
r = requests.get('https://api.overwatchleague.com/players')
r = r.json()
players = json_normalize(r['content'], record_path=['teams'], meta=['name','id'])
players['teamID'] = 0

for p in range(0,len(players)):
    team = players.iloc[p,2]
    teamID = team['id']
    players.iloc[p,-1] = teamID

players = players[['name','id','teamID']]
    
#get team IDs
r = requests.get('https://api.overwatchleague.com/teams')

r = r.json()
teams = json_normalize(r['competitors'])
teams = teams[['competitor.name','competitor.abbreviatedName','competitor.id']]
teams = teams.rename(index=str, columns={"competitor.name": "teamName", "competitor.abbreviatedName": "abbrev","competitor.id":"teamID"})


players = pd.merge(players, teams, left_on = 'teamID', right_on='teamID', how='left')



#matches = pd.DataFrame.from_dict(data)
#match.to_csv(r'C:\Users\rjohns17\Desktop\Data Science\Python\OWL\match.csv')

# Print the status code of the response.

#https://api.overwatchleague.com/stats/matches/21211/maps/1
#https://api.overwatchleague.com/matches/21252
#https://api.overwatchleague.com/matches/21176


#matchstat data
games = []

for m in range(0,len(match)):
    url = r'https://api.overwatchleague.com/matches/' + str(match.iloc[m,0])
    r = requests.get(url)
    r = r.json()
    matchScore = json_normalize(r, record_path=['scores'], meta=['id'])
    matchScore2 = json_normalize(r, record_path=['games'])
    matchScore2 = matchScore2[['number']]
    
    if matchScore2.empty == True:
        games.append(0)
    else:
        games.append(matchScore2['number'].max())


match['games'] = games

filt = match['games'] > 0
playedMatch = match.loc[filt]



#go through each match
matchStats = pd.DataFrame(columns = ['name', 'value', 'Hero_name', 'player', 'match', 'game'])
for i, m in playedMatch.iterrows():
    url = r'https://api.overwatchleague.com/stats/matches/' + str(m['id']) + r'/maps/'
    
    #go through each game
    for g in range(0, m['games']):
        urlG = url + str(g+1)
        
        r = requests.get(urlG)
        r = r.json()
        
        pGame = json_normalize(r, record_path=['teams','players'], meta=['esports_match_id', ['game_number']])
        
        for p, row in pGame.iterrows():
            pStat = json_normalize(pGame.iloc[p,1], record_path=['stats'], meta=['name'], meta_prefix='Hero_')
            pStat['player'] = row['esports_player_id']
            pStat['match'] = row['esports_match_id']
            pStat['game'] = row['game_number']

            filt = pStat.columns != 'id'
            pStat = pStat.loc[:,filt]
            matchStats = pd.concat([matchStats, pStat])

matchStatsP = pd.pivot_table(matchStats,index=['player','match','game','Hero_name'],columns=['name'], values='value',fill_value=0).reset_index()

statsThe = pd.merge(matchStatsP, players, left_on = 'player', right_on='id')
statsThe['points'] = (statsThe['eliminations'] * .5) + (statsThe['damage']/1000) + (statsThe['healing']/1000) 

statsThe = pd.merge(statsThe, playedMatch[['id','tag']], left_on = 'match', right_on='id')    
        
        #add up stats for each player in game to temp player table
    
    #if point total is less than current existing in player table in same week
    #replace master player entry with temp entry
    
        
statsThe.to_csv(r'C:\Users\rjohns17\Desktop\Data Science\Python\OWL\matchStats.csv')





















