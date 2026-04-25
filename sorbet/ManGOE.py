from strauss.sonification import Sonification
from strauss.sources import Objects, Events
from strauss.generator import Synthesizer
from strauss.score import Score

import numpy as np

def ManGOE_Object(notes,length,Maps,map_lims = None,parameter_lims = None,preset = 'pitch_mapper',system = "mono"):

    """
    A consolidated STRAUSS sonification generator that generates an Object-class (i.e. continuous in time)
    source sonification from supplied maps, notes, duration and limits.
  
    ----------
    Inputs:
    ----------

    Maps (dict): 
    The key-data pairs used to map features of the sound to the prescribed dataset. 
    Keys include properties of the sound such as'volume', 'cutoff', 'pitch_shift','time_evo'.
    If 'time_evo' is not included, it is automatically generated within this function.
    Any key paired to None will be passed over in the function.
    All data must be of the same length or an exception will occur.

    notes (nested list): 
    The notes used by the sonification, in scientific notation.

    length (int): 
    Length (in seconds) of the produced sonification.

    map_lims (dict): 
    key - percentage limits which determine the permissible range of the data to be used, 
    in terms of the original data range.
    Supplied as ('0%','100%') for all mapped properties by default.

    parameter_lims (dict): 
    key - value pairs which determine the permissible range of the sound properties.
    Supplied as a set of defauls unless other limits passed into function.
    
    preset (str): 
    Preset to be used by STRAUSS' generator. 

    system (str): 
    The sound system used by the STRAUSS sonification generated (e.g. mono, stereo, DOLBY 5.1)

    ----------
    returns:
    ----------

    soni (object): the resulting STRAUSS sonification

   """


    # 1) Step up the STRAUSS score using the given notes and length of sonification
    score = Score(notes, length)

    # 2) Use the Maps input to dynamically build up the maps for this sonification

    # Start by determining active number of notes, which we'll need to mutliply the datasets by in the maps

    NoNotes = len(notes[0]) if isinstance(notes[0], list) else len(notes)

    # Then determine active maps from the input file - it checks for the presence of 
    # "parameter": data using k:v pattern, and will ignore it if a dataset is set to None

    active_maps = {k: v for k, v in Maps.items() if v is not None}

    # Error handling: if there are no maps, error out here
    if not active_maps:
        print(" No data mapped — stopping.")
        return None

    # If the time evolution is not in active maps, we add it.
    # As the time values themselves don't matter we just generate an arange which is the same length as the input data

    if 'time_evo' not in active_maps:
        dummy_data = next(v for v in active_maps.values())
        active_maps['time_evo'] = np.arange(len(dummy_data))

    #An error I often befall is a quirk of panning sonifications, which is that if polar is not set, 
    # then the default polar is zero, and then this leads to no panning at all! 
    # So we let ManGOE know we injected it ourselves with the polr_guard flag
    polar_guard = False
    if 'azimuth' in active_maps and 'polar' not in active_maps:
        dummy_data = next(v for v in active_maps.values())
        active_maps['polar'] = np.full(len(dummy_data), 0.5)
        polar_guard = True


    # Now we start initialising the maps, starting with pitch. We do this because ultimately each datastream needs 
    # multiplying by the number of notes in the notes selection

    maps = {'pitch': list(range(NoNotes)),}

    # Use the active maps to populate the remainder of the maps:
    for property, data in active_maps.items():
        maps[property] = [data] * NoNotes

 

    # 2a) We now set up the data limits of the maps. The strategy here
    # is to define 0%-100% defaults for the active maps, and replace any properties 
    # that are specified in the input using an update call.
    # As a consequence in cases where polar is inserted by us (polar_guard = True) 
    # we have to exclude it from these auto limits, else it gives a divide by zero error 
    # and STRAUSS dies

    mlims = {k: ('0%', '100%') for k in active_maps if not (k == 'polar' and polar_guard)}

    if map_lims is not None:

        mlims.update(map_lims)


    # 2b) Now we set the parameter limits in preparation of the generator, using almost the same approach.
    # We do however have to define a default parameter library and call from it, as it's not percentage based like the maps.

    default_plims = {
    'volume':           (0.05, 1.0),
    'cutoff':           (0.05, 0.95),
    'pitch_shift':      (-12, 12),
    'azimuth':          (0, 1),
    'volume_lfo/amount':(0, 1.5),
    }

    # Populate paramater lims with the above defaults, making sure we don't touch time_evo!
    plims = {k: default_plims[k] for k in active_maps if k != 'time_evo' and k in default_plims}

    if parameter_lims is not None:

        plims.update(parameter_lims)

    #3) We are now in a position to supply our maps and their limits to STRAUSS' source

    sources = Objects(maps.keys())
    sources.fromdict(maps)
    sources.apply_mapping_functions(map_lims=mlims, param_lims=plims)

    #4) We set up the generator and input the preset supplied

    generator = Synthesizer()
    generator.load_preset(preset)

    # A quality of life feature if you're ever using the cutoff function
    if 'cutoff' in active_maps:
        generator.modify_preset({'filter': 'on'})

    #5) We may now build and render the sonification - yippee! Hooray!
    soni = Sonification(score, sources, generator, system)
    soni.render()


    return soni


def ManGOE_Event(notes,length,Maps,map_lims = None,parameter_lims = None,preset = 'pitch_mapper',system = "mono",downsample=60):
 
    """
    A consolidated STRAUSS sonification generator that generates an Events-class (i.e. discrete in time)
    source sonification from supplied maps, notes, duration and limits.
  
    ----------
    Inputs:
    ----------
 
    Maps (dict): 
    The key-data pairs used to map features of the sound to the prescribed dataset. 
    Keys include properties of the sound such as 'volume', 'cutoff', 'pitch', 'time'.
    'time' is required for Events and defines when each event triggers within the sonification.
    Any key paired to None will be passed over in the function.
 
    notes (nested list): 
    The notes used by the sonification, in scientific notation.
    For Events, 'pitch' in Maps should map per-event data to these discrete notes.
 
    length (int): 
    Length (in seconds) of the produced sonification.
 
    map_lims (dict): 
    key - percentage limits which determine the permissible range of the data to be used, 
    in terms of the original data range.
    Supplied as ('0%','100%') for all mapped properties by default.

    NOTE: 'time' map_lims range must exceed 100% to avoid STRAUSS placing events
    at the very edges of the render window. If not, this function will enforce a
    default of ('0%','101%').
 
    parameter_lims (dict): 
    key - value pairs which determine the permissible range of the sound properties.
    Supplied as a set of defaults unless other limits passed into function.
    
    preset (str): 
    Preset to be used by STRAUSS' generator. 
 
    system (str): 
    The sound system used by the STRAUSS sonification generated (e.g. mono, stereo, DOLBY 5.1)
 
    ----------
    returns:
    ----------
 
    soni (object): the resulting STRAUSS sonification
 
   """
 
    # 1) Set up the STRAUSS score using the given notes and length of sonification
    score = Score(notes, length)
 
    # 2) Use the Maps input to dynamically build up the maps for this sonification
 
    # Filter out any None-valued mappings
    active_maps = {k: v for k, v in Maps.items() if v is not None}
 
    # Error handling: if there are no maps, error out here
    if not active_maps:
        print(" No data mapped — stopping.")
        return None
 
    # Events require a 'time' field — check it's present
    if 'time' not in active_maps:
        print(" Events sonification requires a 'time' key in Maps — stopping.")
        return None
    
    #An error I often befall is a quirk of panning sonifications, which is that if polar is not set, 
    # then the default polar is zero, and then this leads to no panning at all! 
    # So we let ManGOE know we injected it ourselves with the polr_guard flag

    polar_guard = False
    if 'azimuth' in active_maps and 'polar' not in active_maps:
        dummy_data = next(v for v in active_maps.values())
        active_maps['polar'] = np.full(len(dummy_data), 0.5)
        polar_guard = True
        
    # Build the maps dict. For Events, 'pitch' maps per-event data to the note selection
    maps = {}
    for property, data in active_maps.items():
        maps[property] = data
 
    # 2a) Set up map_lims with 0%-100% defaults, then apply user overrides
    # As a consequence in cases where polar is inserted by us (polar_guard = True) 
    # we have to exclude it from these auto limits, else it gives a divide by zero error 
    # and STRAUSS dies
    mlims = {k: ('0%', '100%') for k in active_maps if not (k == 'polar' and polar_guard)}
 
    if map_lims is not None:
        mlims.update(map_lims)
 
    # Safety step - Enforce that 'time' map_lims span more than 100% — if the range is <= 100%,
    # the event sonification will not render. To do so, define a quick function thet reads 
    # the percentage limits of an input

    def parse_percent(s):
        """Extract numeric value from a percentage string like '5%' or '-1%'."""
        return float(str(s).replace('%', ''))
    
    #Perform the actual check
    time_lo, time_hi = mlims['time']
    if parse_percent(time_hi)  <= 100.0:
        print(f" Warning: upper 'time' map_lims limit is <= 100%. STRAUSS requires >100%"
              f"Overriding to '101%' t o avoid STRAUSS failing to render.")
        mlims['time'] = (time_lo, '101%')
 
    # 2b) Set parameter limits from defaults, then apply user overrides
    default_plims = {
    'volume':           (0.05, 1.0),
    'cutoff':           (0.05, 0.95),
    'pitch_shift':      (0, 12),
    'azimuth':          (0, 1),
    'volume_lfo/amount':(0, 1.5),
    }
 
    # Populate parameter lims with defaults, skipping 'time'
    plims = {k: default_plims[k] for k in active_maps if k != 'time' and k in default_plims}
 
    if parameter_lims is not None:
        plims.update(parameter_lims)
 
    # 3) Supply maps and limits to STRAUSS' Events source
    sources = Events(maps.keys())
    sources.fromdict(maps)
    sources.apply_mapping_functions(map_lims=mlims, param_lims=plims)
 
    # 4) Set up the generator with the supplied preset
    generator = Synthesizer()
    generator.load_preset(preset)
 
    if 'cutoff' in active_maps:
        generator.modify_preset({'filter': 'on'})
 
    # 5) Build and render the sonification
    soni = Sonification(score, sources, generator, system)
    soni.render(downsamp=downsample)
 
    return soni