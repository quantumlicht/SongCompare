import os
import sys
import re
from time import time
import logging
from collections import Counter

SUPPORTED_EXTENSIONS = ['mp3', 'm4a', 'wav', 'wma', 'flac']
LOG_FILENAME = 'report.log'

log = logging.getLogger()


def set_logger(filename=None, level=None):
    filename = filename or'log.log'
    level = level or 'INFO'

    format = ("%(asctime)s [%(levelname)-5s] | %(message)s")

    # create the log directory if it doesn't exist
    # if filename and not os.path.exists(os.path.dirname(filename)):
    #     os.makedirs(os.path.dirname(filename))

    logging.basicConfig(level=getattr(logging, level),
                        format=format,
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename=filename,
                        filemode='w')


class Duplicates(object):
    '''
    Store Duplicates in an array
    '''
    def __init__(self):
        self.artist = ''
        self.songs = []
        self.sizes = []
        self.folders = []
        self.paths = []


class Song():
    '''
    Store properties for a song
    '''
    def __init__(self):
        self.artist = ''
        self.name = ''
        self.size = 0
        self.folder = ''
        self.path = ''
        self.extension = ''


class SongLibrary(object):

    def __init__(self, musicDir):
        self.rootMusicDir = musicDir
        self.supported_extensions = SUPPORTED_EXTENSIONS
        self.library = []
        self.nb_songs = 0
        self.nb_duplicates = 0
        self.duplicates = []
        self.dupByArtist = Counter()

    def getSongs(self):
        self.__getSongs(self.rootMusicDir)
        self.nb_songs = len(self.library)

    def __getSongs(self, musicDir):

        musicDir = os.path.abspath(musicDir)

        filesInCurDir = os.listdir(musicDir)

        for file in filesInCurDir:

            curFile = os.path.join(musicDir, file)

            if os.path.isfile(curFile):
                curFileExtension = curFile[-3:]

                if curFileExtension in self.supported_extensions:
                    self.nb_songs += 1

                    # We add to a list all the files that contain
                    split_path = (os.path.abspath(curFile)).split('\\')
                    base_path = [x for x in split_path if x not in self.rootMusicDir.split('\\')]

                    song = Song()
                    song.size = float(os.stat(curFile).st_size / 1024)  # in KB
                    song.path = base_path
                    song.extension = curFileExtension
                    song.artist = base_path[0]
                    song.name = base_path[-1]

                    try:
                        song.folder = base_path[-2]
                    except:
                        song.folder = 'ROOT_FOLDER'

                    self.library.append(song)
            else:
                self.__getSongs(curFile)

    def getDuplicates(self):
        self.__getDuplicates(self.library)
        self.__listDuplicatesByArtist()

    def __getDuplicates(self, songLibrary):
        progress = 0
        log.info("%s files to process" % self.nb_songs)
        while songLibrary:
            # Remove processed song
            song = songLibrary.pop(0)

            song_name = song.name
            song_folder = song.folder
            artist = song.artist
            song_size = song.size
            cleaned_song_name = re.sub("^[\d]{2}", '', song_name)
            song_path = ('/').join(song.path)

            for index, song__toCompare in enumerate([x for x in songLibrary if x.artist == artist]):

                song_name_to_compare = song__toCompare.name
                song_folder_to_compare = song__toCompare.folder
                song_size_to_compare = song__toCompare.size
                song_path_to_compare = ('/').join(song__toCompare.path)

                if song_name_to_compare.find(cleaned_song_name) != -1:
                    dup = Duplicates()
                    dup.artist = artist
                    dup.songs = [song_name, song_name_to_compare]
                    dup.sizes = [song_size, song_size_to_compare]
                    dup.folders = [song_folder, song_folder_to_compare]
                    dup.paths = [song_path, song_path_to_compare]

                    self.duplicates.append(dup)
                    self.nb_duplicates += 1

            progress += 1  # songs processed so far. to be used as a counter

        print('%s duplicates found' % self.nb_duplicates + '\n')

    def __listDuplicatesByArtist(self):
        dups_dict = {}

        for dup in self.duplicates:
            self.dupByArtist[dup.artist] += 1
            if dups_dict.get(dup.artist, None):
                dups_dict[dup.artist].append(dup)
            else:
                dups_dict[dup.artist] = [dup]

        print self.dupByArtist
        for k, v in self.dupByArtist.items():
            log.info('\n' + '='*250)
            log.info(k.upper())
            for dup in dups_dict[k]:
                log.info((dup.sizes, dup.paths))


if __name__ == "__main__":

    set_logger(filename=LOG_FILENAME, level='INFO')

    rootdir = sys.argv[1]

    # Benchmark time to process
    startTime = time()

    # Get list of files
    SongLib = SongLibrary(rootdir)
    SongLib.getSongs()
    SongLib.getDuplicates()

    print('Runtime: %2.2f' % (time() - startTime))
