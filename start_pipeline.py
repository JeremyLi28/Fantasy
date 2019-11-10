from crontab import CronTab
import os

cwd = os.getcwd()

cron = CronTab(user=True)
job = cron.new(command='python3 %s/fantasy-basketball-toolkit/data_crawler.py -t \'DK\' ~/install.log 2>&1' % cwd)
job.hour.every(12)

for item in cron:
    print item

cron.write()