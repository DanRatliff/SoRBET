"""
SLOE.py - Spectraliser Libraries for Offline Exploration

Part of SoRBET (Sonic Radiation Belt Environment Toolkit).

Pre-built sonification functions using the STRAUSS Spectralizer generator,
for spectral data such as wave power spectral density (e.g. WMC chorus
spectra from EMFISIS). The Spectralizer maps a frequency spectrum onto an
audible frequency range using an inverse FFT, so spectral shape becomes
audible timbre.

Dependencies: strauss, numpy
"""

from strauss.sonification import Sonification
from strauss.sources import Objects
from strauss.generator import Spectralizer
from strauss.score import Score
import numpy as np

# ===========================================================================
# PLUM-style functions: one primary mapping each, simple call signatures
# ===========================================================================
 
def SpectrumSonification(notes, length, spectrum_data,
                         min_freq=50, max_freq=2000,
                         interp_type='preserve_power',
                         fit_spec_multiples=True,
                         equal_loudness=False,
                         system='mono'):
    """
    Sonify a single (static) frequency spectrum. Takes a 1D array of
    power/flux values ordered low-to-high frequency and renders it as a
    sustained tone whose timbre is the spectrum shape.
 
    ----------
    Inputs:
    ----------
 
    notes (nested list):
        The notes used by the sonification, in scientific notation.
 
    length (int):
        Length (in seconds) of the produced sonification.
 
    spectrum_data (array-like, 1D):
        Power/flux values of the spectrum, ordered low-to-high frequency.
 
    min_freq (float):
        Minimum audio frequency (Hz) the spectrum maps onto. Default 50.
 
    max_freq (float):
        Maximum audio frequency (Hz) the spectrum maps onto. Default 2000.
 
    interp_type (str):
        'sample' for direct interpolation, 'preserve_power' to avoid
        missing narrow spectral features. Default 'preserve_power'.
 
    fit_spec_multiples (bool):
        Pad iFFT so spectrum sample points land on exact FFT bins.
        Default True.
 
    equal_loudness (bool):
        Apply ISO 226 equal-loudness normalisation. Default False.
 
    system (str):
        Audio system: 'mono', 'stereo', '5.1', etc. Default 'mono'.
 
    ----------
    Returns:
    ----------
 
    soni (Sonification): the rendered STRAUSS Sonification object.
    """
    spectrum_data = np.asarray(spectrum_data)
    if spectrum_data.ndim != 1:
        raise ValueError(f"SpectrumSonification expects a 1D spectrum, got shape {spectrum_data.shape}. "
                         "For time-evolving spectra, use SpectrogramSonification instead!")
 
    # 1) Set up the STRAUSS score
    score = Score(notes, length)
    NoNotes = len(notes[0]) if isinstance(notes[0], list) else len(notes)
 
    # 2) Map the spectrum to source(s)
    maps = {
        'pitch': list(range(NoNotes)),
        'spectrum': [spectrum_data] * NoNotes
    }
 
    sources = Objects(maps.keys())
    sources.fromdict(maps)
    sources.apply_mapping_functions()
 
    # 3) Set up the Spectralizer with the requested frequency range and interpolation
    generator = Spectralizer()
    generator.modify_preset({
        'min_freq': min_freq,
        'max_freq': max_freq,
        'interpolation_type': interp_type,
        'fit_spec_multiples': fit_spec_multiples,
        'equal_loudness_normalisation': equal_loudness,
    })
 
    # 4) Build and render
    soni = Sonification(score, sources, generator, system)
    soni.render()
 
    return soni
 
 
def SpectrogramSonification(notes, length, spectrogram_data,
                            min_freq=50, max_freq=2000,
                            interp_type='preserve_power',
                            regen_phases=True,
                            equal_loudness=False,
                            system='mono'):
    """
    Sonify a time-evolving spectrogram (2D: time x frequency). Each row
    is a spectrum at a different time step; the Spectralizer cross-fades
    between them so you hear the spectral structure evolve over time.
 
    ----------
    Inputs:
    ----------
 
    notes (nested list):
        The notes used by the sonification, in scientific notation.
 
    length (int):
        Length (in seconds) of the produced sonification.
 
    spectrogram_data (array-like, 2D, shape ntime x nfreq):
        Power spectral density array. Rows are time steps, columns are
        frequency bins ordered low-to-high.
 
    min_freq (float):
        Minimum audio frequency (Hz). Default 50.
 
    max_freq (float):
        Maximum audio frequency (Hz). Default 2000.
 
    interp_type (str):
        'sample' or 'preserve_power'. Default 'preserve_power'.
 
    regen_phases (bool):
        Regenerate random phases for each time buffer. Default True.
 
    equal_loudness (bool):
        Apply ISO 226 equal-loudness normalisation. Default False.
 
    system (str):
        Audio system. Default 'mono'.
 
    ----------
    Returns:
    ----------
 
    soni (Sonification): the rendered STRAUSS Sonification object.
    """
    spectrogram_data = np.asarray(spectrogram_data)
    if spectrogram_data.ndim != 2:
        raise ValueError(f"SpectrogramSonification expects a 2D array (ntime x nfreq), "
                         f"got shape {spectrogram_data.shape}. "
                         "For a single spectrum, use SpectrumSonification instead.")
 
    score = Score(notes, length)
    NoNotes = len(notes[0]) if isinstance(notes[0], list) else len(notes)
 
    maps = {
        'pitch': list(range(NoNotes)),
        'spectrum': [spectrogram_data] * NoNotes
    }
 
    sources = Objects(maps.keys())
    sources.fromdict(maps)
    sources.apply_mapping_functions()
 
    # Set up the Spectralizer for evolving spectra
    generator = Spectralizer()
    generator.modify_preset({
        'min_freq': min_freq,
        'max_freq': max_freq,
        'interpolation_type': interp_type,
        'regen_phases': regen_phases,
        'equal_loudness_normalisation': equal_loudness,
    })
 
    soni = Sonification(score, sources, generator, system)
    soni.render()
 
    return soni
 
 
def SpectrogramCutoffSonification(notes, length, spectrogram_data, time_data,
                                  cutoff_data=None,
                                  min_freq=50, max_freq=2000,
                                  interp_type='preserve_power',
                                  cutoff_lims=('0%', '100%'),
                                  cutoff_plims=(0.05, 0.95),
                                  regen_phases=True,
                                  equal_loudness=False,
                                  system='mono'):
    """
    Sonify a time-evolving spectrogram with an additional cutoff filter
    mapped to a secondary data stream. Combines the Spectralizer's
    spectral-to-sound mapping with STRAUSS's low-pass filter, so you can
    layer a second variable on top of the spectral timbre.
 
    ----------
    Inputs:
    ----------
 
    notes (nested list):
        The notes used by the sonification, in scientific notation.
 
    length (int):
        Length (in seconds) of the produced sonification.
 
    spectrogram_data (array-like, 2D, shape ntime x nfreq):
        Power spectral density array.
 
    time_data (array-like, 1D):
        Time axis for the cutoff evolution.
 
    cutoff_data (array-like, 1D, or None):
        Data to map to the filter cutoff. If None, no filter is applied.
 
    min_freq (float):
        Minimum audio frequency (Hz). Default 50.
 
    max_freq (float):
        Maximum audio frequency (Hz). Default 2000.
 
    interp_type (str):
        'sample' or 'preserve_power'. Default 'preserve_power'.
 
    cutoff_lims (tuple):
        Mapping limits for cutoff data. Default ('0%', '100%').
 
    cutoff_plims (tuple):
        Parameter limits for cutoff (fraction of audible range).
        Default (0.05, 0.95).
 
    regen_phases (bool):
        Regenerate random phases per buffer. Default True.
 
    equal_loudness (bool):
        Apply ISO 226 equal-loudness normalisation. Default False.
 
    system (str):
        Audio system. Default 'mono'.
 
    ----------
    Returns:
    ----------
 
    soni (Sonification): the rendered STRAUSS Sonification object.
    """
    spectrogram_data = np.asarray(spectrogram_data)
    if spectrogram_data.ndim != 2:
        raise ValueError(f"Expected 2D spectrogram, got shape {spectrogram_data.shape}.")
 
    score = Score(notes, length)
    NoNotes = len(notes[0]) if isinstance(notes[0], list) else len(notes)
 
    # Build maps — always include spectrum and time_evo
    maps = {
        'pitch': list(range(NoNotes)),
        'spectrum': [spectrogram_data] * NoNotes,
        'time_evo': [time_data] * NoNotes,
    }
 
    lims = {'time_evo': ('0%', '100%')}
    plims = {}
 
    # Optionally add cutoff mapping
    if cutoff_data is not None:
        maps['cutoff'] = [cutoff_data] * NoNotes
        lims['cutoff'] = cutoff_lims
        plims['cutoff'] = cutoff_plims
 
    sources = Objects(maps.keys())
    sources.fromdict(maps)
    sources.apply_mapping_functions(map_lims=lims, param_lims=plims)
 
    generator = Spectralizer()
    generator.modify_preset({
        'min_freq': min_freq,
        'max_freq': max_freq,
        'interpolation_type': interp_type,
        'regen_phases': regen_phases,
        'equal_loudness_normalisation': equal_loudness,
    })
 
    # Turn on the filter if cutoff data is supplied
    if cutoff_data is not None:
        generator.modify_preset({'filter': 'on'})
 
    soni = Sonification(score, sources, generator, system)
    soni.render()
 
    return soni
 
 
# ===========================================================================
# ManGOE-style function: config-dictionary builder for the Spectralizer
# ===========================================================================
 
def SLOE_Object(notes, length, Maps,
                min_freq=50, max_freq=2000,
                interp_type='preserve_power',
                regen_phases=True,
                fit_spec_multiples=True,
                equal_loudness=False,
                map_lims=None, parameter_lims=None,
                system='mono'):
    """
    A consolidated STRAUSS Spectralizer sonification builder that generates an
    Object-class (i.e. continuous in time) source sonification from a spectrum
    or spectrogram plus additional mapped parameters.
 
    This is the ManGOE-equivalent for spectral sonification: pass a 'spectrum'
    key in Maps (1D or 2D array), plus optional additional mappings ('volume',
    'cutoff', 'pitch_shift', 'azimuth', etc.), and the builder handles the
    STRAUSS plumbing.
 
    ----------
    Inputs:
    ----------
 
    notes (nested list):
        The notes used by the sonification, in scientific notation.
 
    length (int):
        Length (in seconds) of the produced sonification.
 
    Maps (dict):
        The key-data pairs used to map features of the sound to the prescribed
        dataset. Must include 'spectrum' (1D or 2D array). Other keys include
        properties of the sound such as:

        'volume', 'cutoff', 'pitch_shift',
        'time_evo', 'azimuth', 'volume_lfo/amount', etc.

        If 'time_evo' is not included, it is automatically generated within
        this function. Any key paired to None will be passed over.
 
    min_freq (float):
        Minimum audio frequency (Hz). Default 50.
 
    max_freq (float):
        Maximum audio frequency (Hz). Default 2000.
 
    interp_type (str):
        'sample' or 'preserve_power'. Default 'preserve_power'.
 
    regen_phases (bool):
        Regenerate phases per buffer for evolving spectra. Default True.
 
    fit_spec_multiples (bool):
        Pad iFFT for exact spectrum-to-bin alignment. Default True.
 
    equal_loudness (bool):
        Apply ISO 226 normalisation. Default False.
 
    map_lims (dict):
        key - percentage limits which determine the permissible range of the
        data to be used, in terms of the original data range.
        Supplied as ('0%','100%') for all mapped properties by default.
 
    parameter_lims (dict):
        key - value pairs which determine the permissible range of the sound
        properties. Supplied as a set of defaults unless other limits passed
        into function.
 
    system (str):
        The sound system used by the STRAUSS sonification generated
        (e.g. mono, stereo, DOLBY 5.1)
 
    ----------
    Returns:
    ----------
 
    soni (Sonification): the resulting STRAUSS sonification
 
    """
 
    # 1) Set up the STRAUSS score using the given notes and length of sonification
    score = Score(notes, length)
 
    # 2) Use the Maps input to dynamically build up the maps for this sonification
 
    # Start by determining active number of notes
    NoNotes = len(notes[0]) if isinstance(notes[0], list) else len(notes)
 
    # Determine active maps from the input — ignore anything set to None
    active_maps = {k: v for k, v in Maps.items() if v is not None}
 
    # Error handling: if there are no maps, error out here
    if not active_maps:
        print(" No data mapped — stopping.")
        return None
 
    # The spectrum key is required for SLOE
    if 'spectrum' not in active_maps:
        print(" SLOE requires a 'spectrum' key in Maps — stopping.")
        return None
    
    #An error I often befall is a quirk of panning sonifications, which is that if polar is not set, 
    # then the default polar is zero, and then this leads to no panning at all! 
    # So we let ManGOE know we injected it ourselves with the polr_guard flag
    polar_guard = False

    if 'azimuth' in active_maps and 'polar' not in active_maps:
        active_maps['polar'] = np.full_like(
        next(v for k, v in active_maps.items() if k != 'spectrum'), 0.5)
        polar_guard = True
 
    # If the time evolution is not in active maps, we add it.
    # As the time values themselves don't matter we just generate an arange
    # which is the same length as the first non-spectrum data array
    if 'time_evo' not in active_maps:
        non_spectrum = {k: v for k, v in active_maps.items() if k != 'spectrum'}
        if non_spectrum:
            dummy_data = next(v for v in non_spectrum.values())
            active_maps['time_evo'] = np.arange(len(dummy_data))
 
    # Now we start initialising the maps, starting with pitch
    maps = {'pitch': list(range(NoNotes))}
 
    # Use the active maps to populate the remainder of the maps
    for prop, data in active_maps.items():
        maps[prop] = [data] * NoNotes
 
    # 2a) Set up the data limits of the maps
    # As a consequence in cases where polar is inserted by us (polar_guard = True) 
    # we have to exclude it from these auto limits, else it gives a divide by zero error 
    # and STRAUSS dies
    mlims = {k: ('0%', '100%') for k in active_maps if k != 'spectrum' and not (k == 'polar' and polar_guard)}

 
    if map_lims is not None:
        mlims.update(map_lims)
 
    # 2b) Set the parameter limits using the same approach as ManGOE
    default_plims = {
        'volume':            (0.05, 1.0),
        'cutoff':            (0.05, 0.95),
        'pitch_shift':       (-12, 12),
        'azimuth':           (0, 1),
        'volume_lfo/amount': (0, 1.5),
    }
 
    # Populate parameter lims with defaults, skipping time_evo and spectrum
    skip_keys = {'time_evo', 'spectrum'}
    plims = {k: default_plims[k] for k in active_maps if k not in skip_keys and k in default_plims}
 
    if parameter_lims is not None:
        plims.update(parameter_lims)
 
    # 3) Supply maps and limits to STRAUSS' Objects source
    sources = Objects(maps.keys())
    sources.fromdict(maps)
    sources.apply_mapping_functions(map_lims=mlims, param_lims=plims)
 
    # 4) Set up the Spectralizer generator
    generator = Spectralizer()
    generator.modify_preset({
        'min_freq': min_freq,
        'max_freq': max_freq,
        'interpolation_type': interp_type,
        'regen_phases': regen_phases,
        'fit_spec_multiples': fit_spec_multiples,
        'equal_loudness_normalisation': equal_loudness,
    })
 
    # A quality of life feature if you're ever using the cutoff function
    if 'cutoff' in active_maps:
        generator.modify_preset({'filter': 'on'})
 
    # 5) Build and render the sonification
    soni = Sonification(score, sources, generator, system)
    soni.render()
 
    return soni
 