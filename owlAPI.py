#https://www.reddit.com/r/Competitiveoverwatch/comments/7p0e8d/owl_api_analysis/

import requests
import pandas as pd
import json
from pandas.io.json import json_normalize

    
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
teams = pd.read_csv(r'C:\Users\Jyran\Documents\GitHub\OWL\teams.csv')
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

playerRole = stats[['name','role']]






#matches
url = "https://api.overwatchleague.com/matches"
data = getOWL(url, 'content')


r = requests.get('https://api.overwatchleague.com/matches')
r = r.json()
match = json_normalize(r['content'],record_path=['competitors'],meta=['id','startDate'], meta_prefix='match_')#, record_path=['teams'], meta=['name','id'])
match = match[['match_id','match_startDate','name']].sort_values('match_id').reset_index()
match['name2'] = ''

for i, r in match.iterrows():
    if ((i+2)%2)==0:
        match.iloc[i,-1] = match.iloc[i+1,-2]
    else:
        match.iloc[i,-1] = match.iloc[i-1,-2]

match['contest'] = match['name'] + ' vs. ' + match['name2']
match = match.iloc[::2].rename(columns={'match_id':'id','match_startDate':'startDate'})

listOmatches = []

for i in range(0,len(data)):
    dataDict = dict(data[i])
    listOmatches.append(dataDict['id'])

match = match[['id','startDate', 'contest']]

match['date'] = pd.to_datetime(match['startDate'],unit='ms')

matchStage = pd.read_csv(r'C:\Users\Jyran\Documents\GitHub\OWL\matchStages.csv')

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
    
    if matchScore2.empty == False:
        flag = (matchScore2[['state']] == 'PENDING').any().any()
    
    if matchScore2.empty == True or flag:
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
      
statsThe['matchgame'] =   statsThe['match'] + statsThe['game']
        #add up stats for each player in game to temp player table
    
    #if point total is less than current existing in player table in same week
    #replace master player entry with temp entry
    
weekly = statsThe.groupby(['player','tag']).agg({'match':'nunique','matchgame':'nunique'}).reset_index()

statsThe = pd.merge(statsThe, weekly, left_on = 'player', right_on='player')

statsThe = statsThe.rename(columns={'match_x':'match', 'id_x':'playerID','id_y':'matchID','matchgame_x':'matchgame','tag_x':'tag','Hero_name':'hero'})
statsThe = statsThe.iloc[:,0:-3]

#create "Fantasy Stats"
fantasyStatsBase = statsThe.groupby(['name','tag', 'teamName', 'match']).agg({'eliminations':'sum','damage':'sum','healing':'sum','points':'sum'}).reset_index()     
fantasyStats = fantasyStatsBase.groupby(['name', 'tag']).agg({'points':'max'}).reset_index()
fantasyStats = pd.merge(fantasyStats, fantasyStatsBase, left_on='points',right_on='points', how='left').rename(columns={'tag_x':'tag','name_x':'name'})
fantasyStats = pd.merge(fantasyStats, match[['id','contest']], left_on='match',right_on='id', how='left')
fantasyStats['name'] = fantasyStats['name'].str.upper()
fantasyStats = pd.merge(fantasyStats, playerRole, left_on='name',right_on='name', how='left').rename(columns={'name_x':'name'})

statsThe =pd.merge(statsThe, match[['id','contest']], left_on='match',right_on='id', how='left')
statsThe['name'] = statsThe['name'].str.upper()
statsThe = pd.merge(statsThe, playerRole, left_on='name',right_on='name', how='left').rename(columns={'name_x':'name'})


gamesPlayed = fullStats.groupby(['name']).agg({'match':'nunique'}).reset_index()
mapsPlayed = fullStats.groupby(['name', 'match']).agg({'game':'nunique'}).reset_index()
mapsPlayed = mapsPlayed.groupby(['name']).agg({'game':'sum'}).reset_index()


fantasyStats = pd.merge(fantasyStats, gamesPlayed, left_on='name', right_on='name').rename(columns={'match_x':'match','match_y':'matchesPlayed','name_x':'name'})
fantasyStats = pd.merge(fantasyStats, mapsPlayed,  left_on='name', right_on='name').rename(columns={'game':'mapsPlayed','name_x':'name'})


#statsThe = pd.merge(statsThe, gamesPlayed, left_on='name', right_on='name').rename(columns={'match':'matchesPlayed','name_x':'name'})
#statsThe = pd.merge(statsThe, mapsPlayed,  left_on='name', right_on='name').rename(columns={'game':'mapsPlayed','name_x':'name'})



cols = ['name','role','tag','teamName','contest','matchesPlayed','mapsPlayed','points','eliminations','damage','healing']
fantasyStats = fantasyStats[cols]

cols = ['name','role','teamName','abbrev', 'contest', 'game','tag','hero',
        'points','eliminations', 'damage', 'healing', 'deaths']
fullStats = statsThe[cols]


#mess with bliz stats


stats = pd.merge(stats, gamesPlayed, left_on='name', right_on='name').rename(columns={'match':'matchesPlayed','name_x':'name'})
stats = pd.merge(stats, mapsPlayed,  left_on='name', right_on='name').rename(columns={'game':'mapsPlayed','name_x':'name'})

cols = [
 'name',
 'role',
 'team',
 'minutes_played',
 'matchesPlayed',
 'mapsPlayed',
 'points10m',
 'totalPoints',
 'eliminations_avg_per_10m',
 'healing_avg_per_10m',
 'hero_damage_avg_per_10m',
 'ultimates_earned_avg_per_10m',
 'deaths_avg_per_10m',
 'final_blows_avg_per_10m'
 ]

stats = stats[cols]

#write dataframe
fantasyStats.to_csv(r'C:\Users\Jyran\Documents\GitHub\OWL\fantasyStats.csv')
fullStats.to_csv(r'C:\Users\Jyran\Documents\GitHub\OWL\fullStats.csv')
stats.to_csv(r'C:\Users\Jyran\Documents\GitHub\OWL\blizzStats.csv')





















