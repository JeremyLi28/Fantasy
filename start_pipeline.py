from crontab import CronTab

cron = CronTab(user=True)
job = cron.new(command='python3 $(pwd)/data_crawler.py -t \'DK\' ~/install.log 2>&1')
job.hour.every(12)
cron.write()