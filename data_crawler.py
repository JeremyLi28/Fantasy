from bs4 import BeautifulSoup
import urllib
import sys
import json

home = './'

def fetch_roto_grinders_proj(year, month, day):
	url = 'https://rotogrinders.com/projected-stats/nba-player?site=draftkings&sport=nba&date=%s-%s-%s' % (year, month, day)
	r = urllib.urlopen(url).read()
	soup = BeautifulSoup(r, features="html.parser")
	# Have 2 scripts tag, we use the 2nd for now, the usage of first need to be further investigated, related to vegas money line
	script_tags = soup.find('section', {'class' : 'pag bdy'}).findAll('script')
	raw_data = script_tags[2].text.split('\n')[2].strip().split('=')[1].strip()[:-1]
	json_data = json.loads(raw_data)
	with open(home + 'data/raw/rotogrinders/projections/%s-%s-%s.json' % (year, month, day), 'w') as json_file:
		json.dump(json_data, json_file)
	print "fetch_roto_grainders_proj for %s-%s-%s" % (year, month, day)


if __name__ == "__main__":
	year = sys.argv[1]
	month = sys.argv[2]
	day = sys.argv[3]
	fetch_roto_grinders_proj(year, month, day)