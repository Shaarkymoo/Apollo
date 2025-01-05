import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
import pprint
import os
import ast
import time
import re
import csv
import shutil
import pandas

def connection():
    client_id = '19e36aafa5484d948f5d1e99f0aadbe8'
    client_secret = '97375cc65bae4d14afb6b55e74245f17'

    sp_oauth = SpotifyOAuth(client_id=client_id,client_secret=client_secret,redirect_uri='http://localhost:8888/callback',scope='user-library-read')
    #print(sp_oauth)

    #auth_manager = spotipy.oauth2.SpotifyClientCredentials(client_id=client_id,client_secret=client_secret)

    access_token = sp_oauth.get_access_token
    #print(access_token)

    sp = Spotify(auth_manager=sp_oauth,retries=0)
    #print(sp)

    return sp

def getTrackId(spotify,query):
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

def getsongs(path):
    list = os.listdir(path)
    print(len(list))
    with open(r"E:\Shaarav\energism\trackpaths.txt",'a',encoding='utf8') as box:
        for a in list:
            a = path + '/' + a
            box.write(a)
            box.write('\n')

    return

def writesongs():
    with open(r"E:\Shaarav\energism\trackList.txt",'r',encoding='utf8') as box:
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
        time.sleep(0.1)
        #print(a)
        b = getTrackId(sp,a)
        list3.append(b)
    
    #print('done')
    #print(list3)
    
    with open(r"E:\Shaarav\energism\trackIDs.txt",'w',encoding='utf8') as box:
        for a in list3:
            box.write(a)
            box.write('\n')
    
    return list3

def getbpms():
    with open(r"E:\Shaarav\energism\trackIDs.txt",'r',encoding='utf8') as box:
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
        print(a)
        result = sp.audio_features(track_id=a)
        #print(result)
        list3.append(result)
        time.sleep(1)
    
    with open(r"E:\Shaarav\energism\trackAnal.txt",'w',encoding='utf8') as box:
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
    with open(r"E:\Shaarav\energism\trackFeats.txt",'r',encoding='utf8') as box2, open(r"E:\Shaarav\energism\trackList.txt",'r',encoding='utf8') as box1:
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

#def datasetFilter():


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
        feature = 'speechiness'
        #print(songdeets)
        if songdeets[feature]<=0.20:
            low_valence[a] = songdict[a]
        elif songdeets[feature]<=0.40:
            mid_low_valence[a]=songdict[a]
        elif songdeets[feature]<=0.60:
            mid_mid_valence[a]=songdict[a]
        elif songdeets[feature]<=0.80:
            mid_high_valence[a]=songdict[a] 
        else:
            high_valence[a]=songdict[a]
    
                                            #valence
    print(len(low_valence))                 #106
    print(len(mid_low_valence))             #253
    print(len(mid_mid_valence))             #329 
    print(len(mid_high_valence))            #261 
    print(len(high_valence))                #105

    playlists = [low_valence,mid_low_valence,mid_mid_valence,mid_high_valence,high_valence]
    playlistsNames = ['slow','mid_low_valence','balanced','upper mediocre','ecstasy']

    # folders = ['everything/']

    # for a in playlists:
    #     #print(a)
    #     for b in a:
    #         print(b)
    #         for c in folders:
    #             try:
    #                 oldAddress = 'E:/Shaarav/music/' + str(b) + '.mp3'
    #                 newAddress = 'E:/Shaarav/playlists/' + playlistsNames[playlists.index(a)] + '/' + str(b) + '.mp3'
    #                 #print(oldAddress)
    #                 #print(newAddress)
    #                 shutil.copy(oldAddress,newAddress)
    #                 os.remove(oldAddress)
    #             except Exception as e:
    #                 print(e)
    #                 pass

def filter2():
    with open(r"E:\Shaarav\energism\songs.csv",'r',encoding='utf8') as box:
        reader = csv.reader(box)
        #print(type(reader))
        reader.__next__()
        songdict = []
        for a in reader:
            songdict.append(a)
        #songdict.pop(0)
        #print(songdict)
        #print(songdict[0])
        #print(type(songdict[1]))

    # print(len(songdict))
    # for a in songdict:
    #     print(a)
    #     break 
    
    # print(type(songdict[0]))
    # for a in songdict[0]:
    #     print(a, type(a))
    #     pass
    
    playlists = {'amped':{},'chill':{},'anger':{},'dance':{},'sad':{},'happy':{}, 'others':{}}

    try:
        for a in songdict:
            if (0.80<=eval(a[2])<=1 and 0.40<=eval(a[5])<=0.60 and 0.40<=eval(a[12])<=0.60 and 0<=eval(a[1])<=0.20):
                playlists['amped'][a[14]] = a
            elif (0.20<=eval(a[2])<=0.40 and 0.40<=eval(a[5])<=0.60 and 0.20<=eval(a[12])<=0.40 and 0.60<=eval(a[3])<=1):
                playlists['chill'][a[14]] = a
            elif (0.60<=eval(a[2])<=0.80 and 00<=eval(a[5])<=0.20 and 0.20<=eval(a[12])<=0.40 and 00<=eval(a[1])<=0.20):
                playlists['anger'][a[14]] = a
            elif (0.60<=eval(a[2])<=0.80 and 0.40<=eval(a[5])<=0.60 and 0.60<=eval(a[12])<=1 and 00<=eval(a[1])<=0.20):
                playlists['dance'][a[14]] = a
            elif (00<=eval(a[2])<=0.20 and 00<=eval(a[5])<=0.20 and 00<=eval(a[12])<=0.20 and 0.40<=eval(a[3])<=0.60):
                playlists['sad'][a[14]] = a
            elif (0.40<=eval(a[2])<=0.60 and 0.80<=eval(a[5])<=1 and 0.40<=eval(a[12])<=0.60 and 00<=eval(a[1])<=0.20):
                playlists['happy'][a[14]] = a
            else:
                playlists['others'][a[14]] = a
    except Exception as e:
        print(a)
        raise e
    
    for a in playlists:
        print(a, len(playlists[a]))



def dataset():
    with open(r"E:\Shaarav\energism\tracklist.txt",'r',encoding='utf8') as box:
        text = box.readlines()
        trackNameList = []
        for a in text:
            a=a.rstrip('\n')
            trackNameList.append(a)
        #print(list2)
    
    for a in trackNameList:
        pass
    print(a)

    with open(r"E:\Shaarav\energism\trackFeats.txt",'r',encoding='utf8') as box:
        records = [(ast.literal_eval(line.strip()))[0] for line in box]
        all_keys = set()
        for record in records:
            all_keys.update(record.keys())
        all_keys = list(all_keys)

        with open(r"E:\Shaarav\energism\songs.csv", 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=all_keys)
            writer.writeheader()
            writer.writerows(records)

def addcolumn():
    with open(r"E:\Shaarav\energism\trackpaths.txt",'r',encoding='utf8') as box:
        text = box.readlines()
        trackNameList = []
        for a in text:
            a=a.rstrip('\n')
            trackNameList.append(a)

    new_column_name = "Track Path"
    new_column_values = trackNameList  # or dynamically calculate this value if needed

    # Read the existing CSV and add the new column
    with open(r"E:\Shaarav\energism\songs.csv", 'r', encoding='utf8') as infile, open(r"E:\Shaarav\energism\songs2.csv", 'w', newline='',encoding='utf8') as outfile:
        reader = csv.DictReader(infile)
        # Add the new column to the fieldnames
        fieldnames = reader.fieldnames + [new_column_name]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        
        # Write the header with the new column
        writer.writeheader()
        for row, new_value in zip(reader, new_column_values):
            row[new_column_name] = new_value  # Assign the new column value for this row
            writer.writerow(row)
    
    return


    



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

# if True:
#     getsongs()
#     print("done1")
#     writesongs()
#     print("done2")
#     getbpms()
#     print("done3")
#     filter()
#     print("done4")


#initial testing
'''
spotty = connection()
testSong = getTrackId(spotty,'devlin - watchtower')
#pprint.pprint(testSong)
testSongFeats = spotty.audio_features(tracks=[testSong])
pprint.pprint(testSongFeats)
'''

# getting song features of all songs
'''
songFolderPath = r"E:/Shaarav/energism/upper mediocre" #kept changing folder paths
getsongs(songFolderPath)
'''
# getting trackIDs
'''
writesongs()
'''

#getting track features
'''
getbpms()
'''

#songs analysis

#filter()

#12-11-2024

#valence {0-20:106, 20-40:253, 40-60:329, 60-80:261, 80-100:105}
#energy {0-20:5, 20-40:45, 40-60:193, 60-80:468, 80-100:343}
#acousticness {0-20:807, 20-40:133, 40-60:56, 60-80:45, 80-100:13}
#danceability {0-20:3, 20-40:66, 40-60:381, 60-80:529, 80-100:75}
#instrumentalness {0-20:978, 20-40:20, 40-60:17, 60-80:21, 80-100:18}
#speechiness {0-20:997, 20-40:53, 40-60:4, 60-80:0, 80-100:0}

#liveness {0-20:705, 20-40:263, 40-60:58, 60-80:22, 80-100:6}

#danceability {0-40:69, 40-60:381, 60-70:312, 70-90:287, 90-100:5}
#getbpms()
#addcolumn()

#amped (energy = 80-100, valence = 40-60, danceability = 40-60, instrumentalness = 0-20)
#chill (energy = 20-40, valence = 40-60, dance = 20-40, acousticness = 60-100)
#anger (energy = 60-80, valence = 00-20, dance = 20-40, instrument = 0-20)
#dance (energy = 60-80, valence = 40-60, dance = 60-100, instrument = 0-20)
#sad (energy = 0-20, valence = 0-20, dance = 0-20, acousticness = 40-60)
#happy (energy = 40-60, valence = 80-100, dance = 40-60, instrumental = 0-20)


filter2()