# :mag: KIT Intel Wrapper 


The phishing Kit Intelligence Tracker (KIT) APIs are a set of static analysis tools for investigating and comparing phishing kit content within single or multiple kits. It can search file hashes, search file content, retrieve content, and submit kits to KIT for cross-analysis.

A phishing kit is a package of software tools, often in the form of a compressed file, that makes it easier to launch phishing attacks and exploits. Phishing kits allow attackers to deploy and redeploy phishing infrastructure before and during an attack rapidly. There are various types of phishing kits, from those targeting consumers, employees, financial institutions, marketplaces, and many more. Kits can deploy malware, collect credentials, detect bots, block IP ranges, generate QR codes, and update dynamically. Use KIT to ingestigate and compare phishing kits, discover evidence about attackers and kit publishers, identify evasion techniques, and find new exploits.

# Contents
:one:   - [Features](#features) <br/>
:two:   - [Set API as environment variable](#apikey) <br/>
:three: - [Flags](#flags) <br/>
:four:  - [Technical Usage](#technical) <br/>
:five:  - [Sample Usage](#sample) <br/>



## Features <a name="features"></a>
:red_circle: Search KIT Intel <br/>
:yellow_circle: Download content <br/>
:large_blue_circle: Define time parameters <br/>
:green_circle: Define result count <br/>
:orange_circle: Automatically extract fields <br/>

## Set API as environment variable <a name="apikey"></a>

This script uses Environment Variables to get your API key.

:desktop_computer: Windows (cmd)
```
$ setx KITAPI "APIKEY"
```

:penguin: Unix  
```
$ export KITAPI="APIKEY"
```

## Flags <a name="flags"></a>
:red_circle: Search
  - -s / --search :: The search term
  - -f / --filter :: Filter return keys. Split multiple keys with a comma
  - -n / --number :: Number of items to return (Default=100)
  - -d / --date :: Date range to search - 24h, 30d, 90d etc. (Default=24h)

:yellow_circle: Content
  - -u / --uuid :: UUID(s) to retrieve content for - Can submit multiple either comma or space separated 
  - -d / --download :: Download content to file
  - -j / --json :: Print return JSON 

:large_blue_circle: Submit
  - -f / --file :: Submit a phishing kit for analysis. Submit a single file, multiple files, or a directory

# Technical Usage <a name="technical"></a>
```
usage: KIT.py [-h] {search,content,submit} ...

Wrapper for KIT Intel's API

positional arguments:
  {search,content,submit}
                        commands
    search              Search KIT Intel
    content             Download file content
    submit              Submit a phishing kit for analysis. Submit a single file, multiple files, or a directory

optional arguments:
  -h, --help            show this help message and exit
```
---
```
usage: kitintel search [-h] -s SEARCH [-f FILTER] [-n NUMBER] [-d DATE] [--format {json,csv}] [--download]

optional arguments:
  -h, --help            show this help message and exit
  -s SEARCH, --search SEARCH
                        Search term
  -f FILTER, --filter FILTER
                        Filter return keys. Split multiple keys with a comma
  -n NUMBER, --number NUMBER
                        Number of items to return - Default 100
  -d DATE, --date DATE  Relative date to search - Examples: 3h, 6d, 9w - Default 1y
  --format {json,csv}   Change output format - Default unformatted json
  --download            Download output to file
```
---
```
usage: mainV2.3.py content [-h] -u UUID [UUID ...] [-d] [-j]

optional arguments:
  -h, --help            show this help message and exit
  -u UUID [UUID ...], --uuid UUID [UUID ...]
                        UUID(s) to retrieve scans for
  -d, --download        Download content to file
  -j, --json            Print JSON data
```
---
```
usage: kitintel submit [-h] -f FILE [FILE ...] [-r]

optional arguments:
  -h, --help            show this help message and exit
  -f FILE [FILE ...], --file FILE [FILE ...]
                        Zip file(s) to submit or directory
  -r, --recursive       Enable directory recursion
```
---
# Sample Usage <a name="sample"></a>
```
$ python3 KIT.py search -s 'content:google, filetype: php' -d 3d -f 'kit.UUID, filename' -n 3
$ python3 KIT.py content -u 2e517c8f-9375-4f55-a503-ca5bbd4d4a5b
$ python3 KIT.py submit -f ./16shop_V8.1_CRACKED.zip
```
