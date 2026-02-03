from scipy import signal
from scipy.interpolate import interp1d
import numpy as np

def compute_filtered_waveform(time, waveform, B0_time, B0_mag,
                                 nperseg=256, noverlap=None,
                                 f_min_factor=0.1, f_max_factor=1.0,
                                 window='hann'):
    """
    Compute waveforms filtered to Whistler frequency range
    [f_min_factor*fce, f_max_factor*fce].

    Parameters:
    -----------
    time : array
        Time array for waveform data
    waveform : array
        Electric or magnetic field waveform
    B0_time : array
        Time array for background magnetic field data
    B0_mag : array
        Background magnetic field magnitude in nT
    nperseg : int
        Length of each segment for STFT (default 256)
    noverlap : int
        Number of overlapping points (default nperseg//2)
    f_min_factor : float
        Lower frequency bound as fraction of fce (default 0.1)
    f_max_factor : float
        Upper frequency bound as fraction of fce (default 1.0)
    window : str
        Window type for STFT (default 'hann')

    Returns:
    --------
    time : array
        Time array for waveform
    waveform_filter: array
        Array of filtered waveform
    """

    # Compute gyrofrequency using the inputted magnetic field
    fce = (1.602176634e-19 * B0_mag*1e-9) / (2 * np.pi * 9.1093837015e-31)

    # Interpolate fce to time timescales/time points of the waveform
    fce_interp_func = interp1d(B0_time, fce, kind='linear',
                               bounds_error=False, fill_value='extrapolate')
    fce_at_times = fce_interp_func(time)

    print(f"fce range: {fce_at_times.min():.1f} - {fce_at_times.max():.1f} Hz")
    print(f"Looking for frequencies between {f_min_factor*fce_at_times[0]:.1f} and {f_max_factor*fce_at_times[0]:.1f} Hz")

    # Compute sampling frequency for STFT - time is uniform so just need diff between first two points
    dt = time[1] - time[0]
    fs = 1.0 / dt

    # Set overlap, if one is supplied - otherwise it's the standard Nyquist frequency
    if noverlap is None:
        noverlap = nperseg // 2

    # Create window for STFT
    win = signal.get_window(window, nperseg)

    # Create ShortTimeFFT object
    hop = nperseg - noverlap
    SFT = signal.ShortTimeFFT(win, hop=hop, fs=fs,
                              mfft=nperseg, scale_to=None)

    # Compute STFT (complex values)
    Wave_FS = SFT.stft(waveform)

    # Get frequency and time arrays
    f_spec = SFT.f
    t_spec = SFT.t(len(waveform))

    # Convert spectrogram times to absolute time
    t_spec_abs = time[0] + t_spec

    # Interpolate fce to STFT times
    fce_at_stft_times = fce_interp_func(t_spec_abs)

    # Create frequency mask for each time step and filter
    FS_filtered = np.zeros_like(Wave_FS)

    for ii, fce_val in enumerate(fce_at_stft_times):
        f_min = f_min_factor * fce_val
        f_max = f_max_factor * fce_val

        # Create mask for this time step
        mask = (f_spec >= f_min) & (f_spec <= f_max)

        # Apply mask to STFT
        FS_filtered[mask, ii] = Wave_FS[mask, ii]

    # Inverse STFT to get filtered waveform
    waveform_filtered = SFT.istft(FS_filtered, k1=len(waveform))

    return time, waveform_filtered

def compute_avg_wna_from_emfisis(time, fce_time, B0, thsvd, plansvd, bsum, frequencies,
                                  f_min_factor=0.1, f_max_factor=1.0,planarity_threshold=0.5):
    """
    Compute average wave normal angle from EMFISIS L4 WNA survey data.
    """

    #Compute fce from B0 vector

    fce = (1.602176634e-19 * B0*1e-9) / (2 * np.pi * 9.1093837015e-31)

    # Interpolate fce to WNA data times
    fce_interp_func = interp1d(fce_time, fce, kind='linear',
                               bounds_error=False, fill_value='extrapolate')
    fce_at_times = fce_interp_func(time)

    print(f"fce range: {fce_at_times.min():.1f} - {fce_at_times.max():.1f} Hz")
    print(f"Looking for frequencies between {f_min_factor*fce_at_times[0]:.1f} and {f_max_factor*fce_at_times[0]:.1f} Hz")


    # Compute power-weighted average WNA
    wna_avg = np.zeros(len(time))

    for ii, fce_val in enumerate(fce_at_times):
        #Assign the upper and lower filters for the frequency mask
        f_min = f_min_factor * fce_val
        f_max = f_max_factor * fce_val

        #Define mask using Boolean
        mask = (frequencies >= f_min) & (frequencies <= f_max)

        #If no such points match the frequency mask? Assign 90 (max wave angle)
        if not np.any(mask):
            wna_avg[ii] = 90
            continue
        #Extract the arrays at the masked values
        theta_masked = thsvd[ii, mask]
        power_masked = bsum[ii, mask]
        planarity_masked = plansvd[ii, mask]

        # Valid points: not NaN, positive power, and good planarity
        valid = (~np.isnan(theta_masked) &
                 ~np.isnan(power_masked) &
                 (power_masked > 0) &
                 ~np.isnan(planarity_masked) &
                 (planarity_masked >= planarity_threshold))

        if np.any(valid):
            wna_avg[ii] = np.average(theta_masked[valid],
                                   weights=power_masked[valid])
        else:
            wna_avg[ii] = 90

    return time, wna_avg