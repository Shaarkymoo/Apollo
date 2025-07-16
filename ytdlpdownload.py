import yt_dlp
from yt_dlp import YoutubeDL

urls = ['https://youtu.be/jhgVu2lsi_k']

#with YoutubeDL() as ydl:
#    ydl.download(urls)
    
#command

#PS D:\Projects\Apollo> .\venv\bin\activate
# yt-dlp -P 'E:\Shaarav\wastebin\' -o '%(title)s - %(channel)s' -x --audio-format 'm4a' 
# --ffmpeg-location 'C:\ffmpeg' https://www.youtube.com/playlist?list=PLIRFSUH_WlMrZhbyDNoK9o9mNW9XlPXs2

# yt-dlp --embed-subs --sub-langs "en.*" --embed-metadata --embed-thumbnail -f bestaudio+bestvideo --merge-output-format mp4 "https://youtu.be/-rDTRuCOs9g"