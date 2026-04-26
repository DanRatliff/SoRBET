# Cutlery - useful functions that support the main SoRBET sonification libraries 
import numpy as np


def deal_with_nans(arr, method='min'):
    """
    STRAUSS doesn't like NaNs, so we fill them in for the sonification.
    
    method='min'      → replace NaN with the array's minimum (gaps → quietest)
    method='interp'   → linearly interpolate across NaN gaps
    method='zero'     → replace NaN with 0
    """
    arr = np.asarray(arr, dtype=float).copy()
    nan_mask = np.isnan(arr)
    if not nan_mask.any():
        return arr
    
    if method == 'min':
        arr[nan_mask] = np.nanmin(arr)

    elif method == 'interp':
        idx = np.arange(len(arr))

        arr[nan_mask] = np.interp(idx[nan_mask], idx[~nan_mask], arr[~nan_mask])

    elif method == 'zero':
        arr[nan_mask] = 0.0

    return arr