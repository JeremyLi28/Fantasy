from setuptools import setup

setup(name='jiayin',
      version='0.1',
      description='Fantasy basketball toolkits',
      url='https://github.com/JeremyLi28/Fantasy',
      author='JeremyLi',
      author_email='jeremyliisagoodman@gmail.com',
      license='MIT',
      packages=['jiayin'],
      install_requires=[
          'bs4',
          'urllib',
          'sys',
          'json',
          'optparse',
          'datetime',
          'nba_api',
          'time',
          'os',
          'draft_kings_client',
          'pandas',
          'urllib2',
          'pytz'
      ],
      zip_safe=False)