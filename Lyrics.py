import lyricsgenius
import eyed3
import musixmatch
from pprint import pprint
import os

def genius_setup(): 
    client_id = 'FYST0CoaHDYMbCMzDsbM2ze6lHCBD7nl5X3IknYGsSmWj3nvgLdLjBaCKpaWLBRE'
    client_secret = 'O9R4odQExaVokhgEDT6-bnEHO79JJdcrzoknYnv3L0k8d0Ryr3WuwfXK7fRpq2q2jfZ_zqywfDM-7LdPhLBkLQ'
    client_token = 'mF3AF4cXWIi-jKzvn8pUyXGMOtVgXqlTmF-gO7Ax72pSssZZTVViwxWKML0y_FCM'

    genius = lyricsgenius.Genius(client_token)
    genius.verbose = False # Turn off status messages
    genius.remove_section_headers = False # Remove section headers (e.g. [Chorus]) from lyrics when searching
    genius.skip_non_songs = True # Include hits thought to be non-songs (e.g. track lists)
    #genius.excluded_terms = ["(Remix)", "(Live)"] # Exclude songs with these words in their title
    genius.response_format = 'plain'
    return genius

def musixmatch_setup():
    apikey = '8878031489eee173a7cdf0fcb909b869'
    return

def search_lyrics(object,query):
    #searchquery = str(input(query))
    song = object.search_song(query)
    #print(song.lyrics)
    return song

def update_songs():
    loc = 'E:\\Shaarav\\playlists\\old rock\\'
    songlist = []
    errors = []
    for a in os.listdir(loc):
        a = a.replace('.mp3','')
        songlist.append(a)
        print(a)
        try:
            song_object = search_lyrics(genius_setup(), a)
            #print(song_object)
            songfile = eyed3.load(loc+a+'.mp3')
            if songfile.tag is None:
                songfile.initTag()
            songfile.tag.lyrics.set(song_object.lyrics)
            songfile.tag.save()
        except Exception as e:
            print(e)
            errors.append(a)
    print("loop is done \n\n\n ")
    print(errors)
    return a


#print("start")
#test_1 = search_lyrics(genius_setup(), update_songs())
#print("searched")
#pprint(vars(test_1))
#print(test_1.lyrics)

update_songs()

