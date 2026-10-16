"""Shows which line endings text files use.

Run: python lineends.py file FILE
     python lineends.py folder FOLDER
Exit code: 0 = no file mixes line endings, 1 = some file does, 2 = could not read.
It only reads files. It never changes, renames or creates one.
"""
import os
import sys
import stat
from pathlib import Path

TEXT_TYPES = (".txt", ".md", ".py", ".csv", ".json", ".html", ".css", ".js")
SHOW = 20  # how many files to print


def count_endings(data):
    """Return (crlf, lf, cr): how many line endings of each kind are in the bytes."""
    crlf = data.count(b"\r\n")
    return crlf, data.count(b"\n") - crlf, data.count(b"\r") - crlf


def label(crlf, lf, cr):
    kinds = [name for name, n in (("CRLF", crlf), ("LF", lf), ("CR", cr)) if n]
    if not kinds:
        return "no line endings"
    if len(kinds) == 1:
        return kinds[0]
    return "mixed"


def safe_input(value, directory=False):
    path = Path(value).absolute()
    if '..' in path.parts:
        raise OSError('Parent-traversal paths are unsupported.')
    for part in [*reversed(path.parents), path]:
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info,'st_file_attributes',0) & 0x400:
            raise OSError('Links/reparse points are unsupported.')
    info = path.lstat()
    if directory:
        if not stat.S_ISDIR(info.st_mode):
            raise OSError('Expected an ordinary directory.')
    elif not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise OSError('Expected an ordinary singly linked file.')
    return path


def check_file(path):
    """Return None for a file that contains NUL bytes (binary, or text such as UTF-16), else (crlf, lf, cr)."""
    path = safe_input(path)
    with open(path, "rb") as f:
        data = f.read()
    if b"\x00" in data:
        return None
    return count_endings(data)


def scan_folder(folder):
    folder = safe_input(folder, directory=True)
    rows = []
    skipped = 0
    total = 0
    stack = [folder]
    while stack:
        current = stack.pop()
        safe_input(current, directory=True)
        with os.scandir(current) as entries:
            ordered = sorted(entries, key=lambda entry: entry.name)
        for entry in ordered:
            total += 1
            if total > 10000:
                raise OSError('More than 10000 entries; refusing this tree.')
            info = entry.stat(follow_symlinks=False)
            directory = stat.S_ISDIR(info.st_mode)
            child = safe_input(entry.path, directory=directory)
            if directory:
                stack.append(child)
            elif not entry.name.lower().endswith(TEXT_TYPES):
                skipped += 1
            else:
                rel = str(child.relative_to(folder)).replace(os.sep, '/')
                rows.append((rel, check_file(child)))
    rows.sort(key=lambda row: row[0])
    return rows, skipped


def report(rows, skipped=0):
    mixed = 0
    shown = 0
    print("Files checked:", len(rows))
    for name, counts in rows:
        if counts is None:
            text = "contains NUL bytes (possibly binary or UTF-16), not counted"
        else:
            text = f"{label(*counts)} (CRLF {counts[0]}, LF {counts[1]}, CR {counts[2]})"
            if label(*counts) == "mixed":
                mixed += 1
        if shown < SHOW:
            print(f"  {ascii(name)}: {text}")
        shown += 1
    if shown > SHOW:
        print("  ... and", shown - SHOW, "more files. Showing the first", str(SHOW) + ".")
    if skipped:
        print("Files with other extensions, not checked:", skipped)
    print("Files that mix line endings:", mixed)
    print("Nothing was changed.")
    return 1 if mixed else 0


def main(argv):
    if len(argv) != 3 or argv[1] not in ("file", "folder"):
        print("Usage: python lineends.py file FILE")
        print("       python lineends.py folder FOLDER")
        return 2
    try:
        if argv[1] == "file":
            if not os.path.isfile(argv[2]):
                print("Not a file:", argv[2])
                return 2
            return report([(os.path.basename(argv[2]), check_file(argv[2]))])
        if not os.path.isdir(argv[2]):
            print("Not a folder:", argv[2])
            return 2
        rows, skipped = scan_folder(argv[2])
        return report(rows, skipped)
    except OSError as e:
        print("Could not read:", e)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
