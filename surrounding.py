import os
import numpy as np
import librosa
import soundfile as sf

def stereo_spread(file_path):
    y, sr = librosa.load(file_path, sr=None, mono=False)
    if y.ndim < 2:
        return 0  # Mono file
    left, right = y[0], y[1]
    correlation = np.corrcoef(left, right)[0, 1]
    spread = 1 - abs(correlation)  # Higher = more stereo difference
    return spread

folder = 'your_mp3_folder'
spread_scores = {}

for filename in os.listdir(folder):
    if filename.endswith(".mp3"):
        full_path = os.path.join(folder, filename)
        try:
            score = stereo_spread(full_path)
            spread_scores[filename] = score
        except Exception as e:
            print(f"Error with {filename}: {e}")

# Print songs with highest spatial spread
for song, score in sorted(spread_scores.items(), key=lambda x: x[1], reverse=True):
    print(f"{song}: Stereo Spread Score = {score:.2f}")
