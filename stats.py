import pandas as pd
import requests


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
statsMe = stats.loc[filt]

stats.to_csv(r'C:\Users\rjohns17\Desktop\Data Science\Python\OWL\stats.csv')
