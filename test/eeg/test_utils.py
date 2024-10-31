import pytest
import os
from typing import List
from shutil import copy2
import tempfile

from ege.utils import format_elapsed_time, recursive_copy, remove_extension, greek_letters, pp
def test_format_elapsed_time():
  assert format_elapsed_time(0) == "0s"
  assert format_elapsed_time(60) == "1m 0s"
  assert format_elapsed_time(3600) == "1h 0m 0s"
  assert format_elapsed_time(36000) == "10h 0m 0s"
  assert format_elapsed_time(3661) == "1h 1m 1s"
def test_pp():
  assert pp({"name": "John", "age": 30}, as_string=True) == "{'age': 30, 'name': 'John'}"
def test_recursive_copy():
  with tempfile.TemporaryDirectory() as src_dir:
    # Create files a, b, c in the source directory
    for file_name in ['a', 'b', 'c']:
      open(os.path.join(src_dir, file_name), 'a').close()

    # Create a temporary destination directory
    with tempfile.TemporaryDirectory() as dst_dir:
      # Call recursive_copy
      recursive_copy(src_dir, dst_dir, ['c'])

      # Check that files a and b got copied to the destination directory and file c was ignored
      assert 'a' in os.listdir(dst_dir)
      assert 'b' in os.listdir(dst_dir)
      assert 'c' not in os.listdir(dst_dir)
def test_remove_extension():
  assert remove_extension("image.png") == "image"
  assert remove_extension("this.that.those") == "this.that"
  assert remove_extension("path/image.png") == "path/image"
  assert remove_extension("path/this.that.those") == "path/this.that"
def test_greek_letters():
  assert greek_letters(0) == "alpha"
  assert greek_letters(1) == "beta"
  assert greek_letters(24) == "alpha1"
