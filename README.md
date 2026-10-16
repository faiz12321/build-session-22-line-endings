# Show which line endings text files use

A small read-only Python tool built step by step. Give it a file or a folder. It counts the line endings in each text file and says whether the file uses CRLF (Windows style), LF (Linux and Mac style), the old CR, no line endings, or a mix. It never changes, renames or creates any file.

Python's own documentation for `open` and `io` says text can end its lines with `\n`, `\r` or `\r\n`, and that Python can translate these when reading. This tool reads the raw bytes instead, so it counts what is really in the file.

## Run it

    python make_sample.py                          # creates NEW fictional sample/; existing paths refuse
    python lineends.py folder sample/tree          # check every text file in a folder
    python lineends.py file sample/tree/todo.txt   # check one file
    python -m unittest -v                          # 40 small fixture tests

On Windows, if `python` is not found, use `py`.

## Files

- `lineends.py` - the tool
- `make_sample.py` - makes eight tiny files with known line endings, written as bytes
- `test_lineends.py` - tests

## Notes

- Folder mode only looks at files ending in .txt .md .py .csv .json .html .css .js. Other files are counted as not checked.
- Files containing NUL bytes are skipped, including the UTF-16 fixture. This is a heuristic, not binary detection or encoding validation; it may miss NUL-free encodings/binary. Extension filtering is also only a heuristic.
- "Mixed" means a file has more than one kind of line ending. A file with a single line and no ending is reported as having none.
- Only the first 20 files are printed. The count covers all of them.
- Names are printed with special characters written as escapes, so they show on any console.
- The tool only reads files, opened in binary read mode. Tests check that nothing is changed or created.
- Tested only on tiny made-up files. Python 3.10 and 3.12 on Linux, and, by GitHub Actions, Python 3.12 on Windows and Ubuntu. Not tested on a Windows 10 or 11 desktop or on real folders.
- Educational example, no warranty. Use at your own risk.
- Code is MIT licensed (see LICENSE). Python belongs to its owners; this repository does not include it.

## Setup and traversal repairs

Use a NEW empty lesson folder. Setup exclusively creates sample/ and eight tiny fixture files. Existing folder/file paths, traversal and linked/reparse parents refuse; repeat setup does not reset. If interrupted, use another new lesson folder instead of deleting existing data.

Final checker refuses input/ancestor/tree links/reparse points, hardlinks, special entries and traversal, even when the entry has a skipped extension. The old os.walk traversal could suppress errors and report a partial tree clean; the new traversal propagates enumeration errors. Scan cap10000entries. Files and entry lists are still read into memory, so this is not a resource sandbox. Stop editors/sync; no hostile-race guarantee.

40 small tests: original23 byte-count/report/listing cases, four setup-preservation and13filesystem/error/traversal cases. NUL wording clarified, not a new encoding detector. Windows skips Unixpipe; symlink cases can skip when unavailable. No real migration or every-encoding proof. No upload/network code; other software/sync uncontrolled. Output exposes names/paths.

Two Windows and two Ubuntu full replays pass40small tests. Platform pairs differ only in unittest time. Windows skips Unixpipe; Ubuntu runs it. Both exercise symlinks. Code MIT licensed.
