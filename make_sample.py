"""Makes a small folder of made-up text files with different line endings.

Run: python make_sample.py
Files are written as bytes, so the line endings are exactly what is written here.
"""
from pathlib import Path


def make(folder):
    tree = Path(folder) / "tree"
    (tree / "docs").mkdir(parents=True, exist_ok=True)
    (tree / "notes.txt").write_bytes(b"one\ntwo\nthree\n")
    (tree / "todo.txt").write_bytes(b"buy milk\r\ncall Sam\r\n")
    (tree / "draft.md").write_bytes(b"# Title\r\nfirst line\nsecond line\r\nthird line\n")
    (tree / "docs" / "plan.txt").write_bytes(b"single line, no ending")
    (tree / "docs" / "data.csv").write_bytes(b"a,b\r\n1,2\r\n")
    (tree / "docs" / "photo.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00")
    (tree / "docs" / "utf16.txt").write_bytes("hi\r\nthere\r\n".encode("utf-16"))
    (tree / "docs" / "readme.rtf").write_bytes(b"{\\rtf1 hello}\n")
    return Path(folder)


if __name__ == "__main__":
    make("sample")
    print("Made sample/tree with eight small files")
