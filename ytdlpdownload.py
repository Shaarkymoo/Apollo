from click import command
import yt_dlp
from yt_dlp import YoutubeDL

urls = ['https://youtu.be/jhgVu2lsi_k']

"""
with YoutubeDL() as ydl:
   ydl.download(urls)
    
command
environment
PS D:\Projects\Apollo> .\venv\bin\activate

playlist downloader
yt-dlp -P 'E:\Shaarav\wastebin\' -o '%(title)s - %(channel)s' -x --audio-format 'm4a' 
--ffmpeg-location 'C:\ffmpeg' https://www.youtube.com/playlist?list=PLIRFSUH_WlMrZhbyDNoK9o9mNW9XlPXs2

video download with subs
yt-dlp --embed-subs --sub-langs "en.*" --embed-metadata --embed-thumbnail -f bestaudio+bestvideo --merge-output-format mp4 "https://youtu.be/-rDTRuCOs9g"

yt-dlp \
  --split-chapters \
  --force-keyframes-at-cuts \
  -x \
  --audio-format mp3 \
  -o "%(title)s/%(section_number)02d - %(section_title)s.%(ext)s" \
  "YOUTUBE_URL"

"""