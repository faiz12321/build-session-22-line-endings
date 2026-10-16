"""Makes a small folder of made-up text files with different line endings.

Run: python make_sample.py
Files are written as bytes, so the line endings are exactly what is written here.
"""
from pathlib import Path
import stat


def make(folder):
    folder = Path(folder).absolute()
    if '..' in folder.parts:
        raise OSError('Parent-traversal setup paths are unsupported.')
    for parent in reversed(folder.parents):
        info = parent.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise OSError('Linked/reparse parents are unsupported.')
    folder.mkdir()
    tree = folder / "tree"
    (tree / "docs").mkdir(parents=True)
    with (tree / "notes.txt").open("xb") as handle: handle.write(b"one\ntwo\nthree\n")
    with (tree / "todo.txt").open("xb") as handle: handle.write(b"buy milk\r\ncall Sam\r\n")
    with (tree / "draft.md").open("xb") as handle: handle.write(b"# Title\r\nfirst line\nsecond line\r\nthird line\n")
    with (tree / "docs" / "plan.txt").open("xb") as handle: handle.write(b"single line, no ending")
    with (tree / "docs" / "data.csv").open("xb") as handle: handle.write(b"a,b\r\n1,2\r\n")
    with (tree / "docs" / "photo.png").open("xb") as handle: handle.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00")
    with (tree / "docs" / "utf16.txt").open("xb") as handle: handle.write("hi\r\nthere\r\n".encode("utf-16"))
    with (tree / "docs" / "readme.rtf").open("xb") as handle: handle.write(b"{\\rtf1 hello}\n")
    return Path(folder)


if __name__ == "__main__":
    try:
        make(Path(__file__).absolute().parent / "sample")
    except FileExistsError:
        raise SystemExit("Stopped: sample already exists. Nothing was replaced or deleted.")
    print("Made sample/tree with eight small files")
