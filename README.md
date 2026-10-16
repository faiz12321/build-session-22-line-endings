# Show which line endings text files use

A small read-only Python tool built step by step. Give it a file or a folder. It counts the line endings in each text file and says whether the file uses CRLF (Windows style), LF (Linux and Mac style), the old CR, no line endings, or a mix. It never changes, renames or creates any file.

Python's own documentation for `open` and `io` says text can end its lines with `\n`, `\r` or `\r\n`, and that Python can translate these when reading. This tool reads the raw bytes instead, so it counts what is really in the file.

## Run it

    python make_sample.py                          # makes a small folder of made-up files in sample/
    python lineends.py folder sample/tree          # check every text file in a folder
    python lineends.py file sample/tree/todo.txt   # check one file
    python -m unittest -v                          # twenty-three automated tests

On Windows, if `python` is not found, use `py`.

## Files

- `lineends.py` - the tool
- `make_sample.py` - makes eight tiny files with known line endings, written as bytes
- `test_lineends.py` - tests

## Notes

- Folder mode only looks at files ending in .txt .md .py .csv .json .html .css .js. Other files are counted as not checked.
- A file containing a zero byte is not counted. This includes text saved as UTF-16, which is not read by this tool.
- "Mixed" means a file has more than one kind of line ending. A file with a single line and no ending is reported as having none.
- Only the first 20 files are printed. The count covers all of them.
- Names are printed with special characters written as escapes, so they show on any console.
- The tool only reads files, opened in binary read mode. Tests check that nothing is changed or created.
- Tested only on tiny made-up files. Python 3.10 and 3.12 on Linux, and, by GitHub Actions, Python 3.12 on Windows and Ubuntu. Not tested on a Windows 10 or 11 desktop or on real folders.
- Educational example, no warranty. Use at your own risk.
- Code is MIT licensed (see LICENSE). Python belongs to its owners; this repository does not include it.
