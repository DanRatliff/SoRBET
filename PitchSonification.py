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

    # selecting our parameters to map, we need to use lists which are the same length
    # as the number of notes - this is why we have four elements in the pitch array
    # and *4 for time_evo and cutoff
    maps = {'pitch': [0], #set up base pitch with an array the same length as our data
            'time_evo': time_data, #map time array of light curve to time in sonification
            'pitch_shift': pitch_data} #map flux to pitch_shift

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
    
    return soni