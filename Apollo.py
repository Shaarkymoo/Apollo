import pprint
import tkinter.filedialog
from tkinter import *
import random
import pygame
from tkinter.font import Font
from pygame import mixer
#from googleapiclient.discovery import build
from pytube import YouTube
import os
from ffmpy import FFmpeg
import lyricsgenius
import datetime
import csv
import pafy

stuff_font = ("Comfortaa", 11)

# color
common_bg = '#000000'
common_fg = '#ffffff'

# endevent
music_end = pygame.USEREVENT + 1
pygame.mixer.music.set_endevent(music_end)
pygame.init()
mixer.init()

# vol
current_volume = float(0.5)
finished_playing = []
queue = []
queue_condition = False
shuffle_condition = False
repeat_one_condition = False
repeat_all_condition = False

# functions

def currently_playing(nametext):
    global song_title

    split_title = nametext.split("/")
    song_title = str(split_title[-1])
    song_title = song_title.replace('.mp3','')
    current_song_name_label.config(text=song_title)
    return


def play_song(song_name):
    global current_volume
    global current_song

    try:
        mixer.music.load(song_name)
        mixer.music.set_volume(current_volume)
        mixer.music.play()
        mixer.music.set_endevent(music_end)
        currently_playing(song_name)
        current_song = song_name

    except Exception as e:
        print(e)
    return


def select_song():
    global queue
    global queue_condition
    global current_song

    filetypes = (('mp3 files','*.mp3'),('text files', '*.txt'),('csv files','*.csv'),('All files', '*.*'))
    filename = tkinter.filedialog.askopenfilename(initialdir="D:/shaarav/", title="Please select a file",filetypes = filetypes)
    if '.txt' in filename:
        with open(filename,'r',encoding='utf8') as file:
            songlist = file.read()
        songlist = songlist.split('\n')
        if mixer.music.get_busy() == False:
            current_song = songlist.pop(0)
            play_song(current_song)
            queue.extend(songlist)
            if len(queue)>=1:
                queue_condition = True
        elif mixer.music.get_busy() == True:
            queue.extend(songlist)
            if len(queue)>=1:
                queue_condition = True
    elif '.csv' in filename:
        with open(filename,'r',encoding='utf8') as file:
            csvreader = csv.reader(file)
            headers = next(csvreader)
            songlist = []
            for a in csvreader:
                song = a[1]+a[2]
                songlist.append(song)
        if mixer.music.get_busy() == False:
            current_song = songlist.pop(0)
            play_song(current_song)
            queue.extend(songlist)
            if len(queue)>=1:
                queue_condition = True
        elif mixer.music.get_busy() == True:
            queue.extend(songlist)
            if len(queue)>=1:
                queue_condition = True

    elif '.mp3' in filename:
        current_song = filename
        if mixer.music.get_busy() == False:
            play_song(current_song)

        elif mixer.music.get_busy() == True:
            queue.append(filename)
            queue_condition = True
    return


def pause():
    try:
        if mixer.music.get_busy() == True:
            mixer.music.pause()
            pause_resume_button.config(text="resume", command=resume)
    except Exception as e:
        print(e)
    return


def resume():
    try:
        if mixer.music.get_busy() == False:
            mixer.music.unpause()
            pause_resume_button.config(text="pause", command=pause)
    except Exception as e:
        print(e)
    return


def increase_vol():
    try:
        global current_volume
        if current_volume >= 1:
            current_volume_label.config(text="Volume: %s" % ("max"))
            return
        else:
            new_vol = current_volume + float(0.1)
            new_vol = round(new_vol, 1)
            current_volume = new_vol
            mixer.music.set_volume(current_volume)
            current_volume_label.config(text="Volume: %1.1f" % (current_volume))
    except Exception as e:
        print(e)
    return


def decrease_vol():
    try:
        global current_volume
        if current_volume <= 0:
            current_volume_label.config(text="Volume: %s" % ("muted"))
            return
        else:
            new_vol = current_volume - float(0.1)
            new_vol = round(new_vol, 1)
            current_volume = new_vol
            mixer.music.set_volume(current_volume)
            current_volume_label.config(text="Volume: %1.1f" % (current_volume))
    except Exception as e:
        print(e)
    return


def stop():
    global current_song
    global finished_playing
    global queue
    try:
        if mixer.music.get_busy() == True:
            mixer.music.unload()
            current_song_name_label.config(text="")
            finished_playing.append(current_song)
            queue = []
    except Exception as e:
        print(e)
    return


def play_next():
    global current_song
    global queue_condition
    global queue
    global finished_playing

    if mixer.music.get_busy() == True:
        new_song = get_song()
        if new_song != None:
            play_song(new_song)
    return


def play_last():
    global current_song
    global queue_condition
    global finished_playing

    if len(finished_playing) != 0:
        queue.insert(0, current_song)
        queue_condition = True
        current_song = finished_playing.pop(-1)
        play_song(current_song)
    return


def shuffle_turn_on():
    global queue_condition
    global shuffle_condition
    if queue_condition == True and shuffle_condition == False:
        shuffle_condition = True
        shuffle_button.config(text="Shuffle : on", command=shuffle_turn_off)
    return


def shuffle_turn_off():
    global shuffle_condition
    if shuffle_condition == True:
        shuffle_condition = False
        shuffle_button.config(text="Shuffle : off",command = shuffle_turn_on)
    return


def check_song():
    for event in pygame.event.get():
        if event.type == music_end:
            new_song = get_song()
            if new_song == None:
                current_song_name_label.config(text="Nothing playing currently")
            else:
                play_song(new_song)
                break

def entry_get():
    global videos
    global save_as

    query = download_search_bar.get()
    save_as = download_save_as.get()
    download_search_button.place_forget()
    download_search_bar.place_forget()
    download_save_as.place_forget()
    download_query_label.place_forget()
    download_save_as_label.place_forget()

    api_key = 'AIzaSyCUwPjj8sdItdIyPwTJrZdcncdgH_ekg3E'
    youtube = build('youtube', 'v3', developerKey=api_key)

    query_term = query
    request = youtube.search().list(
        q=query_term,
        part='snippet',
        maxResults=15,
        type = 'video'
    )
    response = request.execute()
    videos = {}
    for a in response['items']:
        id = a['id']
        id = id['videoId']
        title = a['snippet']
        title = title['title']
        videos[title] = id

    download_listbox.place(x = 10, y = 335, height = 200, width = 620)
    n=0
    for key in videos:
        download_listbox.insert(n,key)
        n=n+1

    download_yes_button.place(x = 255 ,y = 540, height = 40, width = 60)
    download_no_button.place(x = 325,y = 540,height = 40, width = 60 )

def download_yes():
    global save_as
    global videos

    pafy.set_api_key("AIzaSyCUwPjj8sdItdIyPwTJrZdcncdgH_ekg3E")
    for a in download_listbox.curselection():
        index = a

    vidlist = []
    for key,value in videos.items():
        flush = [key,value]
        vidlist.append(flush)

    song_to_be_dd = vidlist[index][1]

    download_listbox.place_forget()
    download_no_button.place_forget()
    download_yes_button.place_forget()
    video_link = 'https://www.youtube.com/watch?v=' + song_to_be_dd
    destination = "D:\\shaarav\\wastebin\\"
    converted_file = "D:\\shaarav\\music\\" + save_as + '.mp3'
    songphase1 = pafy.new(video_link)
    songphase2 = songphase1.getbestaudio(preftype='m4a')
    songphase3 = songphase2.download(filepath = "D:\\shaarav\\wastebin\\")

    if len(save_as)==1 or len(save_as)==0:
        save_as = songphase2.title

    new_file = 'D:\\shaarav\\wastebin\\' + songphase2.title + '.m4a'
    ff = FFmpeg(
            inputs = {new_file: None},
            outputs= {converted_file:'-ac 2' }
    )
    ff.run()

def download_no():
    download_listbox.place_forget()
    download_yes_button.place_forget()
    download_no_button.place_forget()
    download()

def download():

    try:
        playlist_name_entry.place_forget()
        playlist_name_label.place_forget()
        playlist_name_accept.place_forget()
        lyrics_textbox.place_forget()
        lyrics_scrollbar.place_forget()
    except Exception as e:
        print(e)

    download_search_button.place(x = 245, y = 425 , height = 40, width = 150)
    download_search_bar.place(x = 80,y = 335,height = 40, width = 550)
    download_save_as.place(x = 80, y = 380, height = 40, width = 550)
    download_query_label.place(x = 10, y = 335, height = 40, width = 65)
    download_save_as_label.place(x = 10,y = 380, height = 40, width = 65)

    return

def lyrics_func():
    try:
        playlist_name_entry.place_forget()
        playlist_name_label.place_forget()
        playlist_name_accept.place_forget()
        download_search_button.place_forget()
        download_search_bar.place_forget()
        download_save_as.place_forget()
        download_query_label.place_forget()
        download_save_as_label.place_forget()
    except Exception as e:
        print(e)

    client_id = 'FYST0CoaHDYMbCMzDsbM2ze6lHCBD7nl5X3IknYGsSmWj3nvgLdLjBaCKpaWLBRE'
    client_secret = 'O9R4odQExaVokhgEDT6-bnEHO79JJdcrzoknYnv3L0k8d0Ryr3WuwfXK7fRpq2q2jfZ_zqywfDM-7LdPhLBkLQ'
    client_token = 'mF3AF4cXWIi-jKzvn8pUyXGMOtVgXqlTmF-gO7Ax72pSssZZTVViwxWKML0y_FCM'

    genius = lyricsgenius.Genius(client_token)
    search_query = song_title
    song = genius.search_song(search_query)

    lyrics_text = song.lyrics

    lyrics_textbox.place(x = 10,y = 335,height = 300, width = 610)
    lyrics_scrollbar.place(x = 620,y = 335,height = 300, width = 20)

    try:
        lyrics_textbox.delete(0.0,'end')
    except Exception as e:
        print(e)

    lyrics_textbox.insert(INSERT,lyrics_text)

def add_playlist():
    playlist_new_name = playlist_name_entry.get()+'.csv'
    playlist_name_entry.place_forget()
    playlist_name_label.place_forget()
    playlist_name_accept.place_forget()
    try:
        with open(playlist_new_name,'r',newline='\n',encoding='utf8') as file:
            pass
        print("File already exists")
    except:
        with open(playlist_new_name,'w',newline='\n',encoding='utf8') as file:
            headers = ['Date added','Path','Song']
            csvwriter = csv.writer(file)
            csvwriter.writerow(headers)


def del_playlist():
    filetypes = (('text files', '*.txt'),('csv files','*.csv'),('All files', '*.*'))
    file = tkinter.filedialog.askopenfilename(initialdir="C:/Users/Shaarav Agarwal/PycharmProjects/pythonProject/venv", title="Please select a file",filetypes = filetypes)
    os.remove(file)


def add_playlist_display():
    try:
        download_search_button.place_forget()
        download_search_bar.place_forget()
        download_save_as.place_forget()
        download_query_label.place_forget()
        download_save_as_label.place_forget()
        lyrics_textbox.place_forget()
        lyrics_scrollbar.place_forget()
    except Exception as e:
        print(e)

    playlist_name_entry.place(x = 140,y = 335, height = 40, width = 490)
    playlist_name_label.place(x = 10, y = 335, height = 40, width = 130)
    playlist_name_accept.place(x = 270, y = 380,height = 40, width = 100)

def change_playlist():
    playlist_button.config(text = "Back",command=back1)
    download_button.config(text = "Add playlist",command = add_playlist_display)
    lyrics_button.config(text = "Delete playlist",command = del_playlist)

def add_song():
    filetypes = (('mp3 files', '*.mp3'), ('text files', '*.txt'),('csv files','*.csv'), ('All files', '*.*'))
    playlist_name = tkinter.filedialog.askopenfilename(initialdir="C:/Users/Shaarav Agarwal/PycharmProjects/pythonProject/venv", title="Please select a file",
                                                  filetypes=filetypes)
    songlist = tkinter.filedialog.askopenfilenames(initialdir="D:/shaarav/", title="Please select a file",
                                                  filetypes=filetypes)
    with open(playlist_name,'r',newline = '',encoding='utf8') as file:
        csvreader = csv.reader(file)
        headers = next(csvreader)
        old_songs = []
        for b in csvreader:
            old_songs.append(b[2])


    check_tracks = []
    for a in songlist:
        a = a.split('/')
        check_tracks.append(a[-1])

    for a in old_songs:
        try:
            check_tracks.remove(a)
        except:
            pass

    with open(playlist_name,'a',newline = '',encoding='utf8') as file:
        csvwriter = csv.writer(file)
        date = str(datetime.date.today())
        songs = []
        for record in songlist:
            record = record.split('/')
            track = record.pop(-1)
            if track not in check_tracks:
                continue
            path = ''
            for b in record:
                path += b + '/'
            songs.append([date,path,track])
        csvwriter.writerows(songs)


def del_song():
    filetypes = (('mp3 files', '*.mp3'), ('text files', '*.txt'),('csv files','*.csv'), ('All files', '*.*'))
    playlist_name = tkinter.filedialog.askopenfilename(initialdir="C:/Users/Shaarav Agarwal/PycharmProjects/pythonProject/venv", title="Please select a file",
                                                       filetypes=filetypes)
    songlist = tkinter.filedialog.askopenfilenames(initialdir="D:/shaarav/", title="Please select a file",
                                                   filetypes=filetypes)

    with open(playlist_name,'r',newline = '\n',encoding='utf8') as file:
        csvreader = csv.reader(file)
        headers = next(csvreader)
        data = []
        for a in csvreader:
            data.append(a)
    tracks = []
    for record in songlist:
        record = record.split('/')
        tracks.append(record[-1])
    newdata = []

    while tracks:
        for a in data:
            for b in tracks:
                if a[2]==b:
                    data.remove(a)
                    tracks.remove(b)

    with open(playlist_name,'w',newline = '\n',encoding = 'utf8') as file:
        csvwriter = csv.writer(file)
        csvwriter.writerow(headers)
        csvwriter.writerows(data)



def change_song():
    playlist_button.config(text = 'Back', command = back1)
    download_button.config(text = 'Add song', command = add_song)
    lyrics_button.config(text = 'Del song',command = del_song)

def playlist_menu():
    try:
        lyrics_textbox.place_forget()
        lyrics_scrollbar.place_forget()
    except Exception as e:
        print(e)

    playlist_button.config(text = "Back",command=back1)
    download_button.config(text = "Change playlists",command=change_playlist)
    lyrics_button.config(text = "Change songs",command=change_song)

def back1():
    playlist_button.config(text="Playlists",command = playlist_menu)
    download_button.config(text = "Download new songs", command = download)
    lyrics_button.config(text = "Lyrics",command = lyrics_func)

def repeat_one():
    global repeat_one_condition
    global repeat_all_condition

    repeat_one_condition = True
    repeat_all_condition = False
    repeat_button.config(text = "Repeat : one",command = repeat_all)

def repeat_all():
    global repeat_one_condition
    global repeat_all_condition

    repeat_one_condition = False
    repeat_all_condition = True

    repeat_button.config(text = "Repeat : all",command = repeat_off)

def repeat_off():
    global repeat_one_condition
    global repeat_all_condition

    repeat_one_condition = False
    repeat_all_condition = False

    repeat_button.config(text = "Repeat : off", command = repeat_one)

def get_song():
    global queue_condition
    global queue
    global finished_playing
    global repeat_all_condition
    global repeat_one_condition
    global shuffle_condition
    global current_song

    if queue_condition == True:
        if repeat_all_condition == False and repeat_one_condition == False:
            if shuffle_condition == False:
                finished_playing.append(current_song)
                current_song = queue.pop(0)

                if len(queue) == 0:
                    queue_condition = False
                    print("set to false")
                return current_song
            else:
                finished_playing.append(current_song)
                current_song = random.choice(queue)
                queue.remove(current_song)
                if len(queue) == 0:
                    queue_condition = False
                return current_song
        elif repeat_all_condition == False and repeat_one_condition == True:
            return(current_song)
        elif repeat_all_condition == True and repeat_one_condition == False:
            finished_playing.append(current_song)
            if shuffle_condition == False:
                current_song = queue.pop(0)
                queue.append(current_song)
                return current_song
            else:
                current_song = random.choice(queue)
                return current_song
        else:
            pass
    else:
        if repeat_one_condition == True:
            return(current_song)
    return None




########################################################################################################################################


apollo = Tk(className="apollo")
apollo.geometry("640x640")
apollo.configure(bg=common_bg)

# widgets

title_label = Label(apollo, text="Apollo", font=('Montserrat', 20), bg=common_bg, fg=common_fg)
title_label.place(x=260, y=0, height=40, width=120)

select_button = Button(apollo, text="Select a track/playlist", font=stuff_font, bg=common_bg, fg=common_fg,
                       command=select_song)
select_button.place(x=220, y=60, height=40, width=200)

current_song_name_label = Label(apollo, text="Nothing playing currently", font=stuff_font, bg=common_bg,
                                fg=common_fg,
                                wraplength=600, relief='ridge')
current_song_name_label.place(x=10, y=120, height=80, width=620)

current_volume_label = Label(apollo, text='Volume: 0.5', font=stuff_font, bg=common_bg, fg=common_fg,
                             relief='ridge')
current_volume_label.place(x=0, y=210, height=40, width=160)

pause_resume_button = Button(apollo, text="Pause", font=stuff_font, bg=common_bg, fg=common_fg, command=pause)
pause_resume_button.place(x=160, y=210, height=40, width=160)

stop_button = Button(apollo, text='stop', font=stuff_font, bg=common_bg, fg=common_fg, command=stop)
stop_button.place(x=320, y=210, height=40, width=160)

shuffle_button = Button(apollo, text='Shuffle : off', font=stuff_font, bg=common_bg, fg=common_fg,
                        command = shuffle_turn_on)
shuffle_button.place(x=480, y=210, height=40, width=160)

vol_up_button = Button(apollo, text="Vol+", font=stuff_font, bg=common_bg, fg=common_fg, command=increase_vol)
vol_up_button.place(x=0, y=250, height=40, width=80)

vol_down_button = Button(apollo, text="Vol-", font=stuff_font, bg=common_bg, fg=common_fg, command=decrease_vol)
vol_down_button.place(x=80, y=250, height=40, width=80)

play_next_button = Button(apollo, text="Play next song", font=stuff_font, bg=common_bg, fg=common_fg,
                          command=play_next)
play_next_button.place(x=160, y=250, height=40, width=160)

play_last_button = Button(apollo, text="Play last song", font=stuff_font, bg=common_bg, fg=common_fg,
                          command=play_last)
play_last_button.place(x=320, y=250, height=40, width=160)

repeat_button = Button(apollo, text="Repeat : off", font=stuff_font, bg=common_bg, fg=common_fg,
                       command = repeat_one)
repeat_button.place(x=480, y=250, height=40, width=160)

playlist_button = Button(apollo, text="Playlists", font=stuff_font, bg=common_bg, fg=common_fg,
                         command = playlist_menu)
playlist_button.place(x=0, y=290, height=40, width=213)

download_button = Button(apollo, text="Download new songs", font=stuff_font, bg=common_bg, fg=common_fg,
                         command = download)
download_button.place(x=214, y=290, height=40, width=213)

lyrics_button = Button(apollo, text="Lyrics", font=stuff_font, bg=common_bg, fg=common_fg,
                       command = lyrics_func)
lyrics_button.place(x=428, y=290, height=40, width=212)

download_search_button = Button(apollo,text = "Enter query: ",font = stuff_font, bg=common_bg, fg=common_fg,
                                command = entry_get)
download_save_as = Entry(apollo,font = stuff_font,bg = common_bg,fg = common_fg)
download_search_bar = Entry(apollo,font = stuff_font, bg=common_bg, fg=common_fg)
download_save_as_label = Label(apollo,text = "Save as: ",font = stuff_font,bg = common_bg,fg = common_fg)
download_query_label = Label(apollo,text = "Query :",font = stuff_font,bg = common_bg,fg = common_fg)
download_listbox = Listbox(apollo,font = stuff_font,bg = common_bg,fg = common_fg,selectmode = SINGLE)
download_yes_button = Button(apollo,text = 'Yes',font = stuff_font,bg = common_bg,fg = common_fg,
                             command = download_yes)
download_no_button = Button(apollo,text = 'No',font = stuff_font,bg = common_bg,fg = common_fg,
                            command = download_no)

lyrics_scrollbar = Scrollbar(apollo,orient = VERTICAL,width = 20)
lyrics_textbox = Text(apollo,font = stuff_font, bg=common_bg, fg=common_fg, yscrollcommand = lyrics_scrollbar.set , wrap = WORD)

playlist_name_entry = Entry(apollo,font = stuff_font,bg = common_bg,fg = common_fg)
playlist_name_accept = Button(apollo,text = 'Accept',font = stuff_font,bg = common_bg,fg = common_fg,command = add_playlist)
playlist_name_label = Label(apollo,text = 'Enter new name',font = stuff_font,bg = common_bg,fg = common_fg)

while True:
    check_song()
    apollo.update()