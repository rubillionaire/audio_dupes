# given a directory to inspect, duplicate
# mp3 and m4a files are flagged for deletion
# based on their bitrate. Metadata for the
# highest bitrate file is untouched.

# started writing this using hsaudiotag
# thinking I could write tags with it, but
# its read only. So mutagen was pulled in
# to do the writing.

from difflib import SequenceMatcher as sm
from datetime import datetime as dt
import os
import sys

from hsaudiotag import auto

from mutagen.easyid3 import EasyID3
from mutagen.easymp4 import EasyMP4
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4

def audio_dict(audio_dir):
    """
    Takes in a string that represents thefile directory
    that will be inspected for MP3 and M4A files.
    
    Returns a dictionary. The key of the dictionary is
    an Artist. The value is another dictionary, whose
    key is the Album title, and value is a dictionary
    of songs. Each song dictionary is key'ed by its name,
    and its value is a list of the songs that were considered
    duplicates as a list. The song list object has dictionaries
    of each song, include keys for bitrate, path, and file type.
    """
    audio_dict = {}
    
    for root, dirs, files in os.walk(audio_dir):
        for name in files:
            if (name.split(".")[-1].lower() == 'm4a' or \
                name.split(".")[-1].lower() == 'mp3'):
                
                cur_path = "{0}/{1}".format(root, name)
                cur_file = auto.File(cur_path)
                
                artist = cur_file.artist.lower().strip()
                album = cur_file.album.lower().strip()
                title = cur_file.title.lower().strip()
                bitrate = cur_file.bitrate
                
                if not artist in audio_dict:
                    audio_dict[artist] = {}
                
                if not album in audio_dict[artist]:
                    audio_dict[artist][album] = {}
                
                title_key = title
                for in_album_title in audio_dict[artist][album]:
                    if sm(None, title, in_album_title).ratio() > 0.8:
                        title_key = in_album_title
                
                if not title_key in \
                    audio_dict[artist][album]:
                    audio_dict[artist][album][title_key] = []
                
                audio_dict[artist][album][title_key].append({
                    'path': cur_path,
                    'bitrate': cur_file.bitrate,
                    'type': name.split(".")[-1].lower()
                })
                
    return audio_dict

def flag(audio_dict, delete_flag):
    """
    Is passed a dictionary of all artists, albums, and songs.
    Iterates through the audio dictionary looking for every title
    that has two files, it compares the bitrate of the two files.
    The lesser of the two files will have have a metadata field
    changed to include a delete string, which can be filtered for
    in an iTunes smart playlist.
    MP3 delete flag will be in the "composer" field.
    M4A delete flag will be in the "comment" field.
    
    Returns list of flagged song dictionaries.
    """
    flagged = []
    for artist in audio_dict:
        for album in audio_dict[artist]:
            for songlist in audio_dict[artist][album]:
                if len(audio_dict[artist][album][songlist]) > 1:
                    
                    # track the song that wont be deleted
                    song_to_keep = {}
                    # track bitrate through songlist
                    highest_bitrate = 0
                    # find the highest bitrate
                    for song in audio_dict[artist][album][songlist]:
                        if song['bitrate'] > highest_bitrate:
                            highest_bitrate = song['bitrate']
                            song_to_keep = song
                    # flag files for deletion        
                    for song in audio_dict[artist][album][songlist]:
                        if song != song_to_keep:
                            set_flag(song, delete_flag)
                            flagged.append(song)
        
    return flagged

def set_flag(song, delete_flag):
    """
    called in order to set the delete flag on a song.
    gets both the song element from the audio_dict
    and the delete_flag
    """
    if song['type'] == "mp3":
        cur_song = EasyID3(song['path'])
        cur_song['composer'] = delete_flag
    elif song['type'] == "m4a":
        cur_song = EasyMP4(song['path'])
        cur_song['comment'] = delete_flag
    
    cur_song.save()
    
def assert_flags(flagged):
    """
    Asserts that duplicates now have the correct metadata.
    The comment field of the MP3's should start with "dupedelete_"
    The composer field of the M4A's should start with "dupedelete_"
    """
    for song in flagged:
        if song['type'] == 'mp3':
            cur_song = EasyID3(song['path'])
            assert cur_song['composer'][0].startswith('dupedelete')
        elif song['type'] == 'm4a':
            cur_song = EasyMP4(song['path'])
            assert cur_song['comment'][0].startswith('dupedelete')
    return 1

def main():
    """gets the party started"""
    
    if len(sys.argv) == 2:
        audio_dir = sys.argv[1]
    else:
        return "Expected file path to audio directory."
    
    delete_flag = u"dupedelete_{0}".format(dt.now().isoformat())
    
    audio = audio_dict(audio_dir)
    flagged = flag(audio, delete_flag)
    
    assert_flags(flagged)
    
    print "{0} audio files".format(str(len(flagged))) +\
            " were flagged for deletion.\n" +\
            "{0}".format(delete_flag)

if __name__ == '__main__':
    main()