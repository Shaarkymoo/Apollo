from googleapiclient.discovery import build
import pprint
from pytube import YouTube
import os
from ffmpy import FFmpeg


api_key = 'AIzaSyCUwPjj8sdItdIyPwTJrZdcncdgH_ekg3E'
youtube = build('youtube','v3',developerKey=api_key)

query_term = 'smitty+'
request = youtube.search().list(
        q=query_term ,
        part = 'snippet',
        maxResults = 5,
        type = 'video'
    )
response = request.execute()
videos = {}
for a in response['items']:
    id = a['id']
    id = id['videoId']
    title = a['snippet']
    title = title['title']
    videos[title]=id

pprint.pprint(response)
pprint.pprint(videos)

# def search_by_keyword():
#     global desire
#     query_term = str(input("Enter search : "))
#     request = youtube.search().list(
#         q=query_term ,
#         part = 'snippet',
#         maxResults = 5
#     )
#     response = request.execute()
#     print(pprint(response))
#     videos = {}
#     for a in response['items']:
#         id = a['id']
#         id = id['videoId']
#         title = a['snippet']
#         title = title['title']
#         videos[title]=id
#     desire = []
#     for a in videos:
#         print(a)
#         check = str(input("Is this what you wanted(y/n) : "))
#         if check == "y":
#             desire.append(a)
#             desire.append(videos[a])
#             return desire
#     else:
#         print("Search again with a different keyword")
#         search_by_keyword()
#
# search_by_keyword()
# video_link = "https://www.youtube.com/watch?v=" + desire[1]
#
#
#
#
#
#
# yt = YouTube(video_link)
# destination = "D:\\shaarav\\wastebin"
# video = yt.streams.filter(only_audio=True).first()
# out_file = video.download(output_path=destination)
# base, ext = os.path.splitext(out_file)
# new_file = base + '.mp3'
# os.rename(out_file,new_file)
#
# converted_file = "D:\\shaarav\\music\\" + yt.title + '.mp3'
#
# print(yt.title + " has been downloaded")
#
# ff = FFmpeg(
#         inputs = {new_file: None},
#         outputs= {converted_file:'-ac 2' }
# )
# ff.run()