import os
from enum import Enum

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