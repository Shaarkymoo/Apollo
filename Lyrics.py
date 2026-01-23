import lyricsgenius
import eyed3
from pprint import pprint
import os
import tempfile
import subprocess

VSCODE_PATH = r"D:\Microsoft VS Code\Code.exe"

def review_lyrics_in_vscode(song_name, lyrics):
    with tempfile.NamedTemporaryFile(
        mode="w+",
        suffix=".txt",
        delete=False,
        encoding="utf-8"
    ) as tf:
        tf.write(f"# Song: {song_name}\n")
        tf.write("# Edit the lyrics below if needed.\n")
        tf.write("# Close this file to continue.\n\n")
        tf.write(lyrics or "")
        temp_path = tf.name

    # Open in VS Code and WAIT until closed
    subprocess.run([VSCODE_PATH, "--wait", temp_path])

    # Read edited lyrics back
    with open(temp_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Remove comment lines
    final_lyrics = "".join(
        line for line in lines if not line.startswith("#")
    ).strip()

    return final_lyrics


def genius_setup(): 
    client_id = 'FYST0CoaHDYMbCMzDsbM2ze6lHCBD7nl5X3IknYGsSmWj3nvgLdLjBaCKpaWLBRE'
    client_secret = 'O9R4odQExaVokhgEDT6-bnEHO79JJdcrzoknYnv3L0k8d0Ryr3WuwfXK7fRpq2q2jfZ_zqywfDM-7LdPhLBkLQ'
    client_token = 'mF3AF4cXWIi-jKzvn8pUyXGMOtVgXqlTmF-gO7Ax72pSssZZTVViwxWKML0y_FCM'

    genius = lyricsgenius.Genius(client_token)
    genius.verbose = False # Turn off status messages
    genius.remove_section_headers = False # Remove section headers (e.g. [Chorus]) from lyrics when searching
    genius.skip_non_songs = True # Include hits thought to be non-songs (e.g. track lists)
    #genius.excluded_terms = ["(Remix)", "(Live)"] # Exclude songs with these words in their title
    genius.response_format = 'plain'
    return genius

def musixmatch_setup():
    apikey = '8878031489eee173a7cdf0fcb909b869'
    return

def search_lyrics(object,query):
    #searchquery = str(input(query))
    song = object.search_song(query)
    #print(song.lyrics)
    return song

def update_songs(genius_obj):
    loc = 'E:/Shaarav/playlists/despresso/'
    errors = []

    for filename in os.listdir(loc):
        if not filename.endswith(".mp3"):
            continue

        song_name = filename.replace(".mp3", "")
        print(f"Processing: {song_name}")

        try:
            song_object = search_lyrics(genius_obj, song_name)
            if song_object is None:
                raise Exception("No lyrics found")

            reviewed_lyrics = review_lyrics_in_vscode(
                song_name,
                song_object.lyrics
            )

            songfile = eyed3.load(os.path.join(loc, filename))
            if songfile.tag is None:
                songfile.initTag()

            songfile.tag.lyrics.set(reviewed_lyrics)
            songfile.tag.save()

        except Exception as e:
            print("Error:", e)
            errors.append(song_name)

    print("\nDone.")
    print("Errors:", errors)

#print("start")
#test_1 = search_lyrics(genius_setup(), update_songs())
#print("searched")
#pprint(vars(test_1))
#print(test_1.lyrics)

genius_object = genius_setup()
update_songs(genius_object)

