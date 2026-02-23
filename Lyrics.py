import lyricsgenius
import eyed3
import os
import tempfile
import subprocess

VSCODE_PATH = r"D:\Microsoft VS Code\Code.exe"
PROCESSED_FILE = r"D:\Projects\Apollo\processed_songs.txt"

# ------------------ checkpoint helpers ------------------

def load_processed():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def mark_processed(filename):
    with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
        f.write(filename + "\n")


# ------------------ editor review ------------------

def review_lyrics_in_vscode(song_name, lyrics):
    with tempfile.NamedTemporaryFile(
        mode="w+",
        suffix=".txt",
        delete=False,
        encoding="utf-8"
    ) as tf:
        tf.write(f"# Song: {song_name}\n")
        tf.write("# Edit lyrics below. Close file to continue.\n\n")
        if lyrics:
            tf.write(lyrics)

        temp_path = tf.name

    subprocess.run([VSCODE_PATH, "--reuse-window", "--wait", temp_path])

    with open(temp_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    final_lyrics = "".join(
        line for line in lines if not line.startswith("#")
    ).strip()

    return final_lyrics


# ------------------ genius setup ------------------

def genius_setup():
    client_id = 'FYST0CoaHDYMbCMzDsbM2ze6lHCBD7nl5X3IknYGsSmWj3nvgLdLjBaCKpaWLBRE'
    client_secret = 'O9R4odQExaVokhgEDT6-bnEHO79JJdcrzoknYnv3L0k8d0Ryr3WuwfXK7fRpq2q2jfZ_zqywfDM-7LdPhLBkLQ'
    client_token = 'mF3AF4cXWIi-jKzvn8pUyXGMOtVgXqlTmF-gO7Ax72pSssZZTVViwxWKML0y_FCM'
    genius = lyricsgenius.Genius(client_token)
    genius.verbose = False
    genius.remove_section_headers = False
    genius.skip_non_songs = True
    genius.response_format = "plain"
    return genius


def search_lyrics(genius_obj, query):
    return genius_obj.search_song(query)

def musixmatch_setup():
    apikey = '8878031489eee173a7cdf0fcb909b869'
    return 


# ------------------ core logic ------------------

def get_existing_lyrics(songfile):
    """
    Returns lyrics from MP3 tag if present, else None
    """
    if songfile.tag and songfile.tag.lyrics:
        text = songfile.tag.lyrics[0].text
        if text and text.strip():
            return text.strip()
    return None



def update_songs(genius_obj):
    loc = r'E:\Shaarav\playlists\\'
    errors = []

    processed = load_processed()

    for filename in os.listdir(loc):
        if not filename.endswith(".mp3"):
            continue

        if filename in processed:
            print(f"Skipping (already processed): {filename}")
            continue

        song_name = filename[:-4]
        print(f"Processing: {song_name}")

        try:
            path = os.path.join(loc, filename)
            songfile = eyed3.load(path)

            if songfile.tag is None:
                songfile.initTag()

            # 1️⃣ try existing lyrics first
            lyrics = get_existing_lyrics(songfile)

            # 2️⃣ only hit Genius if empty
            if not lyrics:
                print("→ No existing lyrics, querying Genius")
                song_object = search_lyrics(genius_obj, song_name)
                lyrics = song_object.lyrics if song_object else None
            else:
                print("→ Using existing embedded lyrics")

            # 3️⃣ review step (always)
            reviewed_lyrics = review_lyrics_in_vscode(song_name, lyrics)

            if not reviewed_lyrics:
                print("No lyrics provided, skipping.")
                errors.append(song_name)
                continue

            songfile.tag.lyrics.set(reviewed_lyrics)
            songfile.tag.save()

            mark_processed(filename)

        except Exception as e:
            print("Error:", e)
            errors.append(song_name)

    print("\nDone.")
    print("Skipped / errors:", errors)


# ------------------ run ------------------

#print("start")
#test_1 = search_lyrics(genius_setup(), update_songs())
#print("searched")
#pprint(vars(test_1))
#print(test_1.lyrics)

genius_object = genius_setup()
update_songs(genius_object)
