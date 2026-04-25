# ========================================================================
# Hidden functions come first - the first being a check for a valid note 
# and the second being a progression builder for note collections of more 
# than one note (e.g. chords, scales)
# ========================================================================

def _parse_note(rootnote):
    """
    Hidden function that validates and parses a root note string into its components.

    Inputs:
    rootnote (str):
        The desired note in scientific notation (e.g. 'C4', 'A#3')

    Outputs:
    rootnote (str):
        The validated and normalised note string
    Root (str):
        The note letter (e.g. 'C', 'A#')
    Octave (int):
        The octave number
    """

    #Check if there's no letter, and if so get grumpy and throw an error.
    if not any(c.isalpha() for c in rootnote):
        raise ValueError(f"Chord requires a musical note to generate you a chord"
                         f"Please supply a letter from A-G, with or without the sharp (#)")
    # If there's a letter but no number is supplied, they get the 4th Octave
    elif not any(c.isdigit() for c in rootnote):
        rootnote+='4'

    # Break the root note in parts - the root note and the octave
    Root = ''.join(filter(str.isalpha, rootnote))
    Octave = int(''.join(filter(str.isdigit, rootnote)))

    #Make upper case if not already
    Root = Root.upper()

    rootnote = Root+str(Octave)

    return rootnote, Root, Octave




def _build_prog(rootnote, prog,max_notes=None):
    """
    Hidden function that builds a note progression from a root note and a
    list of semitone steps.

    Inputs:
    rootnote (str):
        The root note in scientific notation (e.g. 'C4')
    prog (list):
        List of semitone intervals from the root note
    max_notes (int)
        The number of notes in a progression you want to keep. Select None if you want the whole scale

    Outputs:
    notes (list):
        Nested list of note strings in STRAUSS-safe format
    """
    
    # for lookups, it's easier to just have a solid stave
    stave = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    # Validate root note and break it into it's note and octave
    rootnote, Root, Octave = _parse_note(rootnote)

    #Find where the note is in the stave
    index_root = stave.index(Root)
    
    # Initialise note progression
    notes = [rootnote]

    if max_notes is not None:
        prog = prog[:max_notes-1]

    #populate progression using prog dictionary
    for step in prog:

        #calculate octave based on whether we have stepped up from one octave 
        # to another using int part division
        octave_note = Octave + (index_root + step) // len(stave)

        # Use clock arithmetic to select index inside of stave
        ind_use = (index_root + step) % len(stave)

        #Append progression with note from stave attached to octave
        notes.append(stave[ind_use] + str(octave_note))
    
    return [notes]

# ============================================================================
# The next functions are used to generate a series of notes in a given series 
# - either lone note, chord or scale
#============================================================================

def note(rootnote = 'C4'):
    """
    A simple function that takes an inputted note and converts it to a
    STRAUSS-safe note.

    Inputs:
    rootnote (str):
        The desired note in scientific notation (e.g. 'C4', 'a#3')

    Outputs:
    note (list):
        Nested list containing the validated note string
    """

    # Use the common parser of making sure life is good and the note is of the right format
    rootnote,_,_ = _parse_note(rootnote)

    return [[rootnote]]
    


def chord(rootnote = 'C4',chord = 'major'):
    """
    Generates a chord from a root note and chord type.

    Inputs:
    rootnote (str):
        The root note in scientific notation (e.g. 'C4')
    chord (str):
        The chord type to generate. Options: 'major', 'minor'
    max_notes (int)
        The number of notes in a scale you want to keep. Select None if you want the whole scale

    Outputs:
    chord (list):
        Nested list of note strings forming the chord in STRAUSS-safe format
    """

    #Define tone and semitone climbs for each kind of scale in progression dictionary
    progression = {'major':[4,7],'minor':[3,7]}

    if chord not in progression:
        raise ValueError(f"Unknown scale type: {chord}")
    
    # STRAUSS needs a nested list, so that's what we'll output
    return _build_prog(rootnote,progression[chord])


def scale(rootnote = 'C4',scale = 'major',max_notes = None):
    """
    Generates a scale from a root note and scale type.

    Inputs:
    rootnote (str):
        The root note in scientific notation (e.g. 'C4')
    scale (str):
        The scale type to generate. Options: 'major', 'minor'
    max_notes (int)
        The number of notes in a scale you want to keep. Select None if you want the whole scale

    Outputs:
    scale (list):
        Nested list of note strings forming the scale in STRAUSS-safe format
    """

    #Define tone and semitone climbs for each kind of scale in progression dictionary
    progression = {'major':[2,4,5,7,9,11,12],'minor':[2,3,5,7,8,10,12],
                   'pentatonic major': [2, 4, 7, 9, 12]}

    if scale not in progression:
        raise ValueError(f"Unknown scale type: {scale}")
    
    # STRAUSS needs a nested list, so that's what we'll output
    return _build_prog(rootnote,progression[scale],max_notes)




def transpose(notes, shift):
    """
    Transposes a series of notes by a given number of semitones.

    Inputs:
    notes (list):
        A list of note strings to transpose (e.g. ['C4', 'E4', 'G4']).
        Also accepts nested lists from other ICE functions (e.g. [['C4', 'E4', 'G4']])
    shift (int):
        Number of semitones to shift by. Positive = up, negative = down.

    Outputs:
    transposed (list):
        Nested list of transposed note strings in STRAUSS-safe format
    """

    # for lookups, it's easier to just have a solid stave
    stave = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    # If we've been handed a nested list from another ICE function, flatten it
    if any(isinstance(i, list) for i in notes):
        notes = notes[0]

    # Initialise transposed note list
    transposed = []

    for n in notes:
        # Pop open the note into its root and octave
        _, Root, Octave = _parse_note(n)

        # Find where we are in the stave
        index = stave.index(Root)

        # Use clock arithmetic to find the new note and integer division for the octave
        new_note = stave[(index + shift) % len(stave)] + str(Octave + (index + shift) // len(stave))

        # Add to our transposed collection
        transposed.append(new_note)

    # STRAUSS needs a nested list, so that's what we'll output
    return [transposed]