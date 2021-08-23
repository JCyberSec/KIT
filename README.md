# KIT Intel Wrapper


The phishing Kit Intelligence Tracker (KIT) APIs are a set of static analysis tools for investigating and comparing phishing kit content within single or multiple kits. It can search file hashes, search file content, retrieve content, and submit kits to KIT for cross-analysis.

A phishing kit is a package of software tools, often in the form of a compressed file, that makes it easier to launch phishing attacks and exploits. Phishing kits allow attackers to deploy and redeploy phishing infrastructure before and during an attack rapidly. There are various types of phishing kits, from those targeting consumers, employees, financial institutions, marketplaces, and many more. Kits can deploy malware, collect credentials, detect bots, block IP ranges, generate QR codes, and update dynamically. Use KIT to ingestigate and compare phishing kits, discover evidence about attackers and kit publishers, identify evasion techniques, and find new exploits.
   
## Features
- Search KIT Intel
- Download content
- Define time parameters
- Define result count
- Automatically extract fields

### Set API as environment variable

This script uses Environment Variables to get your API key.

Windows (cmd)
```
$ setx KITAPI "APIKEY"
```

Unix  
```
$ export KITAPI="APIKEY"
```

## Flags
- Search
  - -s / --search :: The search term  [<b>required</b>]
  - -f / --filter :: Filter return keys. Split multiple keys with a comma
  - -n / --number :: Number of items to return (Default=100)
  - -d / --date :: Date range to search - 24h, 30d, 90d etc. (Default=24h)

- Content
  - -u / --uuid :: UUID(s) to retrieve content for - Can submit multiple either comma or space separated 
  - -d / --download :: Download content to file
  - -j / --json :: Print return JSON 

- Submit
  - ...

# Technical Usage
```
usage: mainV2.3.py [-h] {search,content} ...

Wrapper for KIT Intel's API

positional arguments:
  {search,content}  commands
    search          Search KIT Intel
    content         Download file content

optional arguments:
  -h, --help        show this help message and exit

```
---
```

usage: mainV2.3.py search [-h] -s SEARCH [-f FILTER] [-n NUMBER] [-d DATE]

optional arguments:
  -h, --help            show this help message and exit
  -s SEARCH, --search SEARCH
                        Search term
  -f FILTER, --filter FILTER
                        Filter return keys. Split multiple keys with a comma
  -n NUMBER, --number NUMBER
                        Number of items to return - Default 100
  -d DATE, --date DATE  Date range to search - 24h, 30d, 90d etc.


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
## Sample Usage
### Search
```python
$ python3 KIT.py search -s 'content:google, filetype: php' -d 3d -f 'kit.UUID, filename' -n 3
$ python3 KIT.py content -u 2e517c8f-9375-4f55-a503-ca5bbd4d4a5b
```

