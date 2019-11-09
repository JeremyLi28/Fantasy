from crontab import CronTab

cron = CronTab()
job = cron.new(command='python3 ../data_crawler.py -t \'DK\' ~/install.log 2>&1')
job.minute.every(1)

cron.write()