# Copyright (C) 2010-2013 Claudio Guarnieri.
# Copyright (C) 2014-2016 Cuckoo Foundation.
# This file is part of Cuckoo Sandbox - http://www.cuckoosandbox.org
# See the file 'docs/LICENSE' for copying permission.

import cStringIO
import io
import os
import pytest
import shutil
import tempfile

import cuckoo

from cuckoo.common.exceptions import CuckooOperationalError
from cuckoo.common.files import Folders, Files, Storage
from cuckoo.common import utils
from cuckoo.misc import set_cwd

class TestCreateFolders:
    def setup(self):
        self.tmp_dir = tempfile.gettempdir()

    def test_root_folder(self):
        """Tests a single folder creation based on the root parameter."""
        Folders.create(os.path.join(self.tmp_dir, "foo"))
        assert os.path.exists(os.path.join(self.tmp_dir, "foo"))
        os.rmdir(os.path.join(self.tmp_dir, "foo"))

    def test_single_folder(self):
        """Tests a single folder creation."""
        Folders.create(self.tmp_dir, "foo")
        assert os.path.exists(os.path.join(self.tmp_dir, "foo"))
        os.rmdir(os.path.join(self.tmp_dir, "foo"))

    def test_multiple_folders(self):
        """Tests multiple folders creation."""
        Folders.create(self.tmp_dir, ["foo", "bar"])
        assert os.path.exists(os.path.join(self.tmp_dir, "foo"))
        assert os.path.exists(os.path.join(self.tmp_dir, "bar"))
        os.rmdir(os.path.join(self.tmp_dir, "foo"))
        os.rmdir(os.path.join(self.tmp_dir, "bar"))

    def test_duplicate_folder(self):
        """Tests a duplicate folder creation."""
        Folders.create(self.tmp_dir, "foo")
        assert os.path.exists(os.path.join(self.tmp_dir, "foo"))
        Folders.create(self.tmp_dir, "foo")
        os.rmdir(os.path.join(self.tmp_dir, "foo"))

    def test_delete_folder(self):
        """Tests folder deletion #1."""
        Folders.create(self.tmp_dir, "foo")
        assert os.path.exists(os.path.join(self.tmp_dir, "foo"))
        Folders.delete(os.path.join(self.tmp_dir, "foo"))
        assert not os.path.exists(os.path.join(self.tmp_dir, "foo"))

    def test_delete_folder2(self):
        """Tests folder deletion #2."""
        Folders.create(self.tmp_dir, "foo")
        assert os.path.exists(os.path.join(self.tmp_dir, "foo"))
        Folders.delete(self.tmp_dir, "foo")
        assert not os.path.exists(os.path.join(self.tmp_dir, "foo"))

    def test_create_temp(self):
        """Test creation of temporary directory."""
        dirpath1 = Folders.create_temp("/tmp")
        dirpath2 = Folders.create_temp("/tmp")
        assert os.path.exists(dirpath1)
        assert os.path.exists(dirpath2)
        assert dirpath1 != dirpath2

    def test_create_temp_conf(self):
        """Test creation of temporary directory with configuration."""
        dirpath = tempfile.mkdtemp()
        set_cwd(dirpath)

        Folders.create(dirpath, "conf")
        with open(os.path.join(dirpath, "conf", "cuckoo.conf"), "wb") as f:
            f.write("[cuckoo]\ntmppath = %s" % dirpath)

        assert Folders.create_temp().startswith("%s/cuckoo-tmp/" % dirpath)

    def test_create_invld(self):
        """Test creation of a folder we can't access."""
        with pytest.raises(CuckooOperationalError):
            Folders.create("/invalid/directory/path")

    def test_delete_invld(self):
        """Test deletion of a folder we can't access."""
        dirpath = tempfile.mkdtemp()

        os.chmod(dirpath, 0)
        with pytest.raises(CuckooOperationalError):
            Folders.delete(dirpath)

        os.chmod(dirpath, 0775)
        Folders.delete(dirpath)

class TestCreateFile:
    def test_temp_file(self):
        filepath1 = Files.temp_put("hello", "/tmp")
        filepath2 = Files.temp_put("hello", "/tmp")
        assert open(filepath1, "rb").read() == "hello"
        assert open(filepath2, "rb").read() == "hello"
        assert filepath1 != filepath2
        os.unlink(filepath1)
        os.unlink(filepath2)

    def test_create(self):
        dirpath = tempfile.mkdtemp()
        Files.create(dirpath, "a.txt", "foo")
        assert open(os.path.join(dirpath, "a.txt"), "rb").read() == "foo"
        shutil.rmtree(dirpath)

    def test_named_temp(self):
        filepath = Files.temp_named_put("test", "hello.txt", "/tmp")
        assert open(filepath, "rb").read() == "test"
        assert os.path.basename(filepath) == "hello.txt"
        os.unlink(filepath)

    def test_temp_conf(self):
        dirpath = tempfile.mkdtemp()
        set_cwd(dirpath)

        Folders.create(dirpath, "conf")
        with open(os.path.join(dirpath, "conf", "cuckoo.conf"), "wb") as f:
            f.write("[cuckoo]\ntmppath = %s" % dirpath)

        assert Files.temp_put("foo").startswith("%s/cuckoo-tmp/" % dirpath)

    def test_stringio(self):
        filepath = Files.temp_put(cStringIO.StringIO("foo"), "/tmp")
        assert open(filepath, "rb").read() == "foo"

    def test_bytesio(self):
        filepath = Files.temp_put(io.BytesIO("foo"), "/tmp")
        assert open(filepath, "rb").read() == "foo"

    def test_create_bytesio(self):
        dirpath = tempfile.mkdtemp()
        filepath = Files.create(dirpath, "a.txt", io.BytesIO("A"*1024*1024))
        assert open(filepath, "rb").read() == "A"*1024*1024

    def test_hash_file(self):
        filepath = Files.temp_put("hehe", "/tmp")
        assert Files.md5_file(filepath) == "529ca8050a00180790cf88b63468826a"
        assert Files.sha1_file(filepath) == "42525bb6d3b0dc06bb78ae548733e8fbb55446b3"
        assert Files.sha256_file(filepath) == "0ebe2eca800cf7bd9d9d9f9f4aafbc0c77ae155f43bbbeca69cb256a24c7f9bb"

class TestStorage:
    def test_basename(self):
        assert Storage.get_filename_from_path("C:\\a.txt") == "a.txt"
        assert Storage.get_filename_from_path("C:/a.txt") == "a.txt"
        # ???
        assert Storage.get_filename_from_path("C:\\\x00a.txt") == "\x00a.txt"

class TestConvertChar:
    def test_utf(self):
        assert "\\xe9", utils.convert_char(u"\xe9")

    def test_digit(self):
        assert "9" == utils.convert_char(u"9")

    def test_literal(self):
        assert "e" == utils.convert_char("e")

    def test_punctation(self):
        assert "." == utils.convert_char(".")

    def test_whitespace(self):
        assert " " == utils.convert_char(" ")

class TestConvertToPrintable:
    def test_utf(self):
        assert "\\xe9" == utils.convert_to_printable(u"\xe9")

    def test_digit(self):
        assert "9" == utils.convert_to_printable(u"9")

    def test_literal(self):
        assert "e" == utils.convert_to_printable("e")

    def test_punctation(self):
        assert "." == utils.convert_to_printable(".")

    def test_whitespace(self):
        assert " " == utils.convert_to_printable(" ")

    def test_non_printable(self):
        assert r"\x0b" == utils.convert_to_printable(chr(11))

class TestIsPrintable:
    def test_utf(self):
        assert not utils.is_printable(u"\xe9")

    def test_digit(self):
        assert utils.is_printable(u"9")

    def test_literal(self):
        assert utils.is_printable("e")

    def test_punctation(self):
        assert utils.is_printable(".")

    def test_whitespace(self):
        assert utils.is_printable(" ")

    def test_non_printable(self):
        assert not utils.is_printable(chr(11))

class TestVersiontuple:
    def test_version_tuple(self):
        assert (1, 1, 1, 0) == utils.versiontuple("1.1.1.0")

def test_version():
    from cuckoo import __version__
    from cuckoo.misc import version
    assert __version__ == version

def test_exception():
    s = utils.exception_message()
    assert "Cuckoo version: %s" % cuckoo.__version__ in s
    assert "alembic:" in s
    assert "django-extensions:" in s
    assert "peepdf:" in s
    assert "sflock:" in s

def test_guid():
    assert utils.guid_name("{0002e005-0000-0000-c000-000000000046}") == "InprocServer32"
    assert utils.guid_name("{13709620-c279-11ce-a49e-444553540000}") == "Shell"

def test_jsbeautify():
    js = {
        "if(1){a(1,2,3);}": "if (1) {\n    a(1, 2, 3);\n}",
    }
    for k, v in js.items():
        assert utils.jsbeautify(k) == v

def test_htmlprettify():
    html = {
        "<a href=google.com>wow</a>": '<a href="google.com">\n wow\n</a>',
    }
    for k, v in html.items():
        assert utils.htmlprettify(k) == v