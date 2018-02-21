# -*- coding: utf-8 -*-

import requests
import json
import pandas as pd
from datetime import datetime, timedelta

def reindex(df, start_date, end_date, freq):
        date = pd.date_range(start = datetime(*start_date), end = datetime(*end_date), freq = freq)
        date = [pd.Timestamp(x) for x in date]
        df = df.reindex(date)
        df.index.rename('date', inplace = True)
        return df

def get_frequency(index: pd.core.indexes.datetimes.DatetimeIndex)->str:
    """
    Args:
        
        index: a pd.core.indexes.datetimes.DatetimeIndex from a timeseries
        
    Returns:
        
        freq: a string value of either a daily, hourly, minutely, or secondly 
              Offset Alias with the appropriate multiple.
              This is not very robust, and returns False if it is not able to 
              easily determine the frequency
    """
    seconds = index.to_series().diff().median().total_seconds()
    minutes = seconds/60
    hours = minutes/60
    days = hours/24
    if days>=1 and days%int(days) == 0:
        freq = str(int(days))+'D'
    elif hours>=1 and hours%int(hours) == 0:
        freq = str(int(hours))+'H'
    elif minutes>=1 and minutes%int(minutes) == 0:
        freq = str(int(minutes))+'min'
    elif seconds>=1 and seconds%int(seconds) == 0:
        freq = str(int(seconds))+'S'
    else: 
        freq =  False
    return freq
    
    
def time_window_url(paths, public=True, lookback = 7, start_date = False, end_date = False, timezone = 'PST'):
    """
    helper function for cwms_read
    
    Arguments:  
        
        path -- cwms data path, 
        public -- boolean, 
        start_date -- date integer tuple format (YYYY, m, d)
        end_date -- date integer tuple format (YYYY, m, d)
        timezone -- optional keyword argument if time zone is specified.  
                    Defaults to 'PST' if nothing set
    Returns:
        
        url -- url string of CWMS data webservice for the specified 
               data path and time window
               
    """

    if isinstance(paths, list): 
        path = '%22%2C%22'.join(paths)
    else: path = paths
        
    if public:
        url = r'http://pweb.crohms.org/dd/common/web_service/webexec/getjson?timezone=TIMEZONE_&query=%5B%22PATH%22%5D&'
    else:
        url = r'http://nwp-wmlocal2.nwp.usace.army.mil/common/web_service/webexec/getjson?timezone=TIMEZONE_&query=%5B%22PATH%22%5D&'
    
    url = url.replace('PATH', path).replace('TIMEZONE_', timezone)
    if lookback:
        time = 'backward=' + str(lookback) + 'd'
        url = url + time
    else:
        url = url + 'startdate=START_MONTH%2FSTART_DAY%2FSTART_YEAR+00%3A00&enddate=END_MONTH%2FEND_DAY%2FEND_YEAR+00%3A00'
        sy,sm,sd = start_date
        start_date = datetime(sy,sm,sd)
        ey,em,ed = end_date
        end_date = datetime(ey,em,ed)
        url = url.replace('START_MONTH', str(start_date.month)).replace('START_DAY', str(start_date.day)).replace('START_YEAR', str(start_date.year))
        url = url.replace('END_MONTH', str(end_date.month)).replace('END_DAY', str(end_date.day)).replace('END_YEAR', str(end_date.year))
    
    return url

    

def get_cwms(path, public = True, fill = True, **kwargs):
    
    """
    A function to parse CWMS json data from webservice into a pandas dataframe
        
    Positional Arguments: 
        paths -- single string or list of string of CWMS data paths, example: 'TDDO.Temp-Water.Inst.1Hour.0.GOES-REV' 
    Keyword Arguments:
        
        The web service can either get a lookback, which is just a number of 
        days from the current day, or a time window.  Two key word arguments are 
        needed for a time wondow, start_date, end_date.  The Timezone can also
        be set.
        
        lookback    --  The number of days from current day to grab data.
                        (int or str) 
                        example: 7
                        
        start_date  --  The start of a time window (tuple) formatted 
                        (year, month, day)
                        example: (2017, 3, 22)
                        
        end_date    --  The end of a time window (tuple) formatted 
                        (year, month, day)
                        example: (2017, 3, 22)
        
        timezone    --  "PST", "PDT", "MST", "MDT", "GMT"
                        
                        
    Returns:
        
        df -- A pandas dataframe with metadata from the webservice is returned.  
              Metadata is stored in df.__dict__['metadata'], the data is used in 
              some of the plotting functions.  The metadata is easily lost if a df
              is copied or transformed in some way.  It may be best to export the 
              metadata if it is needed.  meta = df.__dict__['metadata']
        
        
    """
    try: 
        lookback = kwargs['lookback']
        start_date = False
        end_date = False
    except:
        lookback = False
        start_date = kwargs['start_date']
        end_date = kwargs['end_date']
    try:timezone = kwargs['timezone']
    except: timezone = 'PST'
    url = time_window_url(path,start_date=start_date, end_date=end_date, lookback = lookback, public=public,timezone = timezone)
    r = requests.get(url)
    json_data = json.loads(r.text)
    df_list = []
    meta = {}
    if not isinstance(path, list):
        path = [path]
    for site in path:
        s = site.split('.')[0]
        try:
            data = json_data[s]
        except KeyError:
            print('No data for %s' % site)
            continue
        lat = data['coordinates']['latitude']
        long = data['coordinates']['longitude']
        tz_offset = data['tz_offset']
        tz = data['timezone']
        for path, vals in data['timeseries'].items():
            
            column_name = '_'.join(path.split('.')[:2])
            column_name = '_'.join(column_name.split('-'))
            try:path_data = vals['values']
            except KeyError: 
                print('No data for %s' % site)
                continue
            date = [val[0] for val in path_data]
            values = [val[1] for val in path_data]
            df= pd.DataFrame({'date': date, column_name: values})
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace = True)
            df_list.append(df)
            vals.pop('values', None)
            vals.update({'path':path, 'lat':lat,'long':long, 'tz_offset':tz_offset, 'timezone':tz})
            meta.update({column_name:vals})
    
    df = pd.concat(df_list, axis = 1)
    
    if fill:
        freq = get_frequency(df.index)
        if not freq:
            print('Unable to determine frequency, returning data frame unfilled')
        else:
            if lookback:
                end = datetime.now()
                start = end - timedelta(days=lookback)
                start_date = (start.year,start.month,start.day)
                end_date = (end.year,end.month,end.day)
            df = df.pipe(reindex, start_date, end_date, freq)
    df.__dict__['metadata'] = meta
    return df
    

def catalog():
    
    """
    
    Requests the CWMS catalog.  Returns a large dict and not easy 
    wade through, it would be easier to go to a dataquery site to find 
    what you are looking for http://www.nwd-wc.usace.army.mil/dd/common/dataquery/www/
        
    Arguments: 
    
    Returns: dict
    
    """
    url = r'http://www.nwd-wc.usace.army.mil/dd/common/web_service/webexec/getjson?catalog=%5B%5D'
    r = requests.get(url)
    return json.loads(r.text)

def site_catalog(site):
    
    """
    Returns a dictionary of CWMS data paths for a particular site
    
    Arguments:
        site -- cwms site name, example TDDO
    
    Returns: 
        json.loads(r.text) -- dictionary of available site data
        
    """
    
    url = r'http://www.nwd-wc.usace.army.mil/dd/common/web_service/webexec/getjson?tscatalog=%5B%22SITE%22%5D'
    url = url.replace('SITE', site.upper())
    r = requests.get(url)
    return json.loads(r.text)

 


