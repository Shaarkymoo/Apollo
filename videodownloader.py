import pafy
import ffmpy
from ffmpy import FFmpeg
import os

url = str(input("Enter url:"))
#print(url)

video = pafy.new(url)
#print(video.title)

bestvid = video.getbestvideo(preftype='mp4')
bestaud = video.getbestaudio(preftype='m4a')
#print(bestvid,bestaud)
bestfull = video.getbest(preftype='mp4')
#print(bestfull.resolution,bestfull.extension)

allstreams = video.allstreams
#for s in allstreams:
#   print(s.mediatype,s.extension,s.quality,s.bitrate, sep="\t")
#print(allstreams)

for s in allstreams:
   if '720' in str(s.quality) and 'mp4' in str(s.extension):
      bestvid = s
      break
      

folder = "E:\\Shaarav\\downloadedVideos2\\"
vidfileloc = folder + video.title + "video" + "." + bestvid.extension
audfileloc = folder + video.title + "audio" + "." + bestaud.extension



vidfilename = bestvid.download(quiet = False, filepath = vidfileloc)
audfilename = bestaud.download(quiet = False, filepath = audfileloc)
location = folder + video.title + "." + bestfull.extension

print(location)

#filename = bestfull.download(quiet = False,filepath = location)

ff = FFmpeg(
    inputs={vidfileloc: None, audfileloc: None},
    outputs={location: None}
)

ff.run()


