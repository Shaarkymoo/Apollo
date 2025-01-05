import yt_dlp
from yt_dlp import YoutubeDL

urls = ['https://youtu.be/jhgVu2lsi_k']

with YoutubeDL() as ydl:
    ydl.download(urls)
    
#command
#git config --global user.email "you@example.com"