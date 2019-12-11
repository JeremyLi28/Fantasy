from crontab import CronTab
import os
from datetime import timedelta, date, datetime

today = datetime.today().strftime('%Y-%m-%d')
yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

cwd = os.getcwd()

cron = CronTab(user=True)
cron.remove_all()
dk_crawler_job = cron.new(command='cd %s/fantasy-basketball-toolkit && /usr/bin/python3 data_crawler.py -t \'DK\' >> /tmp/data_crawler.err 2>&1' % cwd)
dk_crawler_job.every(12).hours()

dk_result_crawler_job = cron.new(command='cd %s/fantasy-basketball-toolkit && /usr/bin/python3 data_crawler.py -t \'ML\' -d \'%s\' >> /tmp/data_crawler.err 2>&1' % (cwd, yesterday))
dk_result_crawler_job.every(12).hours()

dk_result_extractor_job = cron.new(command='cd %s/fantasy-basketball-toolkit && /usr/bin/python3 data_extractor.py -t \'ML\' -d \'%s\' >> /tmp/data_extractor.err 2>&1' % (cwd, yesterday))
dk_result_extractor_job.minute.on(5)
dk_result_extractor_job.hour.every(12)

for item in cron:
    print(item)

cron.write()