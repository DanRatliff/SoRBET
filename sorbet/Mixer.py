#For later audio processing, we import Audio, and install + import pydub
import os
from IPython.display import Audio, display as ipy_display
from pydub import AudioSegment

def combine_audio(AudioList,filename = "CombinedAudio",show = True):

    #Initialise the combined file as None and set up the temorary file name for the audio files we process
    combined = None
    for nn in AudioList:
        
        nn.save('audiotrack.wav')

        # Load your two files
        track = AudioSegment.from_wav('audiotrack.wav')
        
        # Overlay them (mix together, starting at the same time)
        if combined is None:
            combined=track
        else:
            combined = combined.overlay(track)
    
    #Now we're done, delete audiotrack.wav
    if os.path.exists('audiotrack.wav'):
        os.remove('audiotrack.wav')

    # Export
    combined.export(filename+".wav", format="wav")

    if show:
    # If you've saved to file
        print('Below is the combined sound file of both sonifications to make a combined experience!')
        ipy_display(Audio(filename+".wav"))
        

def make_stereo(left_soni,right_soni,filename='StereoAudio',show=True):
    
    left_soni.save('left.wav')
    right_soni.save('right.wav')
    
    left_audio = AudioSegment.from_wav("left.wav")
    right_audio = AudioSegment.from_wav("right.wav")

    stereo_sound = AudioSegment.from_mono_audiosegments(left_audio, right_audio)

    stereo_sound.export(filename+".wav", format="wav")

    # Clean up the temp left and right audio files
    os.remove('left.wav')
    os.remove('right.wav')

    if show:
    # If you've saved to file
        print('Below is the combined stereo sound file of both sonifications to make a combined experience!')
        ipy_display(Audio(filename+".wav"))