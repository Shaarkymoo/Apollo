import pygame
import csv

with open('playlist1.csv','r',encoding='utf8') as box:
    reader = csv.reader(box)
    songlist = []
    for a in reader:
        song = a[1]+a[2]
        songlist.append(song)

pygame.mixer.init()
for b in songlist:
    try:
        pygame.mixer.music.load(b)
        pygame.mixer.music.unload()
    # pygame.mixer.music.play()
    except Exception as e:
        print(e)