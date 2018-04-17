#!/usr/local/bin/python
# -*- coding: utf-8 -*-
helpstr = '''
get_ndfd v1.0.0
2/20/2018
This program retireves observed data from the noaa mesowest XML service.
POC: Jeff Tilton
FORMATTING
==========
configuration file example
--------------------------
Bonneville Dam Agrimet, WA:
  lat: '45.64777778'
  long: '-121.9311111'
  paths:
    temp: BNDW.Temp-Air.Inst.3Hour.0.NOAA-FCST
    wspd: BNDW.Speed-Wind.Inst.3Hour.0.NOAA-FCST
Output
------
Output of this program is timeseries data in "instapost" YAML format
PARAMETERS
==========
'''

import sys, requests, argparse, json, yaml
from xml.dom import minidom
import unicodedata
from datetime import datetime, timedelta

#--------------------------------------------------------------------------------
#Configuration
#--------------------------------------------------------------------------------


#--------------------------------------------------------------------------------
#XML to dictionary conversion
#--------------------------------------------------------------------------------


def parse_element(element):
  '''Converts XML to dictionary data structure
    '''
  dict_data = dict()
  if element.nodeType == element.TEXT_NODE:
    if element.data.strip() != "":
      dict_data = unicodedata.normalize('NFKD', element.data).encode('ascii','ignore')
  if element.nodeType not in [
      element.TEXT_NODE, element.DOCUMENT_NODE, element.DOCUMENT_TYPE_NODE
  ]:
    for item in element.attributes.items():
      dict_data["@" + item[0]] = unicodedata.normalize('NFKD', item[1]).encode('ascii','ignore')
  if element.nodeType not in [element.TEXT_NODE, element.DOCUMENT_TYPE_NODE]:
    for child in element.childNodes:
      child_name, child_dict = parse_element(child)
      if child_name in dict_data:
        if child_dict != {}:
          try:
            dict_data[child_name].append(child_dict)
          except AttributeError:
            dict_data[child_name] = [dict_data[child_name], child_dict]
      else:
        if child_dict != {}:
          dict_data[child_name] = child_dict
    if dict_data.keys() == ["#text"]:
      dict_data = dict_data["#text"]
    elif dict_data.keys() == [u"#text"]:
      dict_data = dict_data[u"#text"]
  return element.nodeName, dict_data


def xml2dict(txt):
  dom = minidom.parseString(unicodedata.normalize('NFKD',txt).encode('ascii','ignore'))
  return parse_element(dom)[1]

def loadConfig(path, verbose = True):
  if verbose:
    sys.stderr.write("loading config file...")
  output = yaml.safe_load(open(path))
  if verbose:
    sys.stderr.write(" %d entries found.\n" % (len(output)))
  return output


def create_ndfd_url(lat, lon, ndfd = [''], units = 'e', start_date=(''), end_date=('')):
    """

    Args:
        lat:        latitude.
        
        lon:       longitude
        
        ndfd:       list of NDFD parameters that you are requesting.  For valid inputs 
                    see the NDFD Element Names Page below
                    https://graphical.weather.gov/xml/docs/elementInputNames.php
                    
        units:      "e" for English "m" for SI
        
        start_date: (yyyy, mm, dd) The beginning time for which you want NDFD data.   
                    If empty, the beginnng time is assumed to be the earliest available 
                    time in the database. Time should be in UTC time.
                    
        end_date:   (yyyy, mm, dd) The ending time for which you want NDFD data.   
                    If empty, the ending time is assumed to be the last available 
                    time in the database. Time should be in UTC time.
        
    Returns:
        url:        Formed url for National Digital Forecast Database (NDFD) web service


    """
    
    BASE_URL ="https://graphical.weather.gov/xml/sample_products/browser_interface/ndfdXMLclient.php?lat=LATITUDE&lon=LONGITUDE&product=time-series&begin=START_DATET00:00:00&end=END_DATET00:00:00&Unit=UNITS&NDFD"

    
    if start_date:
        start_date = [str(x) for x in start_date]
        start_date = '-'.join(start_date)
    if end_date:
        end_date = [str(x) for x in end_date]
        end_date = '-'.join(end_date)
    if list(filter(None, ndfd)):
        ndfd = [x + '=' + x for x in ndfd]
        ndfd = '&'.join(ndfd)
    else:
        ndfd = ''
    lat, lon = str(lat), str(lon)
    
    url = (BASE_URL
           .replace('LATITUDE', lat)
           .replace('LONGITUDE', lon)
           .replace('START_DATE', start_date)
           .replace('END_DATE', end_date)
           .replace('UNITS', units)
           .replace('NDFD', ndfd))
    
    return url


def get_ndfd_web_data(URL, verbose = True):
    """
    Note: Parses NOAA NDFD XML data.  The schema is not very regular so 
            there are a lot of exceptions and it is not able to parse all 
            available data right now.  

    Args:
        URL:   Fully formed url for National Digital Forecast Database (NDFD) web service
                see create_ndfd_url func
    Returns:
        result_dict: NDFD data parsed into dictionary keys are time keys given by the webservice
                    one time stamp series can be associated with multiple value series


    """
    
    raw = requests.get(URL).text
    data_dict = xml2dict(raw)['dwml']['data']
    times = data_dict['time-layout']
    result_dict = {}
    if not isinstance(times, list):
        times = [times]       
    for time in times:
        
        key = time['layout-key']#['#text']
         
        time_list = time['start-valid-time']
        
        if not isinstance(time_list, list): 
            time_list = [time_list]
        #time is on a location basis, converting all tz's to utc
        time_stamps = []
        for time in time_list:
            time_stamp = datetime.strptime(time[:19], '%Y-%m-%dT%H:%M:%S')
            offset = time[20:]
            hours = int(offset.split(':')[0])
            minutes = int(offset.split(':')[1])
            td = timedelta(hours = hours, minutes = minutes)
            time_stamp = time_stamp - td
            time_stamp = str(time_stamp)
            time_stamps.append(time_stamp)
        result_dict.update({key:{'time_stamps':time_stamps}})
    parameters = data_dict['parameters']
    params = list(parameters.keys())[1:]
    
    for p in params:
        data_list = parameters[p]
        if not isinstance(data_list, list):
            data_list = [data_list]
        for data in data_list:
            try:data['@time-layout']
            except KeyError:data = data[list(data.keys())[0]]
            key = data['@time-layout']
            try:
                values =  [x for x in data['value']]
            except:
                if verbose:
                    try:
                        data_type = data['name']
                        sys.stderr.write("\nCurrently no support for %s data\n" % data_type)
                    except KeyError:
                            sys.stderr.write("\nUnable to parse %s \n" % data)
                continue
            try:
                values = [float(x) for x in values]
            except ValueError:
                pass
            try:
                units = data['@units']
            except KeyError:
                units = ''
                if verbose:
                    try:
                        sys.stderr.write('\n%s is unitless\n' % data['name'])
                    except KeyError:
                        sys.stderr.write('\n%s is unitless\n' % data)
            
            if units == 'knots':
                values = [x*1.15078 for x in values]
                units = 'mph'
            elif units == 'Fahrenheit':
                units = 'F'
            try:
                result_dict[key]['parameters'].update({data['name']:{'values':values, 'units':units}})
            except KeyError:
                try:
                    result_dict[key].update({'parameters':{data['name']:{'values':values, 'units':units}}})
                except KeyError:
                    sys.stderr.write('\n%s not written to results\n' % data)
    return result_dict
    


def ndfd_to_instapost(site_name, lat, lon, paths, units = 'e', verbose = True):
    """

    Args:
        
        site_name:  Location name, only used in error handling, does not affect 
                      output
            
        lat:        latitude.
        
        lon:       longitude
        
        paths:      pathname dictionary {ndfd_element: pathname}
                    
        units:      "e" for English "m" for SI
        
        
    Returns:
        result_dict: Dictionary in Instapost format


    """
    result_dict = {}
    ndfd = [k for k in paths.keys()]
    URL = create_ndfd_url(lat,lon, ndfd=ndfd, units = units)
    data_dict = get_ndfd_web_data(URL, verbose = verbose)
    try:
        data_dict = get_ndfd_web_data(URL, verbose = verbose)
    except:
        sys.stderr.write("Error occured while parsing %s.\n" % site_name)
    for k,v in data_dict.items():
        time_stamps = v['time_stamps']
        for param, param_data in v['parameters'].items():
            vals = param_data['values']
            units = param_data['units']
            timeseries = dict((ts,val) for ts,val in zip(time_stamps, vals))
            timezone = 'UTC'
            ndfd_element = ndfd_param_dict[param]
            pathname = paths[ndfd_element]
            result_dict.update(
                                {pathname:{
                                            'timezone': timezone,
                                            'units': units,
                                            'timeseries':timeseries}
                                })
    return result_dict


#--------------------------------------------------------------------------------
# main()
#--------------------------------------------------------------------------------

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=helpstr, 
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('config', help='YAML formatted Configuration file')
    p.add_argument('-v', '--verbose', action='store_true', help='Work verbosely')
    p.add_argument('-rj', '--rawJSON', action='store_true', help='Output JSON')
    p.add_argument('-si', '--SI', action='store_true', help='SI units')
    args = p.parse_args()

    
    rawJSON = args.rawJSON
    config = args.config
    
    if args.SI: 
        units = 'm'
    else:
        units = 'e'
    
    if args.verbose:
        verbose = args.verbose
    else: verbose = False
    
    
    config_dict = loadConfig(config, verbose = verbose)
    ndfd_param_dict = yaml.safe_load(open('ndfd.yml')) 
    
    output = {}
    for key, value in config_dict.items():
        
        try:
            output.update(ndfd_to_instapost(site_name = key,  verbose = verbose, units = units, **value))
        except:
            print('\nNo data found for %s.\n' % key)
            
    
    for k, v in output.items():
        d = {k:v}
        if rawJSON: print(json.dumps(d))
        else: print(yaml.safe_dump(d, default_flow_style=False))
        print('---')
     
        
        

