from googleapiclient.discovery import build
import pprint
from pytube import YouTube
import os

while True:
    video_link = str(input("Link:"))
    if video_link=='n':
        break
    yt = YouTube(video_link)
    destination = "D:\\shaarav\\wastebin"
    video = yt.streams.filter(only_audio=True, audio_codec='A_MPEG/L3').first()
    print(video)
    print(video.parse_codecs())
    out_file = video.download(output_path=destination)
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file,new_file)
    print(yt.title + "has been downloaded")

