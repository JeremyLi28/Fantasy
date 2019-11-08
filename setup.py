from setuptools import setup

setup(name='fantasy-basketball-toolkit',
      version='0.1',
      description='Fantasy basketball toolkits',
      url='https://github.com/JeremyLi28/Fantasy',
      author='JeremyLi',
      author_email='jeremyliisagoodman@gmail.com',
      license='MIT',
      packages=['fantasy-basketball-toolkit'],
      install_requires=[
          'bs4',
          'datetime',
          'nba_api',
          'draft-kings',
          'pandas',
          'pytz'
      ],
      zip_safe=False)