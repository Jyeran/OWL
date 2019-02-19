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
url = "https://api.overwatchleague.com/stats/players"
stats = pd.DataFrame.from_dict(getOWL(url))
stats.to_csv('stats.csv')

#matches
url = "https://api.overwatchleague.com/matches"
data = getOWL(url, 'content')


listOmatches = []

for i in range(0,len(data)):
    dataDict = dict(data[i])
    listOmatches.append(dataDict['id'])


#get player IDs
r = requests.get('https://api.overwatchleague.com/players')
r = r.json()
r = r['content']

players = pd.DataFrame(r)

players = players[['name','id']]
    
#get team IDs
r = requests.get('https://api.overwatchleague.com/teams')

r = r.json()
teams = json_normalize(r['competitors'])
teams = teams[['competitor.name','competitor.homeLocation','competitor.abbreviatedName','competitor.id']]

#data = data['id']
matches = pd.DataFrame.from_dict(data)
#matches.to_csv('matches.csv')

# Print the status code of the response.

#https://api.overwatchleague.com/stats/matches/21211/maps/1
