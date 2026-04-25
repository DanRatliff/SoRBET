
from strauss.sonification import Sonification
from strauss.sources import Objects, Events
from strauss.generator import Sampler, Synthesizer
from strauss.score import Score
import numpy as np
import os
import warnings

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES_PATH = os.path.join(PROJECT_ROOT, 'Samples', 'mallets')

def PitchSonification(notes, length, time_data, pitch_data,
                       time_lims=('0%', '100%'), pitch_lims=('0%', '100%'),
                       pitch_plims=(0, 12), system='mono', preset=None):
    """
    Create a pitch shift filter sonification.

    Parameters
    ----------
    notes : list
        Notes to use, e.g. [["E3"]].
    length : float
        Duration of the sonification in seconds.
    time_data : array-like
        Data mapped to time evolution.
    pitch_data : array-like
        Data mapped to the filter cutoff.
    time_lims : tuple, optional
        Mapping limits for time_evo.
    pitch_lims : tuple, optional
        Mapping limits for cutoff.
    pitch_plims : tuple, optional
        Parameter limits for cutoff (fraction of audible frequencies).
    system : str, optional
        Audio system: 'mono', 'stereo', '5.1', etc.
    preset : str, optional
        Generator preset to load, e.g. 'windy'.

    Returns
    -------
    soni : Sonification
        The rendered Sonification object.
    """

    score = Score(notes, length)
    NoNotes = len(notes[0])

    # selecting our parameters to map, we need to use lists which are the same length
    # as the number of notes - this is why we have four elements in the pitch array
    # and *4 for time_evo and cutoff
    maps = {'pitch': list(range(NoNotes)), #set up base pitch with an array the same length as our data
            'time_evo': [time_data]*NoNotes, #map time array of light curve to time in sonification
            'pitch_shift': [pitch_data]*NoNotes} #map flux to pitch_shift

    # Here we set up our mapping limits, we want the time to go over 100% so the last note has time to play
    lims = {'time_evo': time_lims,
        'pitch_shift': pitch_lims} #use 100% of data range for the pitch mapping

    # here we are using default pitch shift range of 2 octaves but we can change this
    # by introducing a parameter limits dictionary. Here we can define the pitch_shift
    # limits we want in semiquavers (there are 12 semiquavers in an octave)
    plims = {'pitch_shift': pitch_plims}

    # Set up sources! This time we specify the Objects child class
    sources = Objects(maps.keys())
    sources.fromdict(maps)

    # Now we apply mapping functions, including our parameter limits this time:
    sources.apply_mapping_functions(map_lims = lims, param_lims = plims)

    # Choosing the Synthesizer generator:
    generator = Synthesizer()

    # load the pitch_mapper preset
    generator.load_preset('pitch_mapper')

    # call score, sources, generator and audio system (channels) to combine the modules
    soni = Sonification(score, sources, generator, system)
    soni.render()

    return soni



def CutoffSonification(notes, length, time_data, cutoff_data,
                       time_lims=('0%', '100%'), cutoff_lims=('0%', '100%'),
                       cutoff_plims=(0, 0.95), system='mono', preset=None):
    """
    Create a cutoff filter sonification.

    Parameters
    ----------
    notes : list
        Notes to use, e.g. [["E3"]].
    length : float
        Duration of the sonification in seconds.
    time_data : array-like
        Data mapped to time evolution.
    cutoff_data : array-like
        Data mapped to the filter cutoff.
    time_lims : tuple, optional
        Mapping limits for time_evo.
    cutoff_lims : tuple, optional
        Mapping limits for cutoff.
    cutoff_plims : tuple, optional
        Parameter limits for cutoff (fraction of audible frequencies).
    system : str, optional
        Audio system: 'mono', 'stereo', '5.1', etc.
    preset : str, optional
        Generator preset to load, e.g. 'windy'.

    Returns
    -------
    soni : Sonification
        The rendered Sonification object.
    """
    score = Score(notes, length)
    NoNotes = len(notes[0])

    maps = {
        'pitch': list(range(NoNotes)),
        'time_evo': [time_data]*NoNotes,
        'cutoff': [cutoff_data]*NoNotes
    }

    lims = {
        'time_evo': time_lims,
        'cutoff': cutoff_lims
    }

    plims = {'cutoff': cutoff_plims}

    sources = Objects(maps.keys())
    sources.fromdict(maps)
    sources.apply_mapping_functions(map_lims=lims, param_lims=plims)

    generator = Synthesizer()
    generator.modify_preset({'filter': 'on'})

    if preset:
        generator.load_preset(preset)

    soni = Sonification(score, sources, generator, system)
    soni.render()

    return soni

def PanSonification(notes, length, time_data, pan_data,
                       time_lims=('0%', '100%'), pan_lims=('0%', '100%'),
                       pan_plims=(0, 0.95), system='stereo', preset=None):
    """
    Create a left-right panning sonification.

    Parameters
    ----------
    notes : list
        Notes to use, e.g. [["E3"]].
    length : float
        Duration of the sonification in seconds.
    time_data : array-like
        Data mapped to time evolution.
    pan_data : array-like
        Data mapped to the left-right panning.
    time_lims : tuple, optional
        Mapping limits for time_evo.
    pan_lims : tuple, optional
        Mapping limits for panning.
    pan_plims : tuple, optional
        Parameter limits for panning (fraction of audible frequencies).
    system : str, optional
        Audio system: 'mono', 'stereo', '5.1', etc.
    preset : str, optional
        Generator preset to load, e.g. 'windy'.

    Returns
    -------
    soni : Sonification
        The rendered Sonification object.
    """
    score = Score(notes, length)
    NoNotes = len(notes[0])

    #We add a function here
    time_data, pan_data = _DensifyPanData(time_data,pan_data,length)

    maps = {
        'pitch': list(range(NoNotes)),
        'time_evo': [time_data]*NoNotes,
        'azimuth': [pan_data]*NoNotes,
          'polar': [0.5]*NoNotes #setting a constant polar coordinate which is level with the listener
    }

    lims = {
        'time_evo': time_lims,
        'pan': pan_lims
    }

    plims = {}

    sources = Objects(maps.keys())
    sources.fromdict(maps)
    sources.apply_mapping_functions(map_lims=lims, param_lims=plims)

    generator = Synthesizer()
    generator.modify_preset({'filter': 'on'})

    if preset:
        generator.load_preset(preset)

    soni = Sonification(score, sources, generator, system)
    soni.render()

    return soni



def PitchEventSonification(notes, length, time_data, pitch_data,
                       time_lims=('0%', '101%'), pitch_lims=('0%', '100%'),
                         system='mono', preset='staccato',downsample = 60):

    score = Score(notes, length)

    # selecting our parameters to map, we need to use lists which are the same length
    # as the number of notes - this is why we have four elements in the pitch array
    # and *4 for time_evo and cutoff
    maps = {'pitch': pitch_data,
          'time': time_data
          }

    # Here we set up our data limits, we want the time to go over 100% so the last note has time to play
    lims = {'time': time_lims,
          'pitch': pitch_lims}

    # Set up sources! This time we specify the Objects child class
    sources = Events(maps.keys())
    sources.fromdict(maps)

    # Now we apply mapping functions, including our parameter limits this time:
    sources.apply_mapping_functions(map_lims = lims)

    # choose the synthesizer generator:
    generator = Sampler(sampfiles =SAMPLES_PATH)   
    generator.load_preset(preset)

    #call score, sources, generator and audio system (channels) to combine the modules
    soni = Sonification(score, sources, generator, system)
    soni.render(downsamp=downsample)

    return soni

def _DensifyPanData(time_data, pan_data, sonification_length,
                   max_dtheta_per_sec=0.5, max_iter=3):
    """
    Densify (time_data, pan_data) by inserting samples wherever the
    rate of pan change per audio-second exceeds max_dtheta_per_sec.
    Preserves the original signal shape; only adds samples where
    STRAUSS would otherwise struggle to render a smooth pan.

    The threshold is defined in audio-time rather than data-time, so
    the protection scales correctly regardless of sonification length.

    Parameters
    ----------
    time_data : array-like
        Original time array (monotonically increasing).
    pan_data : array-like
        Pan values in [0, 1] aligned with time_data.
    sonification_length : float
        Duration of the rendered audio in seconds.
    max_dtheta_per_sec : float, optional
        Maximum permitted |Δpan| per audio-second. Values much above
        ~5 approach the limit of perceptible smooth panning.
    max_iter : int, optional
        Safety cap on bisection passes.

    Returns
    -------
    time_out : ndarray
        Regridded (denser) time array.
    pan_out : ndarray
        Pan values on the regridded time array.
    """
    time_data = np.asarray(time_data, dtype=float)
    pan_data = np.asarray(pan_data, dtype=float)

    if len(time_data) != len(pan_data):
        raise ValueError("time_data and pan_data must be the same length.")
    if len(time_data) < 2:
        raise ValueError("Need at least 2 samples to densify.")

    data_duration = time_data[-1] - time_data[0]
    if data_duration <= 0:
        raise ValueError("time_data must be strictly increasing.")

    if max_dtheta_per_sec > 5.0:
        warnings.warn(
            f"max_dtheta_per_sec={max_dtheta_per_sec} is approaching "
            f"the limit of perceptible smooth panning. Consider "
            f"lengthening the sonification or smoothing the input."
        )

    scale = sonification_length / data_duration

    t = time_data.copy()
    p = pan_data.copy()

    converged = False
    for _ in range(max_iter):
        dp = np.abs(np.diff(p))
        dt_audio = np.diff(t) * scale
        with np.errstate(divide='ignore', invalid='ignore'):
            rate = np.where(dt_audio > 0, dp / dt_audio, 0.0)

        if rate.max() <= max_dtheta_per_sec:
            converged = True
            break

        n_extra = np.ceil(rate / max_dtheta_per_sec).astype(int) - 1
        n_extra = np.clip(n_extra, 0, None)

        if n_extra.sum() == 0:
            converged = True
            break

        new_times = [t[0]]
        for i, n in enumerate(n_extra):
            if n > 0:
                extras = np.linspace(t[i], t[i+1], n + 2)[1:-1]
                new_times.extend(extras)
            new_times.append(t[i+1])
        t = np.asarray(new_times)
        p = np.interp(t, time_data, pan_data)

        #   Final check — verifies the last densification actually worked
    if not converged:
        dp = np.abs(np.diff(p))
        dt_audio = np.diff(t) * scale
        with np.errstate(divide='ignore', invalid='ignore'):
            rate = np.where(dt_audio > 0, dp / dt_audio, 0.0)
        if rate.max() > max_dtheta_per_sec:
            warnings.warn(
            f"DensifyPanData hit max_iter={max_iter} without converging "
            f"(final max rate = {rate.max():.3f} per audio-second). "
            f"Output may still contain artefacts."
            )

    return t, p