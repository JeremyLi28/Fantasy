from bs4 import BeautifulSoup
import urllib
import sys
import json

home = './'

def Crawl(year, month, day):
	url = 'https://rotogrinders.com/projected-stats/nba-player?site=draftkings&sport=nba&date=%s-%s-%s' % (year, month, day)
	r = urllib.urlopen(url).read()
	soup = BeautifulSoup(r, features="html.parser")
	# Have 2 scripts tag, we use the 2nd for now, the usage of first need to be further investigated, related to vegas money line
	script_tags = soup.find('section', {'class' : 'pag bdy'}).findAll('script')
	player_data = script_tags[2].text.split('\n')[2].strip().split('=')[1].strip()[:-1]
	slate_data = script_tags[1].text.split('\n')[4].strip().split('slates: ')[1][:-1]
	schedule_data = script_tags[1].text.split('\n')[5].strip().split('schedules: ')[1][:-1]
	player_json_data = json.loads(player_data)
	slate_json_data = json.loads(slate_data)
	with open(home + 'data/crawler/rotogrinders/slates/%s-%s-%s.json' % (year, month, day), 'w') as slate_json_file:
		json.dump(slate_json_data, slate_json_file)
	with open(home + 'data/crawler/rotogrinders/projections/%s-%s-%s.json' % (year, month, day), 'w') as player_json_file:
		json.dump(player_json_data, player_json_file)
	print "fetch_roto_grainders_proj for %s-%s-%s" % (year, month, day)


if __name__ == "__main__":
	year = sys.argv[1]
	month = sys.argv[2]
	day = sys.argv[3]
	Crawl(year, month, day)