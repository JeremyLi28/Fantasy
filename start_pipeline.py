from crontab import CronTab
import os

cwd = os.getcwd()

cron = CronTab(user=True)
job = cron.new(command='cd %s/fantasy-basketball-toolkit && /usr/bin/python3 data_crawler.py -t \'DK\' >> /tmp/data_crawler.err 2>&1' % cwd)
job.hour.every(12)

for item in cron:
    print(item)

cron.write()