import os
import random

playlists = os.listdir("E:/shaarav/playlists/")
fullist = []

for a in playlists:
    try:
        if '/new/' not in a:
            
            b = os.listdir("E:/shaarav/playlists/" + a)
            fullist.extend(b)
        else:
            continue
    except Exception as e:
        print(e)

#print(fullist)
#print(len(fullist))
count = 0
for c in fullist:
    if (fullist.count(c))>1:
        count+=1
        print(c)
print(count)


