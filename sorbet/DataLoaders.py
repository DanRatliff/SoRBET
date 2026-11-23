import json
import numpy as np
import cdflib
import re
import urllib.request
from pathlib import Path
import os

_registry_path = Path(__file__).parent / 'FReESR.json'

with open(_registry_path) as f:
    REGISTRY = json.load(f)

"""
The first two functions here are DISCOVERY functions, which are queires to
determine what spacecraft are currently in FReESR, and given those craft,
what data is available from them
"""

def available_spacecraft():
    """
    Return all spacecraft names in the registry.
    """
    return {k for k in REGISTRY if not k.startswith('_')}


def available_quantities(craft):
    """
    Return all quantity names available for a given spacecraft.

    Inputs:
    -----------
    craft (str):
        The spacecraft being queried
    
    Returns:
    --------
    list of available data in the spacecraft
    """

    # Take inputted spacecraft name and convert it to lower case, to surpass any issues arising from input cases 
    craft = craft.lower()

    # Catch any errors related to putting a spacecraft into the function that isn't in FReESR
    if craft not in REGISTRY:
        raise ValueError(f"Unknown spacecraft: {craft}")
    
    #Otherwise, spit out all the available data quanitites from that spacecraft
    return {k for k in REGISTRY[craft] if not k.startswith('_')}



"""
This next function is the one the does the pattern searching at the heart of this more accessible data loader
"""


def find_cdf_file(base_url, filename_pattern):
    """
    Find CDF file from repository that matches the pattern, so that we don't have to worry about version patterns

    Inputs:
    -----------
    base_url (str):
        Directory URL (with trailing /)

    filename_pattern (str):
        Pattern like 'rbsp-a_wfr-waveform-continuous-burst_emfisis-l2_20160120t19'

    Returns:
    --------
    str : Filename found (e.g., 'rbsp-a_..._v1.6.2.cdf')
    """
    with urllib.request.urlopen(base_url) as response:
        html = response.read().decode('utf-8')

    # Find the .cdf files whose root matches the prescribed string
    pattern = rf'href="({re.escape(filename_pattern)}[^"]*\.(cdf|nc))"'
    matches = re.findall(pattern, html)

    # re.findall returns list of tuples when there are groups, so extract full match
    matches = [m[0] for m in matches]

    if not matches:
        raise FileNotFoundError(f"No file found matching {filename_pattern} at {base_url}")

    if len(matches) > 1:
        print(f"Warning: Multiple files match {filename_pattern}, using first: {matches[0]}")

    return matches[0]


"""
Private function (i.e. not one a user should be calling outside of this .py file)
that takes the urls that need years and months filled, and fills them based
on an inputted year and month. This allows us to scan over a year and month range in our data loader
"""

def _resolve_url(entry, date_str, year, month):
    """
    Resolve URL template placeholders from a registry entry.

    Inputs:
    -----------
    entry (dict):
        A single quantity's entry from the FReESR registry

    date_str (str):
        Date in YYYYMMDD format (e.g., '20150317')

    year (str):
        4-digit year string (e.g., '2015')

    month (str):
        2-digit zero-padded month string (e.g., '03')

    Returns:
    --------
    tuple of (base_url, filename_pattern) with placeholders filled in
    """
    #Now, because OMNI is a pain in the ass and does HALF YEARLY files I have to do some grunt work and catch that
    #Ergo, we check for half-years too. Thanks OMNI team.
    half = '01' if int(month) <= 6 else '07'
    
    # Update the base URL of where the file is located online, based on requested year month and date (and now, half year)
    base = entry['url_base'].format(year=year, month=month, date=date_str, half=half)

    # Update the filename pattern based on requested year month and date (...and half year)
    pattern = entry['filename_pattern'].format(year=year, month=month, date=date_str, half=half)

    return base, pattern

"""
The next two functions are the heavy hitters of this data loading scheme
"""

def fetch(craft, data, start, end, path='./data'):
    """
    Download data files for the supplied spacecraft and space data quantities.
    
    Inputs:
    -----------
    craft (str):
        Spacecraft name, e.g. 'rbsp-a', 'ace', 'goes-16'

    data (set of str):
        Quantities to grab, e.g. {'density', 'magnetic field', 'l-shell'}

    start (str):
        Start date in 'YYYY-MM-DD' format

    end (str):
        End date in 'YYYY-MM-DD' format

    path (str):
        Local directory to save files to (default: './data')
    
    Returns:
    --------
    results (dict):
        collection of {quantity_name: list of local file paths}
    """

    #We'll need datetime and timedelta to convert datetimes, and to march forward in days
    from datetime import datetime, timedelta
    
    #grab the spacecraft name and make it all lower case, just in case the input contains cases
    craft = craft.lower()

    # If the spacecraft isn't in FReESR, raise this as an error
    if craft not in REGISTRY:
        raise ValueError(
            f"Unknown spacecraft: {craft}. "
            f"Available: {available_spacecraft()}"
        )
    

    # We now compare the data that the registry lists for the supplied craft to the data asked for,
    # and raise an error if part of the data asked for is not in FReESR

    # Get available data quantities
    quantities = REGISTRY[craft]

    # Take data input, and delete any that exists in quantities - anything left is an unknown 
    # in the eyes of FReESR
    unknown = data - {k for k in quantities if not k.startswith('_')}

    # Now flag an error is unknown contains any elements/is not None
    if unknown:
        raise ValueError(
            f"Unknown quantities for {craft}: {unknown}. "
            f"Available: {available_quantities(craft)}"
        )
    
    # Group by data source so we don't download the same file twice!
    datasets_needed = {}

    for name in data:
        # For each requested data stream, we pull out the dataset it lives in
        ds = quantities[name]['dataset']

        #If we haven't already called it, initialise it
        if ds not in datasets_needed:
            datasets_needed[ds] = []

        # Now append the dataset pull request list with the data we want to pull from it
        datasets_needed[ds].append(name)
    
    # Take the inputted start and end dates and convert them to numbers so that we can count 
    # over the days that we loop
    start_dt = datetime.strptime(start, '%Y-%m-%d')
    end_dt = datetime.strptime(end, '%Y-%m-%d')
    

    #Initialise the results dictionay, the current date and whether the OMI year is done, 
    # when applicable
    results = {name: [] for name in data}
    current = start_dt
    _yearly_done = {}

    #The main loading loop - given the date/day, it loads the data associated with that day

    # There are multiple files with different cadences. In order to make sure we don't load a dataset,
    #  redownload the same set and then stack on multiples of the same dats, we do the following check 
    # to see if we've already fetched the data requested. Thus keep a check on files that have been 
    # resolved. This replaces the yearly check that used to exist in fetch, because OMNI is a 
    # monkey wrench and does half years - WHO DOES THAT!?

    _files_done = set()

    # Loop over dates
    while current <= end_dt:

        # Unpack date into YYYYMMDD, and explicitly grab the year and month - 
        # we'll need these for filepathing
        date_str = current.strftime('%Y%m%d')
        year = current.strftime('%Y')
        month = current.strftime('%m')

        # Loop over data requested
        for dataset_id, quantity_names in datasets_needed.items():
            # Get the registry entry (use first quantity's entry — they share the dataset)
            entry = quantities[quantity_names[0]]
            base_url, file_pattern = _resolve_url(entry, date_str, year, month)
            
#        Monthly/half-yearly files cover many days, so only grab each once
            if (dataset_id, file_pattern) in _files_done:
                continue

            try:
                cdf_filename = find_cdf_file(base_url, file_pattern)
                local_file = Path(path) / cdf_filename
                local_file.parent.mkdir(parents=True, exist_ok=True)
                if not local_file.exists():
                    urllib.request.urlretrieve(base_url + cdf_filename, str(local_file))

                for name in quantity_names:
                    results[name].append(str(local_file))
                _files_done.add((dataset_id, file_pattern))
                print(f"Loaded {dataset_id} for {date_str}")

            except FileNotFoundError as e:
                print(f"Skipping {dataset_id} on {date_str}: {e}")
        
        # Go to the next day in the list
        current += timedelta(days=1)

    return results






def load(craft, data, files,start = None,end=None):
    """
    Load and concatenate data from the downloaded cdf/nc files obtained by fetch.
    
    Inputs:
    -----------
    craft (str):
        Spacecraft name, e.g. 'rbsp-a', 'ace'

    data (set of str):
        Quantities to load, e.g. {'density', 'l-shell'}

    files (dict):
        Output from fetch() — maps quantity names to lists of local file paths

    start (str): optional
        YYY-MM-DD formatted starting instance, used if you want to trim longer datasets to the interval you want
    
    end (str): optional
        YYY-MM-DD formatted ending instance, inclusive of the day, used if you want to trim longer datasets to the interval you want
    
    Returns:
    --------
    dict : {quantity_name: {'time': array, 'data': array, 'raw_epoch': array}}
    """
    # Initialise the results dictionary
    result = {}
    
    #Now, for each variable 
    for name in data:
        #Unpack spacecraft's info from FReESR
        info = REGISTRY[craft][name]

        #Initialise the data arrays
        all_data = []
        all_time = []
        
        for f in files[name]:

            #Crack open the CDF
            cdf = cdflib.CDF(f)

            # Append the existing data with the data from this file
            all_data.append(cdf.varget(info['variables']['data']))

            #Append time with the time from this file
            all_time.append(cdf.varget(info['variables']['time']))
        
        # Make sure everything in concatenated
        raw_time = np.concatenate(all_time)
        dataset = np.concatenate(all_data)      # <- missing

        # Now, some data sources I shall not name (*OMNI*) do their data in
        if start is not None and end is not None:
            # Find out the time 
            timerange = cdflib.cdfepoch.to_datetime(raw_time)

            #Set up an index list of every time instance that falls within your start and end time
            keep = (timerange >= np.datetime64(start)) & (timerange < np.datetime64(end) + np.timedelta64(1, 'D'))

            #Restrict the time and value arrays to this index list
            raw_time = raw_time[keep]
            dataset = dataset[keep]
        
        # Convert epoch to elapsed hours using the registry metadata
        t_hours = epoch_to_hours(raw_time, info['epoch_type'])
        
        # Structure results into dictionary based on variable requested
        result[name] = {
            'time': t_hours,
            'data': dataset,
            'raw_epoch': raw_time
        }
    
    return result






def epoch_to_hours(epoch, epoch_type):
    """
    To make the time data sonification friendly, we convert epochs from the data to numeric arrays
    which are in terms of hours

    Inputs:
    --------
    epoch (array): the numeric epoch in raw form

    epoch_type (str): The label of epoch type (TT2000, regular cdf epoch or Epoch16)

    Returns:
    --------
    time data in hours (array)
    """
    if epoch_type == 'CDF_TT2000':
        return (epoch - epoch[0]) / 3.6E12
    elif epoch_type == 'CDF_EPOCH':
        return (epoch - epoch[0]) / 3.6E6
    elif epoch_type == 'CDF_EPOCH16':
        return (epoch - epoch[0]) / 3600
    else:
        raise ValueError(f"Unknown epoch type: {epoch_type}")
    
"""
This lil' character will clean up the current folder of the cdf and nc files, which 
can bloat the space a little bit too much
"""

def tidy_up(path='./data'):
    """
    Remove all downloaded space data files from the local cache and any empty folders.

    Inputs:
    -----------
    path (str):
        Directory to clean (default: './data')

    """
    #Grab current file path
    data_dir = Path(path)

    # If the CDFs are not there/already gone, say you do nothing
    if not data_dir.exists():
        print(f"Nothing to clean — {path} doesn't exist")
        return 0
    # Otherwise,  clear all the cdf/nc files
    count = 0
    for f in data_dir.glob('*.[cn][dc][f]*'):
        f.unlink()
        count += 1

    # Remove the directory too if it's now empty
    if not any(data_dir.iterdir()):
        data_dir.rmdir()

    print(f"Removed {count} files from {path}")
