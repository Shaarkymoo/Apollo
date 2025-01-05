import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
import pprint
import os
import ast
import time
import re
import shutil


def connection():
    client_id = '19e36aafa5484d948f5d1e99f0aadbe8'
    client_secret = '97375cc65bae4d14afb6b55e74245f17'

    sp_oauth = SpotifyOAuth(client_id=client_id,client_secret=client_secret,redirect_uri='http://localhost:8888/callback',scope='user-library-read')
    #print(sp_oauth)

    #auth_manager = spotipy.oauth2.SpotifyClientCredentials(client_id=client_id,client_secret=client_secret)

    access_token = sp_oauth.get_access_token
    #print(access_token)

    sp = Spotify(auth_manager=sp_oauth)
    #print(sp)

    return sp

def searchForTrack(spotify,query):
    results = spotify.search(q=query,type='track')
    with open('songbpm.txt','w',encoding='utf8') as box:
        box.writelines(results['tracks']['items'][0]['id'])

    # artists = ""
    # for a in (results['tracks']['items'][0]['album']['artists']):
    #     #print()
    #     #for b in (a['album']['artists']):
    #     artists = artists + (a['name']) + ", "
    #     #print(artists)
    # artists = artists.rstrip(', ')
    # return artists

    # track_deets = sp.audio_features(tracks=[track['id']])
    # pprint.pprint(track_deets)

    return (results['tracks']['items'][0]['id'])

# results = sp.current_user_saved_tracks(limit = 50,offset=20)
# for idx, item in enumerate(results['tracks']):
#     track = item['track']
#     #print(idx, track['artists'][0]['name'], " – ", track['name'])

# #pprint.pprint(track)

# track_deets = sp.audio_features(tracks=[track['id']])
# pprint.pprint(track_deets)

# print(results['tracks']['items'][0]['album']['artists'][0]['name'],results['tracks']['items'][0]['album'])

def getsongs():
    list = os.listdir(r'E:\Shaarav\music/')
    print(len(list))
    with open('origsong.txt','w',encoding='utf8') as box:
        for a in list:
            a = a.replace('.mp3','')
            box.write(a)
            box.write('\n')

def writesongs():
    with open('origsong.txt','r',encoding='utf8') as box:
        list = box.readlines()
        list2=[]
        for a in list:
            a=a.rstrip('\n')
            list2.append(a)
        #print(list2)

    sp=connection()
    list3 = []
    for a in list2:
        #print(a)
        time.sleep(1)
        #print(a)
        b = searchForTrack(sp,a)
        list3.append(b)
    
    #print('done')
    #print(list3)
    
    with open('searchresults.txt','w',encoding='utf8') as box:
        for a in list3:
            box.write(a)
            box.write('\n')
    
    return list3

def getbpms():
    with open('searchresults.txt','r',encoding='utf8') as box:
        list = box.readlines()
        list2=[]
        for a in list:
            a=a.rstrip('\n')
            list2.append(a)
        #print(list2)
        box.close()
    
    sp = connection()
    list3 =[]
    for a in list2:
        result = sp.audio_features(tracks=[a])
        #print(result)
        list3.append(result)
        time.sleep(1)
    
    with open('bpms.txt','w',encoding='utf8') as box:
        for a in list3:
            box.write(str(a))
            box.write('\n')

    return list3
    #print(max(list3))
    #print(min(list3))

def getAllSongs():
    with open('origsong.txt','r',encoding='utf8') as box:
        list = box.readlines()
        list2=[]
        for a in list:
            a=a.rstrip('\n')
            list2.append(a)
    return list2

def songdictget():
    with open('bpms.txt','r',encoding='utf8') as box2, open('origsong.txt','r',encoding='utf8') as box1:
        songlist = box1.readlines()
        bpmlist = box2.readlines()

        dict1 = {}
        for i in range(0,len(songlist)):
            dict1[(songlist[i].rstrip('\n'))] = (bpmlist[i].rstrip('\n'))
        return dict1

#songlist = getAllSongs()
#print("got all songs")
#urlList = writesongs()
#print("found all urls")
#bpmsList = getbpms()
#print("got all bpms")


def filter():
    songdict = songdictget()
    #print(len(songdict))
    for a in songdict:
        #print(a,songdict[a])
        break

    low_valence = {}
    mid_low_valence = {}
    mid_mid_valence = {}
    mid_high_valence = {}
    high_valence = {}

    for a in songdict:
        songdeets = ast.literal_eval(songdict[a])
        songdeets = songdeets[0]
        #print(songdeets)
        if songdeets['valence']<=0.20:
            low_valence[a] = songdict[a]
        elif songdeets['valence']<=0.40:
            mid_low_valence[a]=songdict[a]
        elif songdeets['valence']<=0.60:
            mid_mid_valence[a]=songdict[a]
        elif songdeets['valence']<=0.80:
            mid_high_valence[a]=songdict[a] 
        else:
            high_valence[a]=songdict[a]
    

    #print(len(low_valence))                 #74
    #print(len(mid_low_valence))             #241
    #print(len(mid_mid_valence))             #297 
    #print(len(mid_high_valence))            #242 
    #print(len(high_valence))                #100
    playlists = [low_valence,mid_low_valence,mid_mid_valence,mid_high_valence,high_valence]
    playlistsNames = ['slow','mid_low_valence','balanced','upper mediocre','ecstasy']

    folders = ['everything/']

    for a in playlists:
        #print(a)
        for b in a:
            print(b)
            for c in folders:
                try:
                    oldAddress = 'E:/Shaarav/music/' + str(b) + '.mp3'
                    newAddress = 'E:/Shaarav/playlists/' + playlistsNames[playlists.index(a)] + '/' + str(b) + '.mp3'
                    #print(oldAddress)
                    #print(newAddress)
                    shutil.copy(oldAddress,newAddress)
                    os.remove(oldAddress)
                except Exception as e:
                    print(e)
                    pass


#print("songlist length = ", len(songlist))
#print("urlList length = ", len(urlList))
#print("bpmList length = ", len(bpmsList))
#print(songlist[949],"\t,",urlList[949],"\t,",bpmsList[949])

# categories = ['danceability','energy','key','loudness','mode','speechiness','acousticness','instrumentalness','liveness','liveness','valence','tempo']

# # print(len(low_energy_low_valence))   #69
# # print(len(low_energy_high_valence))  #32
# # print(len(high_energy_low_valence))  #402
# # print(len(high_energy_high_valence)) #451

# #print(len(low_valence))  #217
# #print(len(mid_valence))  #473
# #print(len(high_valence)) #264



# for a in high_valence:
#     new_address = a + '.mp3'
#     list1 = os.listdir('E:/Shaarav/playlists/high_valence')
#     #print(list1[5])
#     if new_address not in list1:
#         print(a)

if True:
    getsongs()
    print("done1")
    writesongs()
    print("done2")
    getbpms()
    print("done3")
    filter()
    print("done4")

 
 