# given a directory to inspect and dupe directory, 
# duplicate mp3 and m4a files are moved to the 
# dupe directory based on their bitrate. Files with
# the highest bitrate are left untouched.

# started writing this using hsaudiotag
# thinking I could write tags with it, but
# its read only. So mutagen was pulled in
# to do the writing.

from difflib import SequenceMatcher as sm
from datetime import datetime as dt
import logging
import os
import sys
import shutil

from hsaudiotag import auto

class MoveDupes:
    def __init__(self, audio_dir, dupe_dir):
        self.audio_dict = {}
        self.moved = []
        self.dir = audio_dir
        self.dupe_dir = dupe_dir
        self.logger = self.config_logging()

    def map_audio(self):
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
        for root, dirs, files in os.walk(self.dir):
            for name in files:
                if (name.split(".")[-1].lower() == 'm4a' or \
                    name.split(".")[-1].lower() == 'mp3'):
                
                    cur_path = "{0}/{1}".format(root, name)
                    cur_file = auto.File(cur_path)
                
                    artist = cur_file.artist.lower().strip()
                    album = cur_file.album.lower().strip()
                    title = cur_file.title.lower().strip()
                    bitrate = cur_file.bitrate
                
                    if not artist in self.audio_dict:
                        self.audio_dict[artist] = {}
                
                    if not album in self.audio_dict[artist]:
                        self.audio_dict[artist][album] = {}
                
                    title_key = title
                    for in_album_title in self.audio_dict[artist][album]:
                        if sm(None, title, in_album_title).ratio() > 0.9:
                            title_key = in_album_title
                
                    if not title_key in \
                        self.audio_dict[artist][album]:
                        self.audio_dict[artist][album][title_key] = []
                
                    self.audio_dict[artist][album][title_key].append({
                        'path': cur_path,
                        'bitrate': bitrate,
                        'file_name': name
                    })
                
        return self

    def move(self):
        """
        Is passed a reference to the class in order to read the audio_dict
        of all artists, albums, and songs.
        Iterates through the audio dictionary looking for every title
        that has two files, it compares the bitrate of the two files.
        The lesser of the two files will be moved to the dupe directory.
    
        Returns list of moved song dictionaries.
        """
        for artist in self.audio_dict:
            for album in self.audio_dict[artist]:
                for songlist in self.audio_dict[artist][album]:
                    if len(self.audio_dict[artist][album][songlist]) > 1:
                    
                        # track the song that wont be deleted
                        song_to_keep = {}
                        # track bitrate through songlist
                        highest_bitrate = 0
                        # find the highest bitrate
                        for song in self.audio_dict[artist][album][songlist]:
                            if song['bitrate'] > highest_bitrate:
                                highest_bitrate = song['bitrate']
                                song_to_keep = song
                        # flag files for deletion        
                        for song in self.audio_dict[artist][album][songlist]:
                            if song != song_to_keep:
                                self._do_move(artist, album, song)
        
        return self
    
    def _do_move(self, artist, album, song):
        """
        Called in order to move a song to the dupe
        dir.
        """
        try:
            move_to = "{0}{1}/{2}/".format(self.dupe_dir, 
                                                artist, album)
            if not os.path.exists(move_to):
                os.makedirs(move_to)
                
            shutil.move(song['path'], move_to)
            self.moved.append(song)
            return 1
        except:
            self.logger.error("Could not move file: {0}".format(str(song['path'])))
            return 0

    def config_logging(self):
        """
        Sets up logging to track the files that have no ID3 tags
        or some other problem with mutagen that require them to be
        manually deleted.
        """
        logging.basicConfig(filename='move_dupes.log',
                            filemode='a',
                            format='%(asctime)s,%(msecs)d ' +\
                                    '%(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)
        logging.info("Running audio dupe mover")
    
        return logging.getLogger('move_dupes')

def main():
    """gets the party started"""
    
    if len(sys.argv) == 3:
        audio_dir = sys.argv[1]
        dupe_dir = sys.argv[2]
    else:
        return "Expected file path to audio directory, and dupe directory"
    
    fd = MoveDupes(audio_dir, dupe_dir)
    fd.map_audio().move()
    
    final_msg = "{0} audio files".format(str(len(fd.moved))) +\
            " were moved to the dupe dir:\n" +\
            "{0}".format(fd.dupe_dir)
    print final_msg
    fd.logger.info(final_msg)

if __name__ == '__main__':
    main()