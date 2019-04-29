from lineup_optimizer import DPOptimizer, IPOptimizer
from optparse import OptionParser
import os
import pandas as pd

home = './'


def fetch_cash_line():
	results_dir = home + 'data/extractor/results/slates'
	cash_line = {'date' : [], 'slate_id' : [], 'cash_avg' : [], 'gpp_avg': []}
	for file_name in os.listdir(results_dir):
		slates = pd.read_csv(results_dir + '/' + file_name)
		date = os.path.splitext(file_name)[0]
		for idx, slate in slates.iterrows():
			if slate['CashAvg'] != 0 and slate['CashAvg'] >= 100:		
				cash_line['date'].append(date)
				cash_line['slate_id'].append(int(slate['Id']))
				cash_line['cash_avg'].append(slate['CashAvg'])
				cash_line['gpp_avg'].append(slate['GPPAvg'])
	cash_line_df = pd.DataFrame.from_dict(cash_line)
	cash_line_df.set_index('date', inplace=True)
	cash_line_df.sort_index(inplace=True)
	return cash_line_df

def Experiment(top_k):
	cash_line = fetch_cash_line()
	results = {'date' : [], 'slate_id' : [], 'dkp_avg' : [], 'cash_avg': [], 'cash_above_line': [], 'gpp_avg': [], 'gpp_above_line': []}
	for index, row in cash_line.iterrows():
		date = index
		print "Running", date, int(row['slate_id'])
		# lineups = DPOptimizer('rotogrinders', date, top_k, int(row['slate_id']))
		lineups = IPOptimizer('rotogrinders', date, top_k, int(row['slate_id']))
		if not lineups:
			continue
		if not os.path.exists(home + 'data/results/%s.csv' % date):
			continue
		dk_result = pd.read_csv(home + 'data/results/%s.csv' % date, header=0, index_col=0)
		total = 0
		cash_above_line = 0
		gpp_above_line = 0
		for lineup in lineups:
			points = lineup[-2]
			salary = lineup[-1]
			lineup = lineup[:-2]
			dkp = 0
			for player in lineup:
				if player in dk_result.index.tolist():
					dkp += dk_result.loc[player]['DKP']
			if dkp >= row['cash_avg']:
				cash_above_line += 1
			if dkp >= row['gpp_avg']:
				gpp_above_line += 1
			total += dkp
		results['date'].append(date)
		results['slate_id'].append(int(row['slate_id']))
		results['dkp_avg'].append(total * 1.0 / top_k)
		results['cash_avg'].append(row['cash_avg'])
		results['cash_above_line'].append(cash_above_line * 1.0 / top_k)
		results['gpp_avg'].append(row['gpp_avg'])
		results['gpp_above_line'].append(gpp_above_line * 1.0 / top_k)
	results_df = pd.DataFrame.from_dict(results)
	results_df.set_index('date', inplace=True)
	results_df.to_csv(home + 'data/experiments/rg.csv')


if __name__ == '__main__':
	parser = OptionParser()
	parser.add_option("-k", "--top_k", dest="top_k", default=10)
	(options, args) = parser.parse_args()
	Experiment(int(options.top_k))