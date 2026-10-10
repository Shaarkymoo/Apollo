import lyricsgenius
import eyed3
import os
import tempfile
import subprocess

# Load local API credentials from .env (gitignored)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

VSCODE_PATH = "/usr/bin/code"
PROCESSED_FILE = "/media/shaarky/Data/Projects/Apollo/processed_songs.txt"
NO_LYRICS_FILE = "/media/shaarky/Data/Projects/Apollo/processed - no lyrics.txt"
UNFOUND_FILE = "/media/shaarky/Data/Projects/Apollo/processed - unfound.txt"
MUSIC_LOC = '/media/shaarky/Data/Shaarav/my songs'

# ------------------ checkpoint helpers ------------------

def load_list(filepath):
    if not os.path.exists(filepath):
        return set()
    with open(filepath, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())


def load_processed():
    return load_list(PROCESSED_FILE)


def mark_in(filepath, filename):
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(filename + "\n")


def mark_processed(filename):
    mark_in(PROCESSED_FILE, filename)


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
    client_id = os.environ.get("GENIUS_CLIENT_ID", "")
    client_secret = os.environ.get("GENIUS_CLIENT_SECRET", "")
    client_token = os.environ.get("GENIUS_ACCESS_TOKEN", "")
    genius = lyricsgenius.Genius(client_token)
    genius.verbose = False
    genius.remove_section_headers = False
    genius.skip_non_songs = True
    genius.response_format = "plain"
    return genius


def search_lyrics(genius_obj, query):
    return genius_obj.search_song(query)

def musixmatch_setup():
    apikey = os.environ.get("MUSIXMATCH_API_KEY", "")
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



def iter_mp3_files(loc):
    """Yield (full_path, filename) for every .mp3 under loc, recursively."""
    for root, _dirs, files in os.walk(loc):
        for filename in files:
            if filename.lower().endswith(".mp3"):
                yield os.path.join(root, filename), filename


def update_songs(genius_obj):
    loc = MUSIC_LOC
    errors = []

    processed = load_processed()

    for path, filename in iter_mp3_files(loc):
        if filename in processed:
            print(f"Skipping (already processed): {filename}")
            continue

        song_name = filename[:-4]
        print(f"Processing: {song_name}")

        try:
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


def update_songs_with_markers(genius_obj):
    """
    Manual workflow:
    - Skips songs already recorded in ANY of the 3 checkpoint files
      (processed_songs.txt, processed - no lyrics.txt, processed - unfound.txt)
    - Every song goes through the review window — what you type and save decides
      where it gets recorded:
        * real lyrics  -> saved to the file, recorded in processed_songs.txt
        * "."          -> saved to the file, recorded in processed - no lyrics.txt
        * "*"          -> saved to the file, recorded in processed - unfound.txt
        * empty        -> nothing saved, nothing recorded (added to errors)
    """
    loc = MUSIC_LOC
    errors = []

    processed = load_processed()
    no_lyrics = load_list(NO_LYRICS_FILE)
    unfound = load_list(UNFOUND_FILE)

    for path, filename in iter_mp3_files(loc):
        if filename in processed or filename in no_lyrics or filename in unfound:
            print(f"Skipping (already handled): {filename}")
            continue

        song_name = filename[:-4]
        print(f"Processing: {song_name}")

        try:
            songfile = eyed3.load(path)

            if songfile.tag is None:
                songfile.initTag()

            # 1️⃣ try existing lyrics first (shows what's already embedded)
            lyrics = get_existing_lyrics(songfile)

            # 2️⃣ only hit Genius if empty
            if not lyrics:
                print("→ No existing lyrics, querying Genius")
                song_object = search_lyrics(genius_obj, song_name)
                lyrics = song_object.lyrics if song_object else None
            else:
                print("→ Using existing embedded lyrics")

            # 3️⃣ review step — YOU decide what to keep/type, then save & close
            reviewed_lyrics = review_lyrics_in_vscode(song_name, lyrics)

            if not reviewed_lyrics:
                print("No lyrics provided, skipping.")
                errors.append(song_name)
                continue

            # 4️⃣ save whatever you typed into the file's lyrics tag
            songfile.tag.lyrics.set(reviewed_lyrics)
            songfile.tag.save()

            # 5️⃣ record in the matching checkpoint file
            if reviewed_lyrics == ".":
                print("→ '.' saved — recording in processed - no lyrics")
                mark_in(NO_LYRICS_FILE, filename)
            elif reviewed_lyrics == "*":
                print("→ '*' saved — recording in processed - unfound")
                mark_in(UNFOUND_FILE, filename)
            else:
                print("→ Real lyrics saved — recording in processed")
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
update_songs_with_markers(genius_object)
