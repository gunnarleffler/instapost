```
  _           _                        _ 
 (_)_ __  ___| |_ __ _ _ __   ___  ___| |_
 | | '_ \/ __| __/ _` | '_ \ / _ \/ __| __|
 | | | | \__ \ || (_| | |_) | (_) \__ \ |_
 |_|_| |_|___/\__\__,_| .__/ \___/|___/\__|
                      |_|v1.6.0 10/18/2017

post data to CWMSv3+ databases in realtime

Default input format is YAML formatted as follows:

Station.Stage.Inst.0.0.RAW:
  timezone: GMT
  units: ft
  timeseries:
    '2017-06-02 13:00': 10.11
    '2017-06-02 14:00': 10.1
---
Station.Flow.Inst.~6Hours.0.RAW:
  timezone: GMT
  units: cfs
  timeseries:
    '2017-06-08T00:00:00Z':
      val: 30060.2
      qual: PROTECTED
    '2017-06-08T06:00:00Z':
      val: 30039.2
      qual: QUESTIONABLE


```

instapost is a program to post non SHEF data to CWMS 3.0.0+ databases

## Quick start
edit the instapost.json to reflect local settings.
Requires python 2.7.10+ and cx_Oracle.

## Directories

### /instapost
Directory which contains the instapost script and dependencies.

### /IDP

`get_idp` - gets idaho power data from thier webservice

`config.yaml` - example configuration file

### /rfc_utils 

Some utilities to pull data from the NWRFC

`pixml_to_yaml` - converts pixml files to instapost yaml

`get_rfc_local` - gets local flow data from NWRFC

`get_rfc_webservice` - gets forecast and observed data from NWRFC XML webservice

`get_rfc_ptr` - gets forecast and observed precip and temperature from NWRFC XML webservice 

`get_ahps` - gets AHPS observed data and official forecasts

### /canada 

`get_bc_asws` - gets ASWS (Snotel) data from British Columbia RFC.

### /config
Directory with example config files.

