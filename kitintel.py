#  _  _____ _____  __        __                               
# | |/ /_ _|_   _| \ \      / / __ __ _ _ __  _ __   ___ _ __ 
# | ' / | |  | |    \ \ /\ / / '__/ _` | '_ \| '_ \ / _ \ '__|
# | . \ | |  | |     \ V  V /| | | (_| | |_) | |_) |  __/ |   
# |_|\_\___| |_|      \_/\_/ |_|  \__,_| .__/| .__/ \___|_|   
#                                      |_|   |_|              
#
'''
KIT Wrapper

Command line tool to enable easier use of WMC Global KIT API

For API key please contact WMC Global :: https://www.wmcglobal.com/contact

Author :: Jake 


Change log:
	- Fixed bug in submission loops
''' 
__version__ = '2.7.13'


# Import Table
from copy import deepcopy
from tqdm import tqdm
from tqdm.utils import CallbackIOWrapper
from typing import Dict, Any, List
import argparse
import errno
import feedparser
import glob
import hashlib
import json
import os
import pandas
import pathlib
import re
import requests
import shutil
import time
import traceback
import uuid


## Global Config options
# Content download location
Default_Download_Location = os.getcwd()

# KIT API environment variable
try:
	Env_KIT_APIKey = os.environ['KITAPI']
except Exception as e:
	# Error
	print ("ERROR\t- KITAPI key error - Ensure an API key has been added to the environment variables")
	exit()

# KIT URL base endpoint
URL_Endpoint = 'https://api.phishfeed.com/KIT/v1'

VAILD_KEYWORDS = {
	"datetime": "datetime",
	"content": "content",
	"file.filename": "file.filename",
	"file.filetype": "file.filetype",
	"file.md5": "file.md5",
	"file.sha256": "file.sha256",
	"file.size": "file.size",
	"file.ssdeep": "file.ssdeep",
	"file.UUID": "file.UUID",
	"filename": "file.filename",
	"filetype": "file.filetype",
	"fullfilename": "fullfilename",
	"kit.filetype": "kit.filetype",
	"kit.kitname": "kit.kitname",
	"kit.md5": "kit.md5",
	"kit.sha256": "kit.sha256",
	"kit.size": "kit.size",
	"kit.ssdeep": "kit.ssdeep",
	"kit.UUID": "kit.UUID",
	"md5": "file.md5",
	"scroll_id": "scroll_id",
	"sha256": "file.sha256",
	"size": "file.size",
	"size_filter": "size_filter",
	"ssdeep": "file.ssdeep",
	"UUID": "UUID",
}

def saveToFile(content, uuid, filetype, debug):
	try:
		# Create the file, then write to the same file. This ensures files are not overwritten
		f = open(str(Default_Download_Location) + '/' + str(uuid) + '.' + str(filetype), 'x')
		f = open(str(Default_Download_Location) + '/' + str(uuid) + '.' + str(filetype), 'w')
		f.write(content)
		f.close()
		# OK
		print ("OK\t- Content downloaded to: {}/{}.{}".format(str(Default_Download_Location), str(uuid), str(filetype)))
	except OSError as e:
		if e.errno == errno.EEXIST:
			# Error
			print("ERROR\t- File already exists {}/{}.txt".format(str(Default_Download_Location), str(uuid)))
			if debug:
				traceback.print_exc()
		else:
			# Error
			print("ERROR\t- Failed to write file\t -{}".format(uuid))
			if debug:
				traceback.print_exc()

# Function to access content API
def content(uuidInput, downloadInput, debug):
	# Allow for multiple UUIDs
	for target_uuid in uuidInput:
		try:
			target_uuid = target_uuid.strip(',')
			headers = {'x-api-key': Env_KIT_APIKey, 'Content-Type': 'application/json'}
			data = {}
			data['UUID'] = target_uuid
			# POST request to the endpoint
			response = requests.post(URL_Endpoint + "/content", headers=headers, data=json.dumps(data))
			if response.status_code == 200:
				result = response.json()
				# extract the content download URL
				target_url = (result['download_url'])
				response = requests.get("{}".format(target_url))
				if response.status_code == 200:
					# If saving to file
					if downloadInput:
						saveToFile(response.text, target_uuid, 'txt', debug)
						exit()
					else:
						# If download not selected, content will be printed to screen
						print (response.text)
				else:
					# Error
					print("ERROR\t- Failed to download content for {}".format(target_uuid))
					if debug:
						traceback.print_exc()
						print (response.text)
			elif response.status_code == 403:
				print ("ERROR\t- Forbidden")
				if debug:
					traceback.print_exc()
			else:
				# Error
				print("ERROR\t- Failed to request content for {}".format(target_uuid))
				if debug:
					traceback.print_exc()
					print (response.text)
		except Exception as e:
			# Error
			print("ERROR\t- Failed to parse {}".format(target_uuid))
			if debug:
				traceback.print_exc()
				print (e)

def cross_join(left, right):
	new_rows = [] if right else left
	for left_row in left:
		for right_row in right:
			temp_row = deepcopy(left_row)
			for key, value in right_row.items():
				temp_row[key] = value
			new_rows.append(deepcopy(temp_row))
	return new_rows


def flatten_list(data):
	for elem in data:
		if isinstance(elem, list):
			yield from flatten_list(elem)
		else:
			yield elem


def json_to_dataframe(data_in):
	def flatten_json(data, prev_heading=''):
		if isinstance(data, dict):
			rows = [{}]
			for key, value in data.items():
				rows = cross_join(rows, flatten_json(value, prev_heading + '.' + key))
		elif isinstance(data, list):
			rows = []
			for i in range(len(data)):
				[rows.append(elem) for elem in flatten_list(flatten_json(data[i], prev_heading))]
		else:
			rows = [{prev_heading[1:]: data}]
		return rows

	return pandas.DataFrame(flatten_json(data_in))


def recursive_get(value: Dict[str, Any], path: List[str], default: Any = None) -> Any:
	current_point = value
	for key in path:
		try:
			current_point = current_point[key]
		except KeyError:
			return default
	return current_point


# Function to search KIT
def search(searchInput, filterInput, numberInput, dateInput, uniqueInput, formatInput, downloadInput, debug):
	headers = {'x-api-key': Env_KIT_APIKey, 'Content-Type': 'application/json'}
	data = {}
	
	# Parse filter argument
	if filterInput:
		filterItems = []
		for keyword in filterInput.split(','):
			keyword = keyword.strip()
			if keyword in VAILD_KEYWORDS.keys():
				keyword = VAILD_KEYWORDS[keyword]
				filterItems.append(keyword)
			else:
				# Error
				print ("ERROR\t- '{}' - Unknown filter term. Please try again".format(keyword))
				if debug:
					traceback.print_exc()
				exit()

		data["filter"] = filterItems
		filterData = (filterItems)

	# Parse number argument
	if numberInput:
		data["page_size"] = int(numberInput)

	# Parse date argument
	if dateInput:
		date = {}
		date["gte"] = "now-" + str(dateInput)
		data["datetime_filter"] = date

	# Split search parameters
	search_array = searchInput.split(',')

	# Regex pattern to split keyword and search variable
	# Fine first occournace of : and then capture the rest of the string
	pattern = r"([^:]*)(.*)"

	# Loop through the search input
	for i in range(len(search_array)):
		try:
			# Extract the regex results
			matchObj = re.search(pattern, search_array[i])
			# Check there are hits from the regex
			if matchObj:
				# Strip away a space in the keyword
				keyword = str(matchObj.group(1)).replace(' ', '')
				# Strip char 1 from the value which will always be a ':' due to the regex
				value = str(matchObj.group(2)[1:])
				# Check to ensure the keyword is able to be searched
				if keyword in VAILD_KEYWORDS.keys():
					keyword = VAILD_KEYWORDS[keyword]
					data[keyword] = value
				else:
					# Error
					print ("ERROR\t- '{}' - Unknown search term. Please try again".format(keyword))
					if debug:
						traceback.print_exc()
					exit()
			else:
				# Error	
				print ("ERROR\t- Invalid key:value pair")
				if debug:
					traceback.print_exc()
				exit()
		except Exception as e:
			# Error
			print ("ERROR\t- Ensure search is valid with keyword:search_term")
			if debug:
				traceback.print_exc()

	# Generate the JSON object from the search dictionary
	data = json.dumps(data)
	
	try:
		# POST request to the endpoint
		response = requests.post(URL_Endpoint + "/search", data=data, headers=headers)
	except Exception as e:
		# Error
		print("ERROR\t- Failed search POST")
		if debug:
			traceback.print_exc()

	if response.status_code == 200:
		parsed = json.loads(response.text)
		# Parse unique argument
		if uniqueInput:
			keyword = uniqueInput.strip()
			if keyword in VAILD_KEYWORDS.keys():
				keyword = VAILD_KEYWORDS[keyword]
				uniqueItem = VAILD_KEYWORDS[keyword].split('.')
				parsed["results"] = list({ recursive_get(each,uniqueItem) : each for each in parsed["results"] }.values())
				parsed["unique_count"] = len(parsed["results"])
			else:
				# Error
				print ("ERROR\t- '{}' - Unknown unique term. Please try again".format(keyword))
				if debug:
					traceback.print_exc()
				exit()
		if formatInput == 'json':
			content = json.dumps(parsed, indent=4, sort_keys=False)
			if downloadInput:
				target_uuid = uuid.uuid4()
				saveToFile(content, target_uuid, 'json', debug)
			else:
				print(content)
		elif formatInput == 'csv':
			df = json_to_dataframe(parsed)
			content = df.to_csv()
			if downloadInput:
				target_uuid = uuid.uuid4()
				saveToFile(content, target_uuid, 'csv', debug)
			else:
				print(content)
		else:
			content = json.dumps(parsed)
			if downloadInput:
				target_uuid = uuid.uuid4()
				saveToFile(content, target_uuid, 'json', debug)
			else:
				print (content)
	elif response.status_code == 403:
		print ("ERROR\t- Forbidden")
		if debug:
			traceback.print_exc()
	else:
		# Error
		print("ERROR\t- Failed search")
		if debug:
			traceback.print_exc()
			print (response.text)

# Function to validate zip file before submission
def validateZip(target_zip, zipsha256, debug):
	if target_zip.lower().endswith('.zip'):
		try:
			with open(target_zip, 'rb') as f:
				header_byte = f.read()[0:4].hex().lower()
				# Check header bytes comply with PKZIP archive file
				if header_byte == '504b0304':
					f.close()
					if debug:
						print ("Passed zip validation")
					return True 
				else:
					# Error
					print ("ERROR#1\t- File not a '.zip' file\t\t\t- Filename: {}".format(os.path.basename(target_zip)))
					if debug:
						print ("Failed zip validation")
						traceback.print_exc()
					f.close()
					return False
		except IOError as e:
			# Error
			print ("ERROR\t- Unable to read file\t\t\t- Filename: {}".format(os.path.basename(target_zip)))
			if debug:
				traceback.print_exc()
				print (e)
			return False
	else:
		# Error
		print ("ERROR#2\t- File not a '.zip' file\t\t\t- Filename: {}".format(os.path.basename(target_zip)))
		if debug:
			traceback.print_exc()
		return False

# Function to prevent duplicate kit submission
# Note: There is a duplication checker on the back end, this is to save wasting submission quotas
# It is strongly recommended you keep this check before submitting kits as duplicates will not be processed
def duplicateChecker(target_zip, zipsha256, debug):
	headers = {'x-api-key': Env_KIT_APIKey, 'Content-Type': 'application/json'}
	data = {
		"filter": ["kit.UUID"],
		"page_size": 1
	}
	data['kit.sha256'] = zipsha256
	try:
		# Slow down multi-kit ingest to avoid duplicate kit overlaps
		time.sleep(1)
		# POST request to the endpoint
		if debug:
			print ("Making search POST - " + str(time.time()))
			print (data)
		response = requests.post(URL_Endpoint + "/search", data=json.dumps(data), headers=headers)
		if debug:
			print ("Finished  search POST - " + str(time.time()))
		if response.status_code == 403:
			print ("Uploader only restrictions apply - ", end='')
			return True
		if response.status_code == 200 and response.json()["total_count"] is None:
			# No duplicates found
			return True
		else:
			# Found duplicates
			print ("OK\t- Kit already present in KITIntel\t\t- sha256: {}\t- kit.kitname: {}".format(str(zipsha256), str(os.path.basename(target_zip[:-4]))))
			return False
	except Exception as e:
		# Error
		print ("ERROR\t- Failed duplicate checking POST request")
		if debug:
			print (e)
			traceback.print_exc()
		# If search fails upload the kit anyway
		return True

def submitPost(zipfile, debug):
	file_size = os.stat(zipfile).st_size

	headers = {'x-api-key': Env_KIT_APIKey, 'Content-Type': 'application/json'}
	data = {
		"file_name": os.path.basename(zipfile)
	}

	res = requests.post(URL_Endpoint + "/submit", headers=headers, data=json.dumps(data))
	if debug:
		print (res.json())
	if res.status_code == 200:
		presigned_headers = {'Content-Type': 'application/binary'}
		presigned_url = res.json()['upload_url']
		with open(zipfile, 'rb') as f:
			try:
				with tqdm(total=file_size, unit="B", unit_scale=True, unit_divisor=1024) as t:
					wrapped_file = CallbackIOWrapper(t.update, f, "read")
					upload = requests.put(
						presigned_url, headers=presigned_headers, data=wrapped_file)
					if upload.status_code == 200:
						return True
					if upload.status_code != 200:
						print("ERROR\t- Upload Failed at state 1")
						if debug:
							print (upload.status_code)
							print (upload.text)
			except Exception as e:
				print("ERROR\t- Upload Failed at state 2")
				if debug:
					print(e)
					traceback.print_exc()
	return False


def submit(ziplocation, recursive, debug):
	if debug:
		print ("-------------------------------------------------------------------------------------")
	try:
		#Allow for multiple kit uploads
		for target_zip in ziplocation:
			if debug:
				print ("Running: {}".format(target_zip))
			# Check if current item is a directory
			if os.path.isdir(target_zip):
				ziplocation = []
				# If recursive value is set
				if recursive:
					# Create a list of all files in all directories which end in .zip
					ziplocation = glob.glob(target_zip + '/**/*.zip', recursive=True)
				else:
					# Create a list of all files in current directory which end in .zip
					ziplocation = glob.glob(target_zip + '/*.zip', recursive=False)
				if debug:
					print (ziplocation)
				submit(ziplocation, False, debug)
			else:
				if debug:
					print ("File Entered")
				# Item is not a dir so can be processed as a file
				with open(target_zip, 'rb') as f:
					# Generate SHA256 for file
					h  = hashlib.sha256()
					b  = bytearray(128*1024)
					mv = memoryview(b)
					# Initialize variable
					# This is a 0 byte file hash - Sha256 fails with a 0 byte file.
					zipsha256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
					for n in iter(lambda : f.readinto(mv), 0):
						h.update(mv[:n])
						zipsha256 = h.hexdigest()
					# Check to ensure hash has generated
					if len(zipsha256) < 64:
						# Error
						print("ERROR\t- Unable to generate hash\t\t\t- kit.kitname: {}".format(str(os.path.basename(target_zip))))
						traceback.print_exc()
					else:
						try:
							while True:
								submit = True
								if debug:
									print ("Validation Check - start")
								upload = validateZip(target_zip, zipsha256, debug)
								if debug:
									print ("Validation Check - end")
								if not upload:
									if debug:
										print ("File is not a valid zip - no upload required")
									submit = False
									break
								if debug:
									print ("Duplicate Check - start")
								upload = duplicateChecker(target_zip, zipsha256, debug)
								if debug:
									print ("Duplicate Check - end")
								if not upload:
									if debug:
										print ("File is Duplicate - no upload required")
									submit = False
									break
								# if not duplicate:
								if debug:
									print("New kit - starting upload {} to S3...".format(str(os.path.basename(target_zip))))
								counter = 0
								if submit:
									if debug:
										print ("Submission start")
									success = submitPost(target_zip, debug)
									if debug:
										print ("Submission end")
									if success:
										print ("SUCCESS\t- File submitted\t\t\t\t- sha256: {}\t- kit.kitname: {}".format(str(zipsha256), str(os.path.basename(target_zip[:-4]))))
										break
									if counter > 10:
										print("ERROR\t- Attempted upload 10 times and failed\t\t- kit.kitname: {}".format(str(os.path.basename(target_zip[:-4]))))
										break
									counter = counter + 1
						except Exception as e:
							if debug:
								print (e)
								traceback.print_exc()
	except OSError as e:
		# Handle if a directory is inputted
		if e.errno == 21:
			pass
	except Exception as e:
		# Error
		print ("ERROR\t- Error in kit submission")
		if debug:
			traceback.print_exc()
			print (e)


# Main Function
def main():
	## Argparse Arguments
	parser = argparse.ArgumentParser(prog ='kitintel',
									 description="The phishing Kit Intelligence Tracker (KIT) APIs are a set of static analysis tools for investigating and comparing phishing kit content within single or multiple kits.\n It can search file hashes, search file content, retrieve content, and submit kits to KIT for cross-analysis.",
									 epilog="\n For more information or assistance with KIT - Please speak to your account manager or contact WMC Global")
	subparsers = parser.add_subparsers(help='Commands Available', dest='command')

	# Search Parser
	parser_search = subparsers.add_parser('search', help='Search KIT Intel - Search on kit names, hashes, code content, directory names')
	parser_search.add_argument('-s', '--search', help='Search term', required='True')
	parser_search.add_argument('-f', '--filter', help='Filter return keys. Split multiple keys with a comma')
	parser_search.add_argument('-n', '--number', help='Number of items to return - Default 100', default=100)
	parser_search.add_argument('-d', '--date', help='Relative date to search - Examples: 3h, 6d, 9w - Default 1y', default="1y")
	parser_search.add_argument('-u', '--unique', help='Print only unique values when given a key')
	parser_search.add_argument('--format', choices=['json', 'csv'], help='Change output format - Default unformatted json', default='None')
	parser_search.add_argument('--download', help='Download output to file', action="store_true")
	parser_search.add_argument('--debug', help='Verbose output for debugging only', action="store_true")

	# Content Parser
	parser_content = subparsers.add_parser('content', help='Download file content - Default behavior is to print to screen, file can also be downloaded into the current working directory')
	parser_content.add_argument('-u', '--uuid', help='UUID(s) to retrieve scans for', nargs='+', required='True')
	parser_content.add_argument('-d', '--download', help='Download content to file', action="store_true")
	parser_content.add_argument('--debug', help='Verbose output for debugging only', action="store_true")

	# Submit Parser
	parser_submit = subparsers.add_parser('submit', help='Submit a phishing kit for analysis - Submit a single file, multiple files, or a directory')
	parser_submit.add_argument('-f', '--file', help='Zip file(s) to submit or directory', nargs='+', required='True')
	parser_submit.add_argument('-r', '--recursive', help='Enable directory recursion', action="store_true")
	parser_submit.add_argument('--debug', help='Verbose output for debugging only', action="store_true")

	parser.add_argument('-v', '--version', action='version', version='%(prog)s-{version}'.format(version=__version__))

	args = parser.parse_args()

	# Search
	if args.command == 'search':
		search(args.search, args.filter, args.number, args.date, args.unique, args.format, args.download, args.debug)
	# Content
	elif args.command == 'content':
		content(args.uuid, args.download, args.debug)
	# Submit
	elif args.command == 'submit':
		submit(args.file, args.recursive, args.debug)
	else:
		# Error
		parser.print_help()

def versionCheck():
	try:
		latest_ver = feedparser.parse('https://pypi.org/rss/project/kitintel/releases.xml')['entries'][0]['title']
		if latest_ver < __version__:
			print ("\n\nWARNING: You are using kitintel version {}; however, version {} is available. You should consider upgrading by running:".format(__version__, latest_ver))
			print ("pip3 install kitintel --upgrade")

	except Exception as e:
		# Error
		print (e)

if __name__ == '__main__':
	main()
	versionCheck()