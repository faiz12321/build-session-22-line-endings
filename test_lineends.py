import io
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import lineends
import make_sample


def run(*args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = lineends.main(["lineends.py", *map(str, args)])
    return code, buf.getvalue()


class Counting(unittest.TestCase):
    def test_lf_only(self):
        self.assertEqual(lineends.count_endings(b"a\nb\n"), (0, 2, 0))

    def test_crlf_only(self):
        self.assertEqual(lineends.count_endings(b"a\r\nb\r\n"), (2, 0, 0))

    def test_cr_only(self):
        self.assertEqual(lineends.count_endings(b"a\rb\r"), (0, 0, 2))

    def test_mixed(self):
        self.assertEqual(lineends.count_endings(b"a\r\nb\nc\rd"), (1, 1, 1))

    def test_crlf_not_counted_twice(self):
        self.assertEqual(lineends.count_endings(b"\r\n"), (1, 0, 0))

    def test_empty(self):
        self.assertEqual(lineends.count_endings(b""), (0, 0, 0))

    def test_two_returns_then_newline(self):
        self.assertEqual(lineends.count_endings(b"\r\r\n"), (1, 0, 1))

    def test_labels(self):
        self.assertEqual(lineends.label(0, 0, 0), "no line endings")
        self.assertEqual(lineends.label(3, 0, 0), "CRLF")
        self.assertEqual(lineends.label(0, 3, 0), "LF")
        self.assertEqual(lineends.label(0, 0, 3), "CR")
        self.assertEqual(lineends.label(1, 1, 0), "mixed")


class Files(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def write(self, name, data):
        p = Path(self.tmp) / name
        p.write_bytes(data)
        return p

    def test_file_mode_lf(self):
        code, out = run("file", self.write("a.txt", b"x\ny\n"))
        self.assertEqual(code, 0)
        self.assertIn("'a.txt': LF (CRLF 0, LF 2, CR 0)", out)

    def test_file_mode_mixed_returns_1(self):
        code, out = run("file", self.write("a.txt", b"x\r\ny\n"))
        self.assertEqual(code, 1)
        self.assertIn("mixed", out)

    def test_zero_bytes_not_counted(self):
        code, out = run("file", self.write("a.txt", "hi\r\n".encode("utf-16")))
        self.assertEqual(code, 0)
        self.assertIn("contains NUL bytes", out)

    def test_file_mode_any_extension(self):
        code, out = run("file", self.write("a.data", b"x\n"))
        self.assertIn("LF", out)

    def test_missing_file(self):
        code, out = run("file", Path(self.tmp) / "nope.txt")
        self.assertEqual(code, 2)
        self.assertIn("Not a file", out)

    def test_usage(self):
        self.assertEqual(run()[0], 2)
        self.assertEqual(run("oops", "x")[0], 2)

    def test_unreadable_file(self):
        p = self.write("a.txt", b"x\n")
        with mock.patch("builtins.open", side_effect=PermissionError("denied")):
            code, out = run("file", p)
        self.assertEqual(code, 2)
        self.assertIn("Could not read", out)


class Folder(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def test_sample_folder(self):
        folder = make_sample.make(Path(self.tmp) / "s")
        code, out = run("folder", folder / "tree")
        self.assertEqual(code, 1)
        self.assertIn("Files checked: 6", out)
        self.assertIn("'draft.md': mixed (CRLF 2, LF 2, CR 0)", out)
        self.assertIn("'notes.txt': LF", out)
        self.assertIn("'todo.txt': CRLF", out)
        self.assertIn("'docs/data.csv': CRLF", out)
        self.assertIn("'docs/plan.txt': no line endings", out)
        self.assertIn("other extensions, not checked: 2", out)
        self.assertIn("mix line endings: 1", out)

    def test_clean_folder(self):
        (Path(self.tmp) / "a.txt").write_bytes(b"x\n")
        code, out = run("folder", self.tmp)
        self.assertEqual(code, 0)
        self.assertIn("mix line endings: 0", out)

    def test_extension_in_capitals(self):
        (Path(self.tmp) / "A.TXT").write_bytes(b"x\r\n")
        code, out = run("folder", self.tmp)
        self.assertIn("Files checked: 1", out)

    def test_only_first_20_shown(self):
        for i in range(25):
            (Path(self.tmp) / f"f{i:02d}.txt").write_bytes(b"x\n")
        code, out = run("folder", self.tmp)
        self.assertIn("Files checked: 25", out)
        self.assertIn("and 5 more files. Showing the first 20.", out)
        self.assertNotIn("f24.txt", out)

    def test_not_a_folder(self):
        code, out = run("folder", Path(self.tmp) / "nope")
        self.assertEqual(code, 2)
        self.assertIn("Not a folder", out)

    def test_forward_slashes_in_names(self):
        (Path(self.tmp) / "d").mkdir()
        (Path(self.tmp) / "d" / "a.txt").write_bytes(b"x\n")
        code, out = run("folder", self.tmp)
        self.assertIn("'d/a.txt'", out)


class ReadOnly(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def snapshot(self, folder):
        out = {}
        for dirpath, dirs, files in os.walk(folder):
            for n in dirs + files:
                p = os.path.join(dirpath, n)
                out[p] = Path(p).read_bytes() if os.path.isfile(p) else None
        return out

    def test_nothing_changed_or_created(self):
        folder = make_sample.make(Path(self.tmp) / "s")
        before = self.snapshot(folder)
        run("folder", folder / "tree")
        run("file", folder / "tree" / "draft.md")
        self.assertEqual(before, self.snapshot(folder))

    def test_file_is_opened_for_reading_only(self):
        folder = make_sample.make(Path(self.tmp) / "s")
        modes = []
        real_open = open

        def spy(file, mode="r", *a, **k):
            modes.append(mode)
            return real_open(file, mode, *a, **k)

        with mock.patch("builtins.open", spy):
            run("folder", folder / "tree")
        self.assertTrue(modes)
        self.assertEqual(set(modes), {"rb"})



class SafetyBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.sample = make_sample.make(self.dir/'sample')

class SafeSetup(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.sample = self.root / 'sample'

    def test_existing_folder_preserves_nested_bytes_and_mtime(self):
        (self.sample / 'nested').mkdir(parents=True)
        keep = self.sample / 'nested' / 'keep'
        keep.write_bytes(b'KEEP')
        before = keep.read_bytes(), keep.stat().st_mtime_ns
        with self.assertRaises(FileExistsError):
            make_sample.make(self.sample)
        self.assertEqual(before, (keep.read_bytes(), keep.stat().st_mtime_ns))

    def test_existing_file_preserved(self):
        self.sample.write_bytes(b'KEEP')
        before = self.sample.read_bytes(), self.sample.stat().st_mtime_ns
        with self.assertRaises(FileExistsError):
            make_sample.make(self.sample)
        self.assertEqual(before, (self.sample.read_bytes(), self.sample.stat().st_mtime_ns))

    def test_repeat_preserves_every_output(self):
        make_sample.make(self.sample)
        before = {str(p.relative_to(self.sample)):(p.read_bytes(),p.stat().st_mtime_ns) for p in self.sample.rglob('*') if p.is_file()}
        with self.assertRaises(FileExistsError):
            make_sample.make(self.sample)
        self.assertEqual(before, {str(p.relative_to(self.sample)):(p.read_bytes(),p.stat().st_mtime_ns) for p in self.sample.rglob('*') if p.is_file()})

    def test_cli_repeat_preserves_every_output(self):
        import subprocess, sys
        script = self.root / 'make_sample.py'
        shutil.copyfile(Path(make_sample.__file__).resolve(), script)
        make_sample.make(self.sample)
        before = {str(p.relative_to(self.sample)):(p.read_bytes(),p.stat().st_mtime_ns) for p in self.sample.rglob('*') if p.is_file()}
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('sample already exists', result.stderr)
        self.assertEqual(before, {str(p.relative_to(self.sample)):(p.read_bytes(),p.stat().st_mtime_ns) for p in self.sample.rglob('*') if p.is_file()})




class FilesystemSafety(SafetyBase):
    def link(self,path,target,directory=False):
        try:path.symlink_to(target,target_is_directory=directory)
        except OSError:self.skipTest('Symlink creation unavailable')

    def test_list_hardlink_refused(self):
        target=self.sample/'tree'/'notes.txt';before=target.read_bytes(),target.stat().st_mtime_ns
        link=self.dir/'hard.txt';os.link(target,link)
        self.assertEqual(run('file',link)[0],2)
        self.assertEqual(before,(target.read_bytes(),target.stat().st_mtime_ns))

    def test_list_symlink_existing_dangling_and_selfloop_refused(self):
        link=self.dir/'link';self.link(link,self.sample/'tree'/'notes.txt')
        self.assertEqual(run('file',link)[0],2);link.unlink()
        self.link(link,self.dir/'absent');self.assertEqual(run('file',link)[0],2);link.unlink()
        self.link(link,link);self.assertEqual(run('file',link)[0],2)

    def test_list_linked_parent_refused(self):
        link=self.dir/'linked';self.link(link,self.sample,True)
        self.assertEqual(run('file',link/'tree'/'notes.txt')[0],2)

    def test_folder_root_link_refused(self):
        link=self.dir/'linked';self.link(link,self.sample/'tree',True)
        self.assertEqual(run('folder',link)[0],2)

    def test_tree_file_link_refused(self):
        link=self.sample/'tree'/'link';self.link(link,self.sample/'tree'/'notes.txt')
        self.assertEqual(run('folder',self.sample/'tree')[0],2)

    def test_skipped_extension_link_still_refused(self):
        link=self.sample/'tree'/'skip.bin';self.link(link,self.sample/'tree'/'notes.txt')
        self.assertEqual(run('folder',self.sample/'tree')[0],2)

    def test_tree_recursive_loop_refused(self):
        tree=self.sample/'tree';self.link(tree/'loop',tree,True)
        self.assertEqual(run('folder',tree)[0],2)

    def test_tree_hardlink_refused(self):
        target=self.sample/'tree'/'notes.txt';os.link(target,self.sample/'tree'/'hard')
        self.assertEqual(run('folder',self.sample/'tree')[0],2)

    def test_tree_special_pipe_refused(self):
        if not hasattr(os,'mkfifo'):self.skipTest('Unix pipe unavailable')
        tree=self.sample/'tree';os.mkfifo(tree/'pipe')
        self.assertEqual(run('folder',tree)[0],2)
        self.assertEqual(run('file',tree/'pipe')[0],2)

    def test_traversal_refused(self):
        self.assertEqual(run('file',self.sample/'..'/'sample'/'tree'/'notes.txt')[0],2)
        self.assertEqual(run('folder',self.sample/'..'/'sample'/'tree')[0],2)

    def test_scandir_permission_error_is_not_a_clean_report(self):
        with mock.patch('os.scandir',side_effect=PermissionError('simulated denial')):
            code,out=run('folder',self.sample/'tree')
        self.assertEqual(code,2);self.assertIn('simulated denial',out)

    def test_setup_linked_parent_refused(self):
        link=self.dir/'linked';self.link(link,self.dir,True)
        with self.assertRaises(OSError):make_sample.make(link/'new')
        self.assertFalse((self.dir/'new').exists())

    def test_setup_traversal_refused(self):
        with self.assertRaises(OSError):make_sample.make(self.dir/'..'/self.dir.name/'new')
        self.assertFalse((self.dir/'new').exists())



if __name__ == "__main__":
    unittest.main()
