# -*- coding: utf-8 -*-
helpstr = '''
get_avgs v1.0.0
2/20/2018
This program calculates the 12 hour averages in both the Oregon and Washington 
methods and also combines the two methods for the most restrictive of the two 
methods.
POC: Jeff Tilton
FORMATTING
==========
configuration file example
--------------------------
CHJ:
  path: GOES-COMPUTED
  methods:  ['or', 'wa', 'combined']
Output
------
Output of this program is timeseries data in "instapost" YAML format
PARAMETERS
==========
'''

import sys
import argparse
import json
import yaml
import pandas as pd
from cwms_read.cwms_read import get_cwms
from datetime import timedelta

def loadConfig(path: str, verbose = True)->dict:
  if verbose:
    sys.stderr.write("loading config file...")
  output = yaml.safe_load(open(path))
  if verbose:
    sys.stderr.write(" %d entries found.\n" % (len(output)))
  return output

def oregon_method(df:pd.core.frame.DataFrame) -> pd.core.frame.DataFrame:
    """
    Args:
        df: a pd.core.DataFrame of percent TDG saturation
        
    Returns:
        orgn: The return value. the 12 hour average of TDG data as described below
        
    Oregon Method:
        The Oregon method computes an average using the highest 12 hours TDG 
        readings of the day, then stores it as a daily time series.  The 12 hours
        do not need to be consecutive.
    """
    
    orgn = df \
        .groupby(pd.Grouper(level='date', freq='D')) \
        .aggregate(lambda x: x.sort_values(ascending = False) \
        .reset_index(drop = True).iloc[:12].mean())
    return orgn



def washington_method(df:pd.core.frame.DataFrame) -> pd.core.frame.DataFrame:
    """
    Args:
        df: a pd.core.DataFrame of percent TDG saturation
        
    Returns:
        wa_daily_max: The return value. the 12 hour average of TDG data as described below
        
    Washington Method:
        Use a rolling average to measure 12 consecutive hours. The highest 12 hour
        average in 24 hours is reported on the calendar day (ending at midnight) of the final
        measurement.
        - The first averaging period of each calendar day begins with the first
          hourly measurement at 1:00 a.m. This hour is averaged with the
          previous day’s last 11 hourly measurements.
        - Each subsequent hourly measure is averaged with the previous 11 hours
          until there are 24 averages for the day.
        - From the 24 hour averages, the highest average is reported for the
          calendar day.
        - Round 12 hour average to nearest whole number. 

    """
    #subtracting 1 minute from the index so the 01:00 value is the first value of the day
    index = [pd.Timestamp(x) - timedelta(minutes=1)  for x in df.index.values]
    df.index = index
    df.index.name = 'date'
    roll = df.rolling(window = 12, min_periods = 1, axis = 0).mean()
    
    wa_daily_max = roll.groupby(pd.Grouper(level='date', freq='D')).max().round(decimals = 0)
    return wa_daily_max

def combine(orgn:pd.core.frame.DataFrame, wa:pd.core.frame.DataFrame) -> pd.core.frame.DataFrame:
    """

    Args:
        orgn: a pd.core.DataFrame of the 12 hour average of TDG data computed by 
              the oregon_method
              
        wa: a pd.core.DataFrame of the 12 hour average of TDG data computed by 
              the washington_method
    Returns:
        combined: The return value. the 12 hour average of TDG data as described below
        
    Washington Method:
        The Combined method takes the higher TDG average between the Oregon and 
        Washington methods and stores it as a daily time series.  

    """
    
    
    return pd.concat([wa, orgn]).groupby(level=0).max()

def pd_series_to_instapost(timeseries:pd.core.series.Series, pathname:str, units:str, timezone:str)->dict:
    """
    Args:
        series: a pd.core.Series time series with a time stamp index 
              
        pathname: pathname the data is to be stored at
        
        units: the units the data is in
        
        timezone: the timestamp timezone
        
    Returns:
        result: Dictionary in instapost format
    """
    result = {}
    timeseries = {str(ts):float(val) for ts,val in zip(timeseries.index, timeseries.values)}
    result.update(
                        {pathname:{
                                    'timezone': timezone,
                                    'units': units,
                                    'timeseries':timeseries}
                                })
    return result


 #--------------------------------------------------------------------------------
# main()
#--------------------------------------------------------------------------------

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=helpstr, 
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('config', help='YAML formatted Configuration file')
    p.add_argument('-l', '--lookback', help='Lookback a number of days')
    p.add_argument('-v', '--verbose', action='store_true', help='Work verbosely')
    p.add_argument('-rj', '--rawJSON', action='store_true', help='Output JSON')
    args = p.parse_args()

    verbose = args.verbose
    rawJSON = args.rawJSON
    config = args.config
    
    if args.lookback:
        lookback = int(args.lookback)
    else:
        lookback = 1
    
    config_dict = loadConfig(config, verbose = verbose)
    
    #get lists of projects to do for each method
    oregon = []
    washington = []
    combined = []
    for key, values in config_dict.items():
        if 'or' in values['methods']:
            oregon.append(key)
        if 'wa' in values['methods']:
            washington.append(key)
        if 'combined' in values['methods']:
            combined.append(key)
            
    #create the base pathname for each project.  The pathnames are not consistent
    #in the last section of the pathname.  This will also be done to both the 
    # raw and revised data so 2 separate pathname lists are made for each
    
    path = '.%-Saturation-TDG.Inst.1Hour.0.'
    paths = []
    for key, value in config_dict.items():
        path_end = value['path']
        paths.append('{}{}{}'.format(key, path, path_end))
    
    df = get_cwms(paths, lookback = lookback, public = True)
    meta = df.__dict__['metadata']
    data_dict = {'Washington': [x+'_%_Saturation_TDG' for x in washington],
                 'Oregon': [x+'_%_Saturation_TDG' for x in oregon],
                 'Combined': [x+'_%_Saturation_TDG' for x in combined]}
    for key, value in data_dict.items():
        missing_data = [x for x in value if x not in df.columns]
        data_dict[key] = [x for x in value if x in df.columns]
        if verbose:
            print('{}{}'.format(key, ' data missing for'))
            for site in missing_data:print(site.split('_')[0])
    
    
    wa_daily_max = df[data_dict['Washington']].pipe(washington_method)
    or_daily_max = df[data_dict['Oregon']].pipe(oregon_method)
    combined_wa = wa_daily_max[data_dict['Combined']]
    combined_or = or_daily_max[data_dict['Combined']]
    combined_daily_max = combine(wa_daily_max,or_daily_max)
    new_pathname = '.%-Saturation-TDG.Avg.12Hour.0.'
    for data in [(combined_daily_max,new_pathname +'Combined'), (wa_daily_max,new_pathname +'Washington'),(or_daily_max,new_pathname +'Oregon')]:
        dataframe, path_name = data
        instapost = dataframe.apply(lambda x: pd_series_to_instapost(
                                                x, 
                                                x.name.split('_')[0]+path_name, 
                                                meta[x.name]['units'], 
                                                meta[x.name]['timezone']), axis = 0)
        
        if rawJSON:instapost.apply(lambda x: print(json.dumps(x)))
        else: instapost.apply(lambda x: print(yaml.dump(x)))
        
     


