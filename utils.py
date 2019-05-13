import os

home = './'
raw_data_path = home + 'data/extractor'
extracted_data_path = home + 'data/extractor'

def CreateDirectoryIfNotExist(path):
	if not os.path.exists(path):
		os.makedirs(path)

def GetRawDataPath():
	return raw_data_path

def GetExtractedDataPath():
	return extracted_data_path