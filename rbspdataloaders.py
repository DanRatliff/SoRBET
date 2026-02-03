import urllib.request
import re
import cdflib
import numpy as np
from datetime import datetime, timedelta

def find_cdf_file(base_url, filename_pattern):
    """
    Find CDF file on CDAWeb that matches the pattern, so that we don't have to worry about version patterns

    Parameters:
    -----------
    base_url : str
        Directory URL (with trailing /)
    filename_pattern : str
        Pattern like 'rbsp-a_wfr-waveform-continuous-burst_emfisis-l2_20160120t19'

    Returns:
    --------
    str : Filename found (e.g., 'rbsp-a_..._v1.6.2.cdf')
    """
    with urllib.request.urlopen(base_url) as response:
        html = response.read().decode('utf-8')

    # Find the .cdf files whose root matches the prescribed string
    pattern = rf'href="({re.escape(filename_pattern)}[^"]*\.cdf)"'
    matches = re.findall(pattern, html)

    if not matches:
        raise FileNotFoundError(f"No file found matching {filename_pattern} at {base_url}")

    if len(matches) > 1:
        print(f"Warning: Multiple files match {filename_pattern}, using first: {matches[0]}")

    return matches[0]

def download_van_allen_files(probe, date, year):
    """
    Download Van Allen Probes files for a given probe, date and year, ignoring version numbers (yippee!)

    Inputs:
    -----------
    probe : str (e.g., 'rbspa')
    date (YYYYMMDD) : str (e.g., '20160120')
    year : str (e.g., '2016')
    """
    base = f'https://cdaweb.gsfc.nasa.gov/pub/data/rbsp/{probe}'

    wave_base = f'{base}/l2/emfisis/wfr/waveform/{year}/'
    mag_base = f'{base}/l2/emfisis/magnetometer/uvw/{year}/'
    density_base = f'{base}/l4/emfisis/density/{year}/'
    wna_base = f'{base}/l4/emfisis/wna-survey-sheath-corrected-e/{year}/'

    # Grab the files using the other function, find_cdf_file
    wave_file = find_cdf_file(wave_base, f'rbsp-a_wfr-waveform_emfisis-l2_{date}')
    mag_file = find_cdf_file(mag_base, f'rbsp-a_magnetometer_uvw_emfisis-l2_{date}')
    density_file = find_cdf_file(density_base, f'rbsp-a_density_emfisis-l4_{date}')
    wna_file = find_cdf_file(wna_base, f'rbsp-a_wna-survey-sheath-corrected-e_emfisis-l4_{date}')

    # Download each of them
    urllib.request.urlretrieve(wave_base + wave_file, 'data_file.cdf')
    urllib.request.urlretrieve(mag_base + mag_file, 'mag_file.cdf')
    urllib.request.urlretrieve(density_base + density_file, 'density_file.cdf')
    urllib.request.urlretrieve(wna_base + wna_file, 'wna_file.cdf')


def download_van_allen_daterange(probe, start_date, end_date):
    """
    Download and concatenate Van Allen Probes data over a date range.
    
    Parameters:
    -----------
    probe : str (e.g., 'rbspa')
    start_date : datetime
    end_date : datetime
    
    Returns:
    --------
    dict : Dictionary containing concatenated arrays for each variable
    """
    from datetime import timedelta
    
    # Initialise empty lists to accumulate data
    data = {
        'Bu': [], 'Bv': [], 'Bw': [], 'wave_epoch': [],
        'mag': [], 'mag_epoch': [],
        'density': [], 'density_epoch': [],
        'thsvd': [],'plansvd': [],'wfr_freqs': [],
        'bsum': [],'wna_epoch': []
    }
    
    current = start_date
    while current <= end_date:
        date_str = current.strftime('%Y%m%d')
        year = current.strftime('%Y')
        
        try:
            # Download files for this day
            download_van_allen_files(probe, date_str, year)
            
            # Extract waveform data
            wave_cdf = cdflib.CDF('data_file.cdf')
            data['Bu'].append(wave_cdf.varget('BuSamples').reshape(-1))
            data['Bv'].append(wave_cdf.varget('BvSamples').reshape(-1))
            data['Bw'].append(wave_cdf.varget('BwSamples').reshape(-1))
            data['wave_epoch'].append(wave_cdf.varget('Epoch'))
            
            # Extract magnetometer data
            mag_cdf = cdflib.CDF('mag_file.cdf')
            data['mag'].append(mag_cdf.varget('Magnitude'))
            data['mag_epoch'].append(mag_cdf.varget('Epoch'))
            
            # Extract density data
            density_cdf = cdflib.CDF('density_file.cdf')
            data['density'].append(density_cdf.varget('density'))
            data['density_epoch'].append(density_cdf.varget('Epoch'))
            
            # Extract WNA data
            wna_cdf = cdflib.CDF('wna_file.cdf')
            data['thsvd'].append(wna_cdf.varget('thsvd'))
            data['plansvd'].append(wna_cdf.varget('plansvd'))
            data['bsum'].append(wna_cdf.varget('bsum'))
            data['wna_epoch'].append(wna_cdf.varget('Epoch'))
            
            print(f"Loaded {date_str}")
            
        except FileNotFoundError as e:
            print(f"Skipping {date_str}: {e}")
        
        current += timedelta(days=1)
    #To avoid overfrequency-ing, assign WFR Frequencies at the end
    data['wfr_freqs'].append(wna_cdf.varget('WFR_Frequencies'))
    #Uninstall the files
    

    # Concatenate all arrays
    return {key: np.concatenate(val) for key, val in data.items() if val}