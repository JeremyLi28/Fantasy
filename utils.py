import os
from enum import Enum
from datetime import datetime
import pytz

home = './'
raw_data_path = home + 'data/extractor'
extracted_data_path = home + 'data/extractor'

class SlateType(Enum):
    CLASSIC = "CLASSIC"
    TIERS = "TIERS"
    SHOWDOWN = "SHOWDOWN"

DRAFTKINGS_SLATE_TYPE = {70: SlateType.CLASSIC.name, 73: SlateType.TIERS.name, 81: SlateType.SHOWDOWN.name}

def CreateDirectoryIfNotExist(path):
	if not os.path.exists(path):
		os.makedirs(path)

def GetRawDataPath():
	return raw_data_path

def GetExtractedDataPath():
	return extracted_data_path

def ConvertTimestampStringToLocalDatetime(timestamp_string):
	''' Convert timestamp string to datetime object in local timezon.'''
	''' Input: timestamp_string (2019-11-01T23:00:00.0000000Z)
		Output: datetime object in American/Los Angles timezone
	'''
	return datetime.strptime(timestamp_string[:-9],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=pytz.utc).astimezone(pytz.timezone('America/Los_Angeles'))