```
  _           _                        _
 (_)_ __  ___| |_ __ _ _ __   ___  ___| |_
 | | '_ \/ __| __/ _` | '_ \ / _ \/ __| __|
 | | | | \__ \ || (_| | |_) | (_) \__ \ |_
 |_|_| |_|___/\__\__,_| .__/ \___/|___/\__|
                      |_|v1.0.2 12/07/2016

post data to CWMSv3+ databases in realtime

usage: instapost [-h] [-v] [-t] [-p PATHNAME] [-y] [-j] [-f FILE]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Work verbosely
  -t, --tsv             input in TSV format
  -p PATHNAME, --pathname PATHNAME
                        database pathname to store TSV file
  -y, --yaml            input in YAML format
  -j, --json            input in JSON format
  -f FILE, --file FILE  specify input file (default is STDIN)

```

instapost is a program to post non SHEF data to CWMS 3.0.0+ databases

## Quick start
edit the instapost.json to reflect local settings.
Requires python 2.7.10+ and cx_Oracle.

##Directories

### rfc_utils 

`get_rfc_local` - gets local flow data from NWRFC
`get_rfc_webservice` - gets forecast and observed data from nwrfc XML webservice
`get_ahps` - gets AHPS observed data and official forecasts

### config
directory to generate config files

