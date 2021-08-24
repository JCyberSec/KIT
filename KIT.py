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
Version :: V2.5.1

Change log:
	- Added comments
	- Better error handling
	- Updated submission API to prod

''' 

# Import Table
import argparse
import json
import requests
import os
import hashlib
import errno

## Global Config options
# Content download location
Default_Download_Location = os.getcwd()
# KIT API environment variable
Env_KIT_APIKey = os.environ['KITAPI']

# KIT URL base endpoint
URL_Endpoint = 'https://api.phishfeed.com/KIT/v1'

## Argparse Arguments
parser = argparse.ArgumentParser(description="Wrapper for KIT Intel's API")
subparsers = parser.add_subparsers(help='commands', dest='command')

# Search Parser
# -s search, -f filter, -n number, -d date
parser_search = subparsers.add_parser('search', help='Search KIT Intel')
parser_search.add_argument('-s', '--search', help='Search term', required='True')
parser_search.add_argument('-f', '--filter', help='Filter return keys. Split multiple keys with a comma')
parser_search.add_argument('-n', '--number', help='Number of items to return - Default 100', default=100)
parser_search.add_argument('-d', '--date', help='Date range to search - 24h, 30d etc. - Default 1y', default="1y")

# Content Parser
# -u uuid, -d download, -j json
parser_retrieve = subparsers.add_parser('content', help='Download file content')
parser_retrieve.add_argument('-u', '--uuid', help='UUID(s) to retrieve scans for', nargs='+', required='True')
parser_retrieve.add_argument('-d', '--download', help='Download content to file', action="store_true")
parser_retrieve.add_argument('-j', '--json', help='Print JSON data', action="store_true")

# Submit Parser
# -f file
parser_retrieve = subparsers.add_parser('submit', help='Submit a phishing kit for analysis. Submit a single file, multiple files, or a directory')
parser_retrieve.add_argument('-f', '--file', help='Zip file(s) to submit', nargs='+', required='True')


args = parser.parse_args()

# Function to access content API
def download_content(uuid):
	# Allow for multiple UUIDs
	for target_uuid in uuid:
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
				if args.json:
					print (result)
				else:
					# extract the content download URL
					target_url = (result['content'])
					response = requests.get("{}".format(target_url))
					if response.status_code == 200:
						# If saving to file
						if args.download:
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

# Function to search KIT
def search(search, filter, number, date):
	headers = {'x-api-key': Env_KIT_APIKey, 'Content-Type': 'application/json'}
	data = {}
	
	# Parse filter argument
	if args.filter:
		filterItems = []
		for i in filter.split(','):
			filterItems.append(i.strip())

		data["filter"] = filterItems
		filterData = (filterItems)
	
	# Parse number argument
	if args.number:
		data["page_size"] = int(args.number)

	# Parse date argument
	if args.date:
		date = {}
		date["gte"] = "now-" + str(args.date)
		data["datetime_filter"] = date

	# Split search parameters
	search_array = args.search.replace(':', ',')
	search_array = search_array.split(',')

	try:
		# Iterate though key value search items
		for i in range(0, len(search_array),2):
			data[search_array[i].replace(' ', '')] = search_array[i+1]
	except IndexError:
		print ("ERROR\t- Missing key value pair in search")
		exit()
	except Exception as e:
		print ("ERROR\t- Error in search JSON")
		print (e)

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
def submit(ziplocation):
	try:
		# Allow for multiple kit uploads
		for target_zip in ziplocation:
			with open(target_zip, 'rb') as f:
				# Generate SHA256 for file
				h  = hashlib.sha256()
				b  = bytearray(128*1024)
				mv = memoryview(b)
				for n in iter(lambda : f.readinto(mv), 0):
					h.update(mv[:n])
					zipsha256 = h.hexdigest()
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
	except OSError as e:
		# Handle if a directory is inputted
		if e.errno == 21:
			ziplocation = []
			for file in os.listdir(target_zip):
				if file.lower().endswith('.zip'):
					ziplocation.append(file)
			# Scan zip files in directory
			submit(ziplocation)
	except Exception as e:
		print (e)



# Main Function
def main():
	# Search
	if args.command == 'search':
		search(args.search, args.filter, args.number, args.date)
	# Content
	if args.command == 'content':
		download_content(args.uuid)
	# Submit
	if args.command == 'submit':
		submit(args.file)

if __name__ == '__main__':
	main()
