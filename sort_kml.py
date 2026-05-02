#!/usr/bin/env python3
"""
sort_kml.py — Sorts Folder and Placemark children alphabetically by name
at every level of the KML tree, preserving Style/StyleMap order.

Usage:
    python3 sort_kml.py                     # sorts Photo Geocoding.kml in-place
    python3 sort_kml.py input.kml           # sorts input.kml in-place
    python3 sort_kml.py input.kml out.kml   # writes sorted output to out.kml
"""

import re
import sys
from pathlib import Path

INPUT_DEFAULT = Path(__file__).parent / "Photo Geocoding.kml"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_close(text: str, start: int, tag: str) -> int:
    """
    Given that text[start:] begins with an opening <tag …> element, return
    the index *after* the matching closing </tag>.  Handles nesting.
    """
    open_pat = re.compile(rf"<{re.escape(tag)}(?:\s[^>]*)?>")
    close_pat = re.compile(rf"</{re.escape(tag)}>")

    # Skip past the opening tag itself
    open_m = open_pat.match(text, start)
    assert open_m, f"Expected <{tag}> at position {start}"
    pos = open_m.end()
    depth = 1  # we have consumed one opening tag

    while depth > 0:
        open_m = open_pat.search(text, pos)
        close_m = close_pat.search(text, pos)

        if close_m is None:
            raise ValueError(f"Unmatched <{tag}> starting at position {start}")

        if open_m is not None and open_m.start() < close_m.start():
            depth += 1
            pos = open_m.end()
        else:
            depth -= 1
            pos = close_m.end()

    return pos  # position after </tag>


def _get_name(block: str) -> str:
    """Return the first <name>…</name> text, lowercased, for sort key."""
    m = re.search(r"<name>(.*?)</name>", block, re.DOTALL)
    return m.group(1).strip().lower() if m else ""


# ---------------------------------------------------------------------------
# Core sort logic
# ---------------------------------------------------------------------------

def _sort_children(content: str) -> str:
    """
    Within `content` (the inner text of a Folder), tokenise all immediate
    Folder/Placemark children, sort them alphabetically by <name>, recurse
    into sub-Folders, and return the re-assembled string.

    Non-sortable text (whitespace, <name>, <open>, etc.) is preserved in
    two buckets: a prefix (before the first sortable block) and inter-block
    whitespace spacers.
    """
    tokens: list = []  # alternating: str (literal) | tuple(tag, block_str)

    i = 0
    while i < len(content):
        m = re.search(r"<(Folder|Placemark)(?:\s[^>]*)?>", content[i:])
        if not m:
            tokens.append(content[i:])
            break

        before = content[i : i + m.start()]
        if before:
            tokens.append(before)

        tag = m.group(1)
        block_start = i + m.start()
        block_end = _find_close(content, block_start, tag)
        tokens.append((tag, content[block_start:block_end]))
        i = block_end

    # Identify first / last sortable token indices
    sortable_indices = [k for k, t in enumerate(tokens) if isinstance(t, tuple)]
    if not sortable_indices:
        return content

    first_s, last_s = sortable_indices[0], sortable_indices[-1]

    prefix = "".join(t for t in tokens[:first_s] if isinstance(t, str))
    suffix = "".join(t for t in tokens[last_s + 1:] if isinstance(t, str))

    # Collect blocks and inter-block whitespace spacers in order
    blocks: list[tuple[str, str]] = []
    spacers: list[str] = []
    for k in range(first_s, last_s + 1):
        t = tokens[k]
        if isinstance(t, tuple):
            blocks.append(t)
        else:
            spacers.append(t)

    # Recurse into sub-Folders
    recursed: list[tuple[str, str]] = []
    for tag, blk in blocks:
        if tag == "Folder":
            open_m = re.match(r"<Folder(?:\s[^>]*)?>", blk)
            assert open_m
            inner_start = open_m.end()
            inner_end = blk.rfind("</Folder>")
            inner = blk[inner_start:inner_end]
            blk = blk[:inner_start] + _sort_children(inner) + blk[inner_end:]
        recursed.append((tag, blk))

    # Sort alphabetically by <name>
    recursed.sort(key=lambda tb: _get_name(tb[1]))

    # Re-assemble with original inter-block whitespace
    parts = [prefix]
    for idx, (_, blk) in enumerate(recursed):
        parts.append(blk)
        if idx < len(spacers):
            parts.append(spacers[idx])
        elif idx < len(recursed) - 1:
            parts.append("\n")
    parts.append(suffix)

    return "".join(parts)


def kml_stats(text: str) -> None:
    """Print summary statistics about the sorted KML."""
    # Total placemarks
    place_count = len(re.findall(r"<Placemark(?:\s[^>]*)?>", text))
    print(f"  Places  : {place_count}")

    # Total folders (excluding the single root folder)
    folder_count = len(re.findall(r"<Folder(?:\s[^>]*)?>", text)) - 1
    print(f"  Folders : {folder_count}")

    # Names of the top-level regions (direct Folder children of the root folder)
    root_m = re.search(r"<Folder(?:\s[^>]*)?>", text)
    if root_m:
        root_end = _find_close(text, root_m.start(), "Folder")
        root_open_end = root_m.end()
        root_inner = text[root_open_end : root_end - len("</Folder>")]
        top_names = []
        i = 0
        while True:
            fm = re.search(r"<Folder(?:\s[^>]*)?>", root_inner[i:])
            if not fm:
                break
            fstart = i + fm.start()
            fend = _find_close(root_inner, fstart, "Folder")
            block = root_inner[fstart:fend]
            name_m = re.search(r"<name>(.*?)</name>", block, re.DOTALL)
            if name_m:
                top_names.append(name_m.group(1).strip())
            i = fend
        print(f"  Regions : {', '.join(top_names)}")

    # Folder with the most placemarks (excluding the root)
    # Advance by 1 past each opening tag so nested folders are all visited.
    i = 0
    folder_counts: list[tuple[str, int]] = []
    while True:
        fm = re.search(r"<Folder(?:\s[^>]*)?>", text[i:])
        if not fm:
            break
        fstart = i + fm.start()
        fend = _find_close(text, fstart, "Folder")
        block = text[fstart:fend]
        count = len(re.findall(r"<Placemark(?:\s[^>]*)?>", block))
        name_m = re.search(r"<name>(.*?)</name>", block, re.DOTALL)
        folder_counts.append((name_m.group(1).strip() if name_m else "?", count))
        i = fstart + 1  # step past opening tag only, so nested folders are found

    # Sort descending; index 0 is the root (contains everything), skip it
    folder_counts.sort(key=lambda x: x[1], reverse=True)
    if len(folder_counts) > 1:
        busiest_name, busiest_count = folder_counts[1]
        print(f"  Busiest : {busiest_name} ({busiest_count} places)")


def sort_kml(text: str) -> str:
    """
    Sort Folder and Placemark blocks at every nesting level, alphabetically
    by the text of their first <name> child element.

    Style/StyleMap blocks are left in place (they appear before the Folder
    tree and have no <name> that needs ordering relative to placemarks).
    """
    folder_m = re.search(r"<Folder(?:\s[^>]*)?>", text)
    if not folder_m:
        print("No <Folder> found – nothing to sort.", file=sys.stderr)
        return text

    folder_start = folder_m.start()
    folder_end = _find_close(text, folder_start, "Folder")
    folder_text = text[folder_start:folder_end]

    open_m = re.match(r"<Folder(?:\s[^>]*)?>", folder_text)
    assert open_m
    inner_start = open_m.end()
    inner_end = folder_text.rfind("</Folder>")
    inner = folder_text[inner_start:inner_end]

    sorted_folder = folder_text[:inner_start] + _sort_children(inner) + folder_text[inner_end:]
    return text[:folder_start] + sorted_folder + text[folder_end:]


def main() -> None:
    args = sys.argv[1:]

    if len(args) == 0:
        input_path = INPUT_DEFAULT
        output_path = INPUT_DEFAULT
    elif len(args) == 1:
        input_path = Path(args[0])
        output_path = input_path
    elif len(args) == 2:
        input_path = Path(args[0])
        output_path = Path(args[1])
    else:
        print("Usage: sort_kml.py [input.kml [output.kml]]", file=sys.stderr)
        sys.exit(1)

    print(f"Reading {input_path} …")
    text = input_path.read_text(encoding="utf-8")

    print("Sorting …")
    sorted_text = sort_kml(text)

    print("Stats:")
    kml_stats(sorted_text)

    print(f"Writing {output_path} …")
    output_path.write_text(sorted_text, encoding="utf-8")
    print("Done.")


if __name__ == "__main__":
    main()
