import os
folder = "D:/shaarav/playlists/intense/"
songlist = os.listdir("D:/shaarav/playlists/intense/")

for a in songlist:
    old_name = folder + a
    a = a.replace('.mp3','')
    a = a.split()
    a.pop()
    b = ''
    b = b.join(a) + '.mp3'
    new_name = folder + b
    os.rename(old_name,new_name)