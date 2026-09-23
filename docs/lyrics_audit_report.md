# Lyrics Audit Report v2 — Renames, Segregation & Odd Ones Out
**Date:** 2026-08-26
**Music folder:** /media/shaarky/Data/Shaarav/playlists/ (3163 mp3s)
**Record file:** /media/shaarky/Data/Projects/Apollo/processed_songs.txt (2352 entries)

---

## 1. The 11 — recorded as processed but the file has NO lyrics

These 11 are in `processed_songs.txt` (so the loop recorded them as done) but the
current files have **no USLT lyrics frame at all**. This is the "didn't make the
transfer" bucket.

```
guitar solos/John Mayer - Slow Dancing In A Burning Room.mp3
heavy rock band/Nickelback - When We Stand Together.mp3
lovely/Train - Drive By.mp3
midrock/imagine dragons - whatever it takes.mp3
old party/Queen - Radio Ga Ga.mp3
old vocal/Backstreet Boys - Forces of Nature.mp3
old vocal/Backstreet Boys - The Unloved.mp3
old vocal/Lionel Richie - All Night Long.mp3
old vocal/Michael Jackson - You Rock My World.mp3
old vocal/Tears For Fears - Shout.mp3
potentones/Electric Light Orchestra - Last Train to London.mp3
```

> ⚠️ **ELO caveat:** `potentones/Electric Light Orchestra - Last Train to London.mp3`
> has a duplicate in `old party/` — that copy **does** have lyrics. So for ELO,
> the song exists with lyrics elsewhere in the library. The other 10 have no
> lyrics anywhere.

---

## 2. Segregation of the 791 no-lyrics songs by folder

**Your hypothesis was RIGHT.** The no-lyrics songs are almost entirely confined
to 6 playlists that were skipped wholesale. 670 of 791 (85%) sit in playlists
that are 70–96% missing lyrics:

| Playlist | Total | With lyrics | No lyrics | % missing |
|---|---|---|---|---|
| **quasar** | 96 | 4 | **92** | 96% |
| **robot seizure** | 279 | 21 | **258** | 92% |
| **karaoke** | 35 | 4 | **31** | 89% |
| **potentones** | 59 | 7 | **52** | 88% |
| **vibe** | 121 | 24 | **97** | 80% |
| **wtf** | 177 | 37 | **140** | 79% |
| cringe | 100 | 62 | 38 | 38% |
| X-POP | 73 | 49 | 24 | 33% |
| old vocal | 111 | 100 | 11 | 10% |
| old party | 146 | 140 | 6 | 4% |
| party | 28 | 22 | 6 | 21% |
| guitar solos | 25 | 20 | 5 | 20% |
| vocal beat | 62 | 57 | 5 | 8% |
| heavy rock band | 192 | 188 | 4 | 2% |
| midrock | 217 | 213 | 4 | 2% |
| indie | 93 | 90 | 3 | 3% |
| old guitar | 112 | 109 | 3 | 3% |
| raprap | 278 | 275 | 3 | 1% |
| light vocal | 58 | 56 | 2 | 3% |
| lowvibe | 45 | 43 | 2 | 4% |
| mainstream | 153 | 151 | 2 | 1% |
| literarap | 52 | 51 | 1 | 2% |
| lovely | 259 | 258 | 1 | 0% |
| songs with rap segments | 16 | 15 | 1 | 6% |
| edm drop | 201 | 201 | 0 | 0% |
| iron | 120 | 120 | 0 | 0% |
| low vibe rap | 28 | 28 | 0 | 0% |
| party rap | 19 | 19 | 0 | 0% |
| whisky | 8 | 8 | 0 | 0% |

**The 6 skipped playlists:** `robot seizure`, `wtf`, `vibe`, `quasar`,
`potentones`, `karaoke` = **670 of the 791 no-lyrics songs (85%)**. These
playlists were added/mostly never run through the lyrics loop.

---

## 3. Odd ones out in the 791 (121 songs)

These are no-lyrics songs sitting in playlists that WERE otherwise processed
(<70% missing) — they are the genuine stragglers, not part of the skipped-playlist
pattern. **121 total**, including **10 of the 11** from section 1 (tagged
`[PROCESSED-BUT-MISSING]`):

- **cringe: 38** — the biggest odd-one-out cluster (playlist was 62% processed)
- **X-POP: 24**
- **old vocal: 11** (includes 5 of the 11: Forces of Nature, The Unloved, Lionel
  Richie, MJ You Rock My World, Tears For Fears Shout)
- **old party: 6** (includes Queen Radio Ga Ga)
- **party: 6, guitar solos: 5** (includes John Mayer), **vocal beat: 5**
- **heavy rock band: 4** (includes Nickelback), **midrock: 4** (includes imagine dragons)
- **indie: 3, old guitar: 3, raprap: 3, light vocal: 2, lowvibe: 2, mainstream: 2**
- **literarap: 1, lovely: 1** (includes Train Drive By), **songs with rap segments: 1**

Full list: `/tmp/opencode/odd_ones_out.txt`

---

## 4. The 128 — check if renaming explains them

**9 of the 128 are renamed versions of songs that ARE in the record** — they
should fold into the processed set. These 9 have lyrics, their current filename
doesn't match the record, but they are the same songs:

| Record entry (old name) | Current file (new name) |
|---|---|
| A Little Faster- There For Tomorrow.mp3 | heavy rock band/A Little Faster - There For Tomorrow.mp3 |
| Caravan Palace -  Reverse.mp3 | mainstream/Caravan Palace - Reverse.mp3 |
| Kya Mujhe Pyar - Pritam.mp3 | cringe/Kya Mujhe Pyar - Pritam, K.K..mp3 |
| The Road to Hell Part II - Chris Rea Official.mp3 | guitar solos/The Road to Hell Part II - Chris Rea.mp3 |
| Hozier - From Eden - Hozier.mp3 | lovely/Hozier - From Eden.mp3 |
| Mike Posner, Stanaj, Yung Bae - Momma Always Told Me (feat. Stanaj & Yung Bae).mp3 | party rap/Mike Posner, Stanaj, Yung Bae - Momma Always Told Me.mp3 |
| Ted Lasso _ Ted Lasso Theme - Marcus Mumford & Tom Howe _ WaterTower.mp3 | mainstream/Marcus Mumford & Tom Howe _ WaterTower.mp3 |
| Tainted Love.mp3 | old party/Tainted Love - Soft Cell.mp3 |
| hands in the air.mp3 | raprap/Timbaland feat. Ne Yo- Hands in the Air.mp3 |

**The remaining 119 of the 128 are genuinely novel** — songs with lyrics that
were never in the record at all. Where they live:

| Folder | Count |
|---|---|
| cringe | 55 |
| X-POP | 46 |
| robot seizure | 6 |
| wtf | 6 |
| karaoke | 1 |
| lovely | 1 |
| party rap | 1 |
| potentones | 1 |
| quasar | 1 |
| vibe | 1 |

These are mostly songs whose lyrics came from another source (e.g. downloaded
with lyrics pre-embedded), or a run that didn't update the record. **They are
already counted in the 2372 with-lyrics total** — the record just never knew
about them.

---

## 5. The 98 "missing" record entries — renamed or removed?

**No files are truly missing.** Of the 98 record entries with no matching
filename:

- **15 are renames** → the song exists under a new filename (9 with lyrics, all
  listed in section 4's table, plus 6 more where the *new* name is ALSO already
  in the record: Memory Box, Face Off, Gorillaz Plastic Beach, T-Pain Best Love
  Song, Safe And Sound, Ed Sheeran Remember The Name).
- **83 are intentionally removed** — no matching file exists anywhere. Examples:
  Travis Scott - SICKO MODE, Bloc Party - Helicopter, Fall Out Boy - Centuries,
  Eye of the Tiger - Survivor, Purple Rain - Prince, Gorillaz - Clint Eastwood,
  The Cranberries - Dreams, Dandelions - Ruth B, etc.
  Full list: `/tmp/opencode/removed_from_record.txt`

---

## 6. Updated with_lyrics + updated record

- **`with_lyrics.txt`** (updated) = all 2372 songs with lyrics **by current file
  path**. The 9 renamed songs from section 4 are in here under their new names —
  they now correctly belong to the "processed with lyrics" set.
- **`processed_songs_UPDATED.txt`** = the record with renames applied (old
  entries replaced by new names) and the 83 removed entries dropped. Size: 2346
  (was 2352). This is a proposed corrected record you can adopt.

---

## Bottom line

| Question | Answer |
|---|---|
| What are the 11? | 11 songs recorded as processed but with no lyrics in the file (see §1). 10 have no lyrics anywhere; ELO exists with lyrics as a duplicate in old party/. |
| Are the 791 explained by skipped playlists? | **Mostly yes (85%)** — 670 are in the 6 skipped playlists (robot seizure, wtf, vibe, quasar, potentones, karaoke). |
| Odd ones out? | **121** no-lyrics songs in otherwise-processed playlists — mostly cringe (38) and X-POP (24), incl. 10 of the 11. |
| Do the 128 fold into the 2372? | **9 yes (renames), 119 no (genuinely novel with lyrics).** |
| Any missing files? | **No** — 15 renamed, 83 intentionally removed. |
---

# v3 — Record Cleanup (2026-08-26)

## What changed
`processed_songs.txt` was cleaned from **2352 → 2212 entries** (backup saved at
`processed_songs.txt.bak`).

## Removed (140 entries total)
| Reason | Count | Detail |
|---|---|---|
| **Missing file** | 83 | File no longer exists anywhere (intentionally removed) |
| **No lyrics** | 10 | In record but file has NO USLT lyrics frame (the 11, minus ELO — ELO has lyrics in the old party/ duplicate) |
| **Junk lyrics metadata** | 41 | Lyrics frame contains garbage — mostly a single `.` character (placeholder), plus watermarks like `[Dj MaX]only-exclusive.ru` and `[Instrumental]` stubs |

**Plus 9 renames applied** — old record names replaced with current filenames
(e.g. `Caravan Palace -  Reverse.mp3` → `Caravan Palace - Reverse.mp3`), so the
renamed-with-lyrics songs stay in the record under their real names.

## Junk-lyrics files found (< 40 chars) — 43 total
40 files have lyrics = just `.` — these are placeholder junk, not real lyrics.
They were previously **counted as "with lyrics"** in the 2372 because a USLT
frame existed, but they're effectively empty. Examples:

```
vibe/Dave Brubeck, The Dave Brubeck Quartet - Take Five.mp3
iron/Eruption - Van Halen.mp3
karaoke/Superman (Instrumental) - Eminem.mp3
guitar solos/Sirius - The Alan Parsons Project.mp3
edm drop/deadmau5 & Wolfgang Gartner - Channel 43.mp3
wtf/Polyphia - G.O.A.T..mp3
```

Plus 3 non-`.` junk entries:
- `lovely/Iyaz - Replay.mp3` → `BMF` (3 chars)
- `edm drop/Parov Stelar - Catgroove.mp3` → `[Instrumental] | Rock my body (x4)` (33)
- `robot seizure/Chuckie Feat. Gregor Salto - What Happens In Vegas.mp3` → `[Dj MaX]only-exclusive.ru[Dj MaX]` (33 — a watermark)

## The 128 audit (correct-lyrics check)
- **126 of the 128 have real lyrics (≥40 chars)** — these are the novel songs to
  verify one-by-one.
- **2 have junk lyrics** and should be removed from consideration:
  - `lovely/Iyaz - Replay.mp3` → `BMF`
  - `robot seizure/Chuckie Feat. Gregor Salto - What Happens In Vegas.mp3` → watermark

## Corrected totals (after junk filter)
| Metric | Before | After |
|---|---|---|
| Files with real lyrics (≥40 chars) | 2372 (inflated) | **2329** |
| Junk-lyrics files | — | 43 |
| Record size | 2352 | **2212** |

## What the program will now do
With the cleaned record, running `Lyrics.py` (after fixing its path to
`/media/shaarky/Data/Shaarav/playlists/` + `os.walk()`) will:
- ✅ Process all 791 no-lyrics songs
- ✅ Re-process the 10 lost-lyrics songs (removed from record)
- ✅ Re-process the 41 junk-lyrics songs (removed from record)
- ⚠️ Re-prompt on the 126 novel songs with lyrics (they're not in the record) —
  exactly what you want to verify one-by-one
- ✅ Skip the 2212 songs with verified real lyrics

## Files
- `processed_songs.txt` — cleaned (2212)
- `processed_songs.txt.bak` — original (2352)
- `/tmp/opencode/removed_missing_file.txt`, `removed_no_lyrics.txt`, `removed_junk_lyrics.txt`
- `/tmp/opencode/audit_128.txt` — full 128 audit (126 ok / 2 junk)
