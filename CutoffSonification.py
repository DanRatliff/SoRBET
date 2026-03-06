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
    NoNotes = len(notes)

    maps = {
        'pitch': np.linspace(0,NoNotes-1,num=NoNotes,endpoint=False),
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