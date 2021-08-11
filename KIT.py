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
Version :: V2.3
Input :: Command line arguments
Return :: API output

Change log:
	- Public Release

''' 

# Import Table
import argparse
import json
import requests
import os

# Global Config options
Env_KIT_APIKey = os.environ['KITAPI']
Default_Download_Location = os.getcwd()
URL_Endpoint = 'https://api.phishfeed.com/KIT/v1'

## Argparse Arguments
parser = argparse.ArgumentParser(description="Wrapper for KIT Intel's API")
subparsers = parser.add_subparsers(help='commands', dest='command')

# Search Parser
parser_search = subparsers.add_parser('search', help='Search KIT Intel')
parser_search.add_argument('-s', '--search', help='Search term', required='True')
parser_search.add_argument('-f', '--filter', help='Filter return keys. Split multiple keys with a comma')
parser_search.add_argument('-n', '--number', help='Number of items to return - Default 100', default=100)
parser_search.add_argument('-d', '--date', help='Date range to search - 24h, 30d, 90d etc.', default="24h")

# Content Parser
parser_retrieve = subparsers.add_parser('content', help='Download file content')
parser_retrieve.add_argument('-u', '--uuid', help='UUID(s) to retrieve scans for', nargs='+', required='True')
parser_retrieve.add_argument('-d', '--download', help='Download content to file', action="store_true")
parser_retrieve.add_argument('-j', '--json', help='Print JSON data', action="store_true")

args = parser.parse_args()

def download_content(uuid):
	for target_uuid in uuid:
		try:
			target_uuid = target_uuid.strip(',')
			headers = {'x-api-key': Env_KIT_APIKey, 'Content-Type': 'application/json'}
			data = {}
			data['UUID'] = target_uuid
			response = requests.post(URL_Endpoint + "/content", headers=headers, data=json.dumps(data))
			result = response.json()
			if args.json:
				print (result)
			else:
				target_url = (result['content'])
				response = requests.get("{}".format(target_url))
				if args.download:
					with open(str(Default_Download_Location) + str(target_uuid[0]) + '.txt', 'wb') as f:
					    f.write(response.content)
					print("Content downloaded to: " + str(Default_Download_Location) + '/' + str(target_uuid[0]) + '.txt')
				else:
					print (response.text)
		except Exception as e:
			print("Failed to download DOM for {}".format(target_uuid[0]))
			print(e)
			pass

def search(search, filter, number, date):
	headers = {'x-api-key': Env_KIT_APIKey, 'Content-Type': 'application/json'}
	data = {}
	if args.filter:
		filterItems = []
		for i in filter.split(','):
			filterItems.append(i.strip())

		data["filter"] = filterItems
		filterData = (filterItems)

	if args.number:
		data["page_size"] = int(args.number)

	if args.date:
		date = {}
		date["gte"] = "now-" + str(args.date)
		data["datetime_filter"] = date

	search_array = args.search.replace(':', ',')
	search_array = search_array.split(',')
	try:
		for i in range(0, len(search_array),2):
			data[search_array[i].replace(' ', '')] = search_array[i+1]
	except IndexError:
		print ("Missing key value pair in search")
		exit()
	except Exception as e:
		print ("Error in search JSON")
		raise e
	data = (json.dumps(data))
	response = requests.post(URL_Endpoint + "/search", data=data, headers=headers)
	print (response.text)

def main():
	if args.command == 'search':
		search(args.search, args.filter, args.number, args.date)
	if args.command == 'content':
		download_content(args.uuid)

if __name__ == '__main__':
	main()