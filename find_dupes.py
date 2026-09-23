#!/usr/bin/env python3
"""find_dupes.py — find likely-duplicate MP3 files by name matching.

Scans a folder tree for `.mp3` files, normalizes each filename into an
(artist, title) pair, matches titles against each other with fuzzy
string comparison, and writes a self-contained HTML report grouping
near-duplicate files for manual review.

The script NEVER deletes, moves, or modifies any file. It only reads
file metadata (size + MD5 for exact duplicates) and writes the report.

Usage:
    python find_dupes.py <folder> [--threshold 90] [--out report.html]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import html
import itertools
import json
import os
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

try:
    from rapidfuzz import fuzz
except ImportError:
    sys.stderr.write("rapidfuzz is required: pip install rapidfuzz\n")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Tiers
# ---------------------------------------------------------------------------

TIER_EXACT = 0
TIER_STRONG = 1
TIER_MEDIUM = 2
TIER_VARIANT = 3

TIER_NAMES = {
    TIER_EXACT: "exact",
    TIER_STRONG: "strong",
    TIER_MEDIUM: "medium",
    TIER_VARIANT: "variant",
}

TIER_ORDER = [TIER_EXACT, TIER_STRONG, TIER_MEDIUM, TIER_VARIANT]


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

TRACK_RE = re.compile(r"^\d{1,2}\s*[-.]\s+")
BRACKET_RE = re.compile(r"\[.*?\]|\(.*?\)|﹝.*?﹞|〔.*?〕|【.*?】")
# Keep: a-z 0-9, whitespace, & - – — | : , .
FILTER_RE = re.compile(r"[^a-z0-9&\s\-–—|:,.]+")
WS_RE = re.compile(r"\s+")
SEP_RE = re.compile(r"\s+[-–—|:]|[-–—|:]\s+")
SEPARATOR_CHARS = frozenset("-–—|:")
# Artist agreement compares normalized artist strings: ",", "&" join names
# ("Missio, Shug", "bbno$ & Rebecca Black") and must read as word separators
# for rapidfuzz's whitespace tokenizer ("missio" ~ "missio shug").
ARTIST_CLEAN_RE = re.compile(r"[,&]+")

# Feat markers, longest first so e.g. "featuring" wins over "feat".
FEAT_MARKERS = ("produced by", "featuring", "prod", "feat", "ft", "with")

STOPWORDS = frozenset(
    "the a an and or of to for on in at by with without "
    "feat ft featuring vs from so its it's".split()
)

# Single-word variant markers ("Hello" vs "Hello Sped Up" -> leftover must
# be one of these, or a phrase marker, or a file's own 2+-separator parts).
# Only high-signal tags: generic English words (clean, radio, edit, version,
# original, mix, official, audio, ...) are deliberately EXCLUDED because they
# are common real title words ("So Fresh So Clean" must not variant-match
# "Fresh"). Bracket-style tags like "(Clean)" are stripped before this.
MARKER_WORDS = frozenset(
    "sped slowed reverb nightcore 8d remix extended live acoustic piano "
    "instrumental karaoke remaster remastered deluxe bonus demo cover vip "
    "mashup acapella cappella".split()
)
PHRASE_MARKERS = frozenset({"sped up"})


def _find_feat_marker(s: str) -> Optional[tuple[int, int]]:
    """Return (start, end) of the earliest valid feat marker in *s*, or None.

    A marker is valid when it starts at a word boundary and (for "with") is
    followed by a space + word + optional comma/&.
    """
    best: Optional[tuple[int, int]] = None
    for marker in FEAT_MARKERS:
        start = 0
        while True:
            idx = s.find(marker, start)
            if idx == -1:
                break
            # Word boundary before the marker.
            if idx > 0 and (s[idx - 1].isalnum() or s[idx - 1] == "_"):
                start = idx + 1
                continue
            after = idx + len(marker)
            if marker == "with":
                # "with" must be followed by " <word>[ , | & ]" or end-of-title.
                if not re.match(r"\s+[a-z0-9]+(?:\s*[,&]\s*|\s*$)", s[after:]):
                    start = idx + 1
                    continue
            else:
                # Not followed by a letter/digit ("feat" inside "featured").
                if after < len(s) and s[after].isalnum():
                    start = idx + 1
                    continue
            if best is None or idx < best[0]:
                best = (idx, after)
            break
    return best


def strip_feat_sections(s: str) -> str:
    """Remove 'feat. X' / 'ft. Y' / 'prod. Z' sections from *s*.

    Each section runs from the marker to the next separator char or the
    end of the string. Only the section is removed, never the whole name.
    """
    while True:
        hit = _find_feat_marker(s)
        if hit is None:
            return s
        start, _end = hit
        nxt = len(s)
        for i in range(start, len(s)):
            if s[i] in SEPARATOR_CHARS:
                nxt = i
                break
        s = s[:start] + " " + s[nxt:]


def normalize_name(stem: str) -> str:
    """Return the fully de-noised lowercase name for a filename stem."""
    s = TRACK_RE.sub("", stem)
    # Remove bracketed/parenthesized content FIRST, before NFKD/ASCII: the
    # ascii-encode step would silently drop unicode brackets (﹝﹞ etc.) and
    # glue the surrounding words together, and the char filter would destroy
    # the brackets/parens we rely on to find their content.
    s = BRACKET_RE.sub(" ", s)
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = s.replace("'", "").replace("$", "")
    s = FILTER_RE.sub(" ", s)
    # Drop "." everywhere: "will.i.am" -> "william", "Anderson .Paak" -> "paak".
    s = s.replace(".", "")
    s = strip_feat_sections(s)
    return WS_RE.sub(" ", s).strip()


def split_parts(s: str) -> tuple[str, ...]:
    """Split on separator chars (- – — | :) that have whitespace on a side.

    Empty parts are KEPT: a file like "GRANRODEO - " lost its (non-Latin)
    title to ASCII normalization, leaving a dangling separator; keeping the
    empty part means the file has no usable title and never matches anything.
    """
    return tuple(p.strip() for p in SEP_RE.split(s))


def tokenize_title(title: str) -> tuple[frozenset[str], tuple[str, ...]]:
    """Return (significant token set, ordered significant tokens).

    Tokens are plain [a-z0-9]+ words so punctuation never sticks to them.
    """
    words = re.findall(r"[a-z0-9]+", title)
    sig = [w for w in words if w not in STOPWORDS]
    return frozenset(sig), tuple(sig)


def human_size(n: int) -> str:
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    return f"{n / 1024:.1f} KB"


# ---------------------------------------------------------------------------
# Records & orientation
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Arrangement:
    artist: Optional[str]  # normalized artist part string, or None
    title_raw: str  # normalized title part string
    title_full: str  # significant tokens joined ("fuzz" input)
    title_tokens: frozenset[str]
    title_order: tuple[str, ...]


@dataclass(slots=True)
class FileRecord:
    idx: int
    path: str
    rel_path: str
    name: str
    folder: str
    size: int
    md5: Optional[str]
    norm: str
    parts: tuple[str, ...]
    arrangements: tuple[Arrangement, ...] = ()
    variant_tokens: frozenset[str] = frozenset()
    ambiguous: bool = False
    display_artist: Optional[str] = None


def _arr(artist: Optional[str], title: str) -> Arrangement:
    tokens, order = tokenize_title(title)
    return Arrangement(
        artist=artist,
        title_raw=title,
        title_full=" ".join(order),
        title_tokens=tokens,
        title_order=order,
    )


def orient_record(rec: FileRecord, artist_like: frozenset[str]) -> None:
    """Populate *rec*'s arrangements based on the artist-consensus set."""
    parts = rec.parts
    n = len(parts)
    if n == 1:
        rec.arrangements = (_arr(None, parts[0]),)
        rec.display_artist = None
        return
    if n == 2:
        # Artist-consensus decides orientation.
        a_like = parts[0] in artist_like
        b_like = parts[1] in artist_like
        if a_like and not b_like:
            rec.arrangements = (_arr(parts[0], parts[1]),)
            rec.display_artist = parts[0]
        elif b_like and not a_like:
            rec.arrangements = (_arr(parts[1], parts[0]),)
            rec.display_artist = parts[1]
        else:
            # Neither part is artist-like, or both are: orientation is
            # uncertain, so keep both arrangements and flag the file ambiguous
            # so the matcher never trusts an arrangement whose "title" could
            # be the other part's artist (the artist-leak pattern).
            rec.arrangements = (_arr(parts[0], parts[1]), _arr(parts[1], parts[0]))
            rec.ambiguous = True
            rec.display_artist = None
        return
    # n >= 3: first part = artist, second = title, rest = variant tags.
    rec.arrangements = (_arr(parts[0], parts[1]),)
    rec.variant_tokens = frozenset(w for p in parts[2:] for w in p.split())
    rec.display_artist = parts[0]


def md5_of(path: str) -> Optional[str]:
    try:
        h = hashlib.md5()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError as exc:
        sys.stderr.write(f"warning: cannot read {path}: {exc}\n")
        return None


def collect_files(root: str) -> list[str]:
    paths: list[str] = []

    def onerror(exc: OSError) -> None:
        sys.stderr.write(f"warning: cannot enter {exc.filename}: {exc.strerror}\n")

    for dirpath, _dirnames, filenames in os.walk(root, onerror=onerror):
        for fn in sorted(filenames):
            if fn.lower().endswith(".mp3"):
                paths.append(os.path.join(dirpath, fn))
    return sorted(paths)


def build_records(paths: list[str], root: str) -> list[FileRecord]:
    """Stat + hash + normalize + orient every file into a FileRecord."""
    records: list[FileRecord] = []
    for i, path in enumerate(paths):
        try:
            size = os.path.getsize(path)
        except OSError as exc:
            sys.stderr.write(f"warning: cannot stat {path}: {exc}\n")
            continue
        stem = os.path.basename(path)[:-4]
        records.append(
            FileRecord(
                idx=len(records),
                path=path,
                rel_path=os.path.relpath(path, root),
                name=os.path.basename(path),
                folder=os.path.dirname(os.path.relpath(path, root)) or ".",
                size=size,
                md5=None,
                norm=normalize_name(stem),
                parts=split_parts(normalize_name(stem)),
            )
        )

    # MD5 only for size buckets with 2+ members (rarely needed, saves IO).
    by_size: dict[int, list[FileRecord]] = {}
    for rec in records:
        by_size.setdefault(rec.size, []).append(rec)
    total = sum(1 for v in by_size.values() if len(v) >= 2)
    done = 0
    for group in by_size.values():
        if len(group) < 2:
            continue
        for rec in group:
            rec.md5 = md5_of(rec.path)
            done += 1
            if done % 200 == 0:
                sys.stderr.write(f"hashing {done}/{total}\n")

    # Artist-consensus: only the LEFT part of a multi-part name is in artist
    # position by convention, so only left-side parts with >= 3 occurrences are
    # "artist-like". Counting ALL parts lets popular TITLE words (a title
    # appearing in 3+ files, e.g. "closer", "monster") masquerade as artists
    # and mis-orients files like "Ne-Yo - Closer" backwards. Empty parts (a
    # title lost to ASCII normalization) are never artists.
    counts: Counter[str] = Counter()
    for rec in records:
        if len(rec.parts) >= 2 and rec.parts[0]:
            counts[rec.parts[0]] += 1
    artist_like = frozenset(p for p, c in counts.items() if c >= 3)
    for rec in records:
        orient_record(rec, artist_like)
    return records


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PairMatch:
    a: int
    b: int
    tier: int
    score: float
    title_a: str
    title_b: str


@dataclass(frozen=True, slots=True)
class Group:
    tier: int
    max_score: float
    title: str
    mix: frozenset[int]
    member_paths: tuple[int, ...]
    members: tuple[int, ...]


def artists_agree(a: Optional[str], b: Optional[str]) -> Optional[bool]:
    if a is None or b is None:
        return None
    return fuzz.token_set_ratio(
        ARTIST_CLEAN_RE.sub(" ", a), ARTIST_CLEAN_RE.sub(" ", b)
    ) >= 85


def is_variant_leftover(
    large_order: tuple[str, ...],
    small_tokens: frozenset[str],
    extra_allowed: frozenset[str],
) -> bool:
    """True if the extra tokens of the larger title are all markers/tags."""
    leftover = [t for t in large_order if t not in small_tokens]
    i = 0
    while i < len(leftover):
        if " ".join(leftover[i : i + 2]) in PHRASE_MARKERS:
            i += 2
            continue
        if leftover[i] in MARKER_WORDS or leftover[i] in extra_allowed:
            i += 1
            continue
        return False
    return True


def exact_groups(records: list[FileRecord]) -> tuple[list[Group], set[int]]:
    """Group byte-identical files; return (groups, ids to skip in matching)."""
    by_key: dict[tuple[int, str], list[FileRecord]] = {}
    for rec in records:
        if rec.md5 is not None:
            by_key.setdefault((rec.size, rec.md5), []).append(rec)
    groups: list[Group] = []
    skip: set[int] = set()
    for key, members in by_key.items():
        if len(members) < 2:
            continue
        ids = tuple(sorted(r.idx for r in members))
        groups.append(
            Group(TIER_EXACT, 100.0, members[0].norm, frozenset({TIER_EXACT}), ids, ids)
        )
        skip.update(ids)
    return groups, skip


def match_all(
    records: list[FileRecord], threshold: int, skip: set[int]
) -> list[PairMatch]:
    """Name-match non-exact records via an inverted token index."""
    active = [r.idx for r in records if r.idx not in skip and r.arrangements]
    index: dict[str, set[int]] = {}
    for i in active:
        for arr in records[i].arrangements:
            for tok in arr.title_tokens:
                if len(tok) >= 2:
                    index.setdefault(tok, set()).add(i)

    pairs: set[tuple[int, int]] = set()
    for ids in index.values():
        if len(ids) >= 2:
            pairs.update(itertools.combinations(sorted(ids), 2))

    results: list[PairMatch] = []
    for a, b in pairs:
        ra, rb = records[a], records[b]
        both_ambiguous = ra.ambiguous and rb.ambiguous
        any_ambiguous = ra.ambiguous or rb.ambiguous

        # All arrangement combos, best gate first. The artist-leak pattern
        # ("artist - song1" vs "artist - song2" where a rare artist appears in
        # only 2 files) shows up as an ambiguous-ambiguous combo whose titles
        # agree but whose artists don't: the matched "title" is actually the
        # shared artist name. Such combos must never produce a title match.
        combos: list[tuple[float, Arrangement, Arrangement]] = []
        for arr_a in ra.arrangements:
            for arr_b in rb.arrangements:
                if not arr_a.title_full and not arr_b.title_full:
                    continue
                gate = fuzz.ratio(arr_a.title_full, arr_b.title_full)
                combos.append((gate, arr_a, arr_b))
        combos.sort(key=lambda c: c[0], reverse=True)

        for gate, arr_a, arr_b in combos:
            agree = artists_agree(arr_a.artist, arr_b.artist)
            if gate >= threshold:
                if both_ambiguous and agree is False:
                    continue  # artist-leak combo; try lower-scoring arrangements
                # STRONG: artists agree or unknown. MEDIUM: artists differ.
                tier = TIER_STRONG if agree is not False else TIER_MEDIUM
                results.append(
                    PairMatch(a, b, tier, float(gate), arr_a.title_raw, arr_b.title_raw)
                )
                break

            # gate < threshold: only the best combo may be a variant match.
            la, lb = arr_a.title_tokens, arr_b.title_tokens
            extra = ra.variant_tokens | rb.variant_tokens
            if la < lb:
                ok = is_variant_leftover(arr_b.title_order, la, extra)
            elif lb < la:
                ok = is_variant_leftover(arr_a.title_order, lb, extra)
            else:
                ok = False
            # A variant match through an ambiguous file is only trustworthy when
            # the artists agree or are unknown; otherwise the matched "title"
            # may be the other file's artist name ("KUURO - Swarm VIP" must not
            # match "Take Me to Hell - SWARM").
            if ok and not (any_ambiguous and agree is False):
                set_sim = fuzz.token_set_ratio(arr_a.title_full, arr_b.title_full)
                results.append(
                    PairMatch(a, b, TIER_VARIANT, float(set_sim), arr_a.title_raw, arr_b.title_raw)
                )
            break

    return results


def union_find(pairs: list[PairMatch], n: int) -> list[Group]:
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        parent[find(x)] = find(y)

    for p in pairs:
        union(p.a, p.b)

    comps: dict[int, list[PairMatch]] = {}
    for p in pairs:
        comps.setdefault(find(p.a), []).append(p)

    groups: list[Group] = []
    for ps in comps.values():
        tier = min(p.tier for p in ps)
        best = max(ps, key=lambda p: p.score)
        title = min((best.title_a, best.title_b), key=len)
        members = tuple(sorted({p.a for p in ps} | {p.b for p in ps}))
        groups.append(
            Group(
                tier=tier,
                max_score=best.score,
                title=title,
                mix=frozenset(p.tier for p in ps),
                member_paths=members,
                members=members,
            )
        )
    groups.sort(key=lambda g: (g.tier, -g.max_score))
    return groups


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Duplicate MP3 finder — report for __FOLDER__</title>
<style>
  body { font-family: system-ui, -apple-system, sans-serif; margin: 2rem auto;
         max-width: 1100px; padding: 0 1rem; color: #222; }
  h1 { font-size: 1.3rem; }
  .muted { color: #6b7280; }
  #toolbar { position: sticky; top: 0; background: #fff; padding: .5rem 0;
             border-bottom: 1px solid #e5e7eb; z-index: 10; }
  button { padding: .4rem .8rem; cursor: pointer; }
  section { margin-top: 1.5rem; }
  h2 { font-size: 1.05rem; border-bottom: 2px solid #eee; padding-bottom: .3rem; }
  .note { color: #6b7280; font-size: .85rem; margin: .3rem 0 .8rem; }
  .group { border: 1px solid #e5e7eb; border-radius: 6px; margin-bottom: .8rem;
           overflow: hidden; }
  .group-header { display: flex; align-items: center; gap: .6rem; padding: .5rem .8rem;
                  background: #f9fafb; font-size: .9rem; flex-wrap: wrap; }
  .group-info { font-weight: 600; }
  .mix { font-weight: 400; font-style: italic; }
  .badge { padding: .1rem .5rem; border-radius: 999px; color: #fff;
           font-size: .75rem; font-weight: 600; }
  .badge.exact { background: #1a7f37; }
  .badge.strong { background: #1f6feb; }
  .badge.medium { background: #b45309; }
  .badge.variant { background: #8250df; }
  table { width: 100%; border-collapse: collapse; }
  td { padding: .35rem .6rem; border-top: 1px solid #f3f4f6; font-size: .88rem;
       vertical-align: top; }
  tr:nth-child(even) td { background: #fcfcfd; }
  td.name { font-weight: 500; }
  td.muted { color: #6b7280; }
  td.folder { color: #6b7280; word-break: break-all; }
  a { color: #1f6feb; text-decoration: none; }
  pre#copied { background: #f3f4f6; padding: .8rem; overflow-x: auto;
               font-size: .8rem; }
  details { display: inline-block; margin-left: .8rem; }
</style>
</head>
<body>
<h1>Duplicate MP3 finder — report for <span class="muted">__FOLDER__</span></h1>
<p class="muted">Generated __TIMESTAMP__ — <span id="summary"></span></p>
<div id="toolbar">
  <button id="copy">Copy checked paths to clipboard</button>
  <span id="count" class="muted">0 checked</span>
  <details><summary>Copied paths</summary><pre id="copied"></pre></details>
</div>
<div id="sections">
  <section data-section="exact">
    <h2>Exact duplicates</h2>
    <p class="note">Byte-identical files (same size + MD5).</p><div class="groups"></div>
  </section>
  <section data-section="strong">
    <h2>High confidence</h2>
    <p class="note">Same title, same artist (handles &ldquo;Artist - Song&rdquo; vs &ldquo;Song - Artist&rdquo;).</p>
    <div class="groups"></div>
  </section>
  <section data-section="medium">
    <h2>Medium confidence</h2>
    <p class="note">Same title, different or unknown artist &mdash; verify these.</p>
    <div class="groups"></div>
  </section>
  <section data-section="variant">
    <h2>Variants</h2>
    <p class="note">One name is a marker/stopword variant of the other (remix, sped up, live&hellip;).</p>
    <div class="groups"></div>
  </section>
</div>
<script>
const DATA = __DATA__;
const TIERS = ["exact", "strong", "medium", "variant"];
const LABELS = { exact: "Exact", strong: "High", medium: "Medium", variant: "Variant" };

function shellQuote(p) { return "'" + p.replace(/'/g, "'\\\\''") + "'"; }

function updateCount() {
  document.getElementById("count").textContent =
    document.querySelectorAll(".dup-check:checked").length + " checked";
}

function makeRow(f) {
  const tr = document.createElement("tr");
  const tdCheck = document.createElement("td");
  const cb = document.createElement("input");
  cb.type = "checkbox";
  cb.className = "dup-check";
  cb.dataset.path = f.path;
  cb.addEventListener("change", updateCount);
  tdCheck.appendChild(cb);
  tr.appendChild(tdCheck);

  const tdName = document.createElement("td");
  tdName.className = "name";
  tdName.textContent = f.name;
  tr.appendChild(tdName);

  const tdSize = document.createElement("td");
  tdSize.textContent = f.size_hr;
  tr.appendChild(tdSize);

  const tdFolder = document.createElement("td");
  tdFolder.className = "folder";
  tdFolder.textContent = f.folder;
  tr.appendChild(tdFolder);

  const tdArtist = document.createElement("td");
  tdArtist.className = "muted";
  tdArtist.textContent = f.artist === null ? "?" : f.artist;
  tr.appendChild(tdArtist);

  const tdOpen = document.createElement("td");
  const a = document.createElement("a");
  a.href = "file://" + f.path;
  a.target = "_blank";
  a.rel = "noopener";
  a.textContent = "open";
  tdOpen.appendChild(a);
  tr.appendChild(tdOpen);
  return tr;
}

function makeGroup(num, g, tier) {
  const wrap = document.createElement("div");
  wrap.className = "group " + tier;
  const header = document.createElement("div");
  header.className = "group-header";

  const badge = document.createElement("span");
  badge.className = "badge " + tier;
  badge.textContent = LABELS[tier];
  header.appendChild(badge);

  const info = document.createElement("span");
  info.className = "group-info";
  info.textContent = "Group " + num + " \u2014 " + g.files.length +
    " files \u2014 title: '" + g.title + "' \u2014 max score " + g.max_score;
  header.appendChild(info);

  if (g.mix.length > 1) {
    const mix = document.createElement("span");
    mix.className = "mix muted";
    mix.textContent = "(mix: " + g.mix.map(t => LABELS[t]).join(" + ") + ")";
    header.appendChild(mix);
  }
  wrap.appendChild(header);

  const table = document.createElement("table");
  for (const f of g.files) table.appendChild(makeRow(f));
  wrap.appendChild(table);
  return wrap;
}

function render() {
  const byTier = { exact: [], strong: [], medium: [], variant: [] };
  for (const g of DATA.groups) byTier[g.tier].push(g);
  let num = 0;
  for (const tier of TIERS) {
    const section = document.querySelector('[data-section="' + tier + '"]');
    const container = section.querySelector(".groups");
    const list = byTier[tier];
    if (!list.length) {
      const p = document.createElement("p");
      p.className = "muted";
      p.textContent = "None found.";
      container.appendChild(p);
      continue;
    }
    for (const g of list) {
      num += 1;
      container.appendChild(makeGroup(num, g, tier));
    }
  }
  document.getElementById("summary").textContent =
    DATA.n_files + " mp3 files, " + DATA.n_groups + " duplicate group(s)";
}

document.getElementById("copy").addEventListener("click", async function () {
  const paths = Array.from(document.querySelectorAll(".dup-check:checked"))
    .map(cb => cb.dataset.path);
  const text = paths.map(shellQuote).join("\\n");
  document.getElementById("copied").textContent = text;
  try {
    await navigator.clipboard.writeText(text);
  } catch (e) {
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
  }
});

render();
</script>
</body>
</html>
"""


def _js_safe(obj) -> str:
    """JSON with < > & escaped so the data is inert inside <script>."""
    return json.dumps(obj, ensure_ascii=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def build_report(
    folder: str, records: list[FileRecord], groups: list[Group], n_files: int
) -> str:
    by_idx = {r.idx: r for r in records}
    group_data = []
    for g in groups:
        files = []
        for i in g.members:
            r = by_idx[i]
            files.append(
                {
                    "path": r.path,
                    "name": r.name,
                    "folder": r.folder,
                    "size_hr": human_size(r.size),
                    "artist": r.display_artist,
                }
            )
        group_data.append(
            {
                "tier": TIER_NAMES[g.tier],
                "title": g.title or "(untitled)",
                "max_score": round(g.max_score, 1),
                "mix": sorted(TIER_NAMES[t] for t in g.mix),
                "files": files,
            }
        )
    data = {
        "n_files": n_files,
        "n_groups": len(group_data),
        "groups": group_data,
    }
    stamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        _HTML_TEMPLATE.replace("__FOLDER__", html.escape(folder))
        .replace("__TIMESTAMP__", stamp)
        .replace("__DATA__", _js_safe(data))
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Find likely-duplicate MP3 files by name matching and "
        "write an HTML report for manual review. Never deletes anything."
    )
    parser.add_argument("folder", help="root folder to scan recursively")
    parser.add_argument("--threshold", type=int, default=90,
                        help="title similarity cutoff for high confidence (0-100, default 90)")
    parser.add_argument("--out", default="dupes-report.html",
                        help="output report path (default dupes-report.html)")
    args = parser.parse_args(argv)

    if not os.path.isdir(args.folder):
        sys.stderr.write(f"error: not a directory: {args.folder}\n")
        return 1

    paths = collect_files(args.folder)
    records = build_records(paths, args.folder)
    exact, skip = exact_groups(records)
    pairs = match_all(records, args.threshold, skip)
    groups = union_find(pairs, len(records))
    all_groups = exact + groups

    html_text = build_report(args.folder, records, all_groups, len(records))
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html_text)

    counts = {t: sum(1 for g in all_groups if g.tier == t) for t in TIER_ORDER}
    print(f"Scanned {len(records)} mp3 files")
    for t in TIER_ORDER:
        print(f"  {TIER_NAMES[t]:8s}: {counts[t]} group(s)")
    print(f"Report: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
