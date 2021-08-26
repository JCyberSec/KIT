#  _  _____ _____  __        __                               
# | |/ /_ _|_   _| \ \      / / __ __ _ _ __  _ __   ___ _ __ 
# | ' / | |  | |    \ \ /\ / / '__/ _` | '_ \| '_ \ / _ \ '__|
# | . \ | |  | |     \ V  V /| | | (_| | |_) | |_) |  __/ |   
# |_|\_\___| |_|      \_/\_/ |_|  \__,_| .__/| .__/ \___|_|   
#                                      |_|   |_|              
'''
KIT Wrapper

Command line tool to enable easier use of WMC Global KIT API

For API key please contact WMC Global :: https://www.wmcglobal.com/contact

Author :: Jake 
Version :: V2.6.12.1

Change log:
	- Added recursive submission feature

''' 

# Import Table
import argparse
import json
import requests
import os
import hashlib
import errno
import re
import glob


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


# Function to access content API
def download_content(uuidInput, downloadInput, jsonInput):
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
				# If json argument print the returned JSON object to screen
				if jsonInput:
					print (result)
				else:
					# extract the content download URL
					target_url = (result['content'])
					response = requests.get("{}".format(target_url))
					if response.status_code == 200:
						# If saving to file
						if downloadInput:
							try:
								# Create the file, then write to the same file. This ensures files are not overwritten
								f = open(str(Default_Download_Location) + '/' + str(target_uuid) + '.txt', 'x')
								f = open(str(Default_Download_Location) + '/' + str(target_uuid) + '.txt', 'w')
								f.write(response.text)
								f.close()
								# OK
								print ("OK\t- Content downloaded to: {}/{}.txt".format(str(Default_Download_Location), str(target_uuid)))
							except OSError as e:
								if e.errno == errno.EEXIST:
									# Error
									print("ERROR\t- File already exists {}/{}.txt".format(str(Default_Download_Location), str(target_uuid)))
								else:
									# Error
									print("ERROR\t- Failed to write file\t -{}".format(target_uuid))
						else:
							# If download not selected, content will be printed to screen
							print (response.text)
					else:
						# Error
						print("ERROR\t- Failed to download content for {}".format(target_uuid))
						print (response.text)
			else:
				# Error
				print("ERROR\t- Failed to request content for {}".format(target_uuid))
				print (response.text)
		except Exception as e:
			# Error
			print("ERROR\t- Failed to parse {}".format(target_uuid))
			print (e)

# Function to search KIT
def search(searchInput, filterInput, numberInput, dateInput):
	headers = {'x-api-key': Env_KIT_APIKey, 'Content-Type': 'application/json'}
	data = {}
	
	# Parse filter argument
	if filterInput:
		filterItems = []
		for i in filterInput.split(','):
			filterItems.append(i.strip())

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
				if keyword in ('content', 'datetime_filter', 'filename', 'filetype', 'fullfilename', 'kit.filetype', 'kit.kitname', 'kit.md5', 'kit.sha256', 'kit.size', 'kit.ssdeep', 'kit.UUID', 'md5', 'sha256', 'size', 'size_filter', 'ssdeep', 'UUID'):
					data[keyword] = value
				else:
					# Error
					print ("ERROR\t- '{}' - This is an unknown search term. Please try again".format(keyword))
					exit()
			else:
				# Error	
				print ("ERROR\t- Invalid key:value pair")
				exit()
		except Exception as e:
			# Error
			print ("ERROR\t- Ensure search is valid with keyword:searchTerm")
			raise e

	# Generate the JSON object from the search dictionary
	data = json.dumps(data)
	
	try:
		# POST request to the endpoint
		response = requests.post(URL_Endpoint + "/search", data=data, headers=headers)
		if response.status_code == 200:
			print (response.text)
		else:
			# Error
			print("ERROR\t- Failed search")
			print (response.text)
	except Exception as e:
		# Error
		print("ERROR\t- Failed search POST")
		print(e)

# Function to prevent duplicate kit submission
# Note: There is a duplication checker on the back end, this is to save wasting submission quotas
# It is strongly recommended you keep this check before submitting kits as duplicates will not be processed
def duplicateChecker(target_zip, zipsha256):
	try:
		headers = {'x-api-key': Env_KIT_APIKey, 'Content-Type': 'application/json'}
		data = {}
		data['kit.sha256'] = zipsha256
		data = json.dumps(data)
		try:
			# POST request to the endpoint
			response = requests.post(URL_Endpoint + "/search", data=data, headers=headers)
			result = json.loads(response.text)
			if result['count']:
				# Found duplicates
				return True
			else:
				# No duplicates found
				return False
		except Exception as e:
			# Error
			print ("ERROR\t- Failed hash search")
			print (e)
	except Exception as e:
		# Error
		print ("ERROR\t- Duplicate checker error")
		print (e)

# Function to validate zip file before submission
def validateZip(target_zip, zipsha256):
	if target_zip.lower().endswith('.zip'):
		try:
			with open(target_zip, 'rb') as f:
				header_byte = f.read()[0:4].hex().lower()
				# Check header bytes comply with PKZIP archive file
				if header_byte == '504b0304':
					if duplicateChecker(target_zip, zipsha256):
						# File present in KIT already
						print ("OK\t- File present in KIT\t\t- sha256: {}\t- kit.kitname: {}".format(str(zipsha256), str(os.path.basename(target_zip[:-4]))))
						f.close()
						return False
				else:
					# Error
					print ("ERROR\t- File does not appear to be a zip file")
					f.close()
					return False

			# File passed basic local checks
			return True

		except IOError as e:
			# Error
			print ("ERROR\t- Unable to read file")
			print (e)
			return False
	else:
		# Error
		print ("ERROR\t- File not a '.zip' file\t- Filename: " + str(os.path.basename(target_zip)))

# Function to submit a kit to KIT Intel for processing
def submit(ziplocation, recursive):
	try:
		# Allow for multiple kit uploads
		for target_zip in ziplocation:
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
				submit(ziplocation, False)
			else:
				# Item is not a zip so can be processed as a file
				with open(target_zip, 'rb') as f:
					# Generate SHA256 for file
					h  = hashlib.sha256()
					b  = bytearray(128*1024)
					mv = memoryview(b)
					# Initialize variable
					zipsha256 = ""
					for n in iter(lambda : f.readinto(mv), 0):
						h.update(mv[:n])
						zipsha256 = h.hexdigest()
					# Check to ensure hash has generated
					if len(zipsha256) < 64:
						# Error
						print("ERROR\t- Not a valid zip\t- kit.kitname: {}".format(str(os.path.basename(target_zip))))
					else:
						if validateZip(target_zip, zipsha256):
							# Submit New Kit
							headers = {'x-api-key': Env_KIT_APIKey, 'Content-Type': 'application/json'}
							data = {}
							data['file_name'] = os.path.basename(target_zip)
							try:
								# POST request to the endpoint
								response = requests.post(URL_Endpoint + "/submit", headers=headers, data=json.dumps(data))
							except Exception as e:
								# Error
								print("ERROR\t- Failed request to submit")
								print (response.text)
								exit()
							# OK
							if response.status_code == 200:
								result = response.json()
								target_url = (result['url'])
								headers = {'Content-Type': 'application/binary'}
								# Save file binary data ready for upload
								f = open(target_zip, 'rb')
								data = f.read()
								f.close()
								try:
									# PUT request to the endpoint
									upload = requests.put(target_url, data=data, headers=headers)
									if upload.status_code == 200:
										# OK
										print ("SUCCESS\t- File submitted\t\t- sha256: {}\t- kit.kitname: {}".format(str(zipsha256), str(os.path.basename(target_zip[:-4]))))
									else:
										# Error
										print ("ERROR\t- Upload failed\t\t- Status code: " + str(upload.status_code))
								except Exception as e:
									# Error
									print ("ERROR\t- Failed PUT request")
									print (e)
							else:
								print ("ERROR\t- Failed POST\t- Status code: " + str(response.status_code))

							# Slow down multi-kit ingest to avoid duplicate kit overlaps
							time.sleep(2)
	except OSError as e:
		# Handle if a directory is inputted
		if e.errno == 21:
			pass
	except Exception as e:
		# Error
		print ("ERROR\t- Error in kit submission")
		print (e)



# Main Function
def main():
	## Argparse Arguments
	parser = argparse.ArgumentParser(prog ='kitintel', description="The phishing Kit Intelligence Tracker (KIT) APIs are a set of static analysis tools for investigating and comparing phishing kit content within single or multiple kits.\n It can search file hashes, search file content, retrieve content, and submit kits to KIT for cross-analysis.")
	subparsers = parser.add_subparsers(help='Commands Available', dest='command')

	# Search Parser
	# -s search, -f filter, -n number, -d date
	parser_search = subparsers.add_parser('search', help='Search KIT Intel - Search on kit names, hashes, code content, directory names')
	parser_search.add_argument('-s', '--search', help='Search term', required='True')
	parser_search.add_argument('-f', '--filter', help='Filter return keys. Split multiple keys with a comma')
	parser_search.add_argument('-n', '--number', help='Number of items to return - Default 100', default=100)
	parser_search.add_argument('-d', '--date', help='Date range to search - 24h, 30d etc. - Default 1y', default="1y")

	# Content Parser
	# -u uuid, -d download, -j json
	parser_retrieve = subparsers.add_parser('content', help='Download file content - Default behavior is to print to screen, file can also be downloaded into the current working directory')
	parser_retrieve.add_argument('-u', '--uuid', help='UUID(s) to retrieve scans for', nargs='+', required='True')
	parser_retrieve.add_argument('-d', '--download', help='Download content to file', action="store_true")
	parser_retrieve.add_argument('-j', '--json', help='Print JSON data', action="store_true")

	# Submit Parser
	# -f file
	parser_retrieve = subparsers.add_parser('submit', help='Submit a phishing kit for analysis - Submit a single file, multiple files, or a directory')
	parser_retrieve.add_argument('-f', '--file', help='Zip file(s) to submit or directory', nargs='+', required='True')
	parser_retrieve.add_argument('-r', '--recursive', help='Enable directory recursion', action="store_true")

	args = parser.parse_args()

	# Search
	if args.command == 'search':
		search(args.search, args.filter, args.number, args.date)
	# Content
	elif args.command == 'content':
		download_content(args.uuid, args.download, args.json)
	# Submit
	elif args.command == 'submit':
		submit(args.file, args.recursive)
	else:
		# Error
		parser.print_help()

if __name__ == '__main__':
	main()
