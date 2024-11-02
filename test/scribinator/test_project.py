import os, os.path, shutil, tempfile, unittest, argparse, datetime
from contextlib import contextmanager

from scribinator.project import Project

class TestProject(unittest.TestCase):
  @staticmethod
  def path_src():
    return os.path.join(os.path.dirname(__file__), 'demo_audio.m4a')
  @contextmanager
  def create_project(self):
    # Create a temporary directory with our audio file in place
    self.tmp_dir = tempfile.TemporaryDirectory()
    src = self.path_src()

    # Create Project based on the path of the copied audio file
    args = argparse.Namespace(**{
      "reset": False,
      "title": "a title",
      "description": "a description",
      "location": "a location",
      'when': "a time",
      'author': 'an author'
    })
    project = Project(args, src)

    yield project

    self.tmp_dir.cleanup()


  def create(self):
    # Create a temporary directory with our audio file in place
    self.tmp_dir = tempfile.TemporaryDirectory()
    src = os.path.join(os.path.dirname(__file__), 'demo_audio.m4a')
    # dst = os.path.join(self.tmp_dir.name, 'demo_audio.m4a')
    # shutil.copy(src, dst)

    # Create Project based on the path of the copied audio file
    args = argparse.Namespace(**{
      "reset": False,
      "title": "a title",
      "description": "a description",
      "location": "a location",
      'when': "a time",
      'author': 'an author'
    })
    return Project(args, src)

  def test_meta(self):
    with self.create_project() as project:
      dt = datetime.datetime.fromtimestamp(
        os.stat(self.path_src()).st_birthtime
      ).strftime('%Y-%m-%d %H:%M:%S')
      meta = project.meta()
      exp = {
        'author': 'unknown',
        'description': 'transcription services by Scribinator 1000',
        'location': 'unknown',
        'title': 'an author',
        'when': dt,
      }
      unittest.TestCase().assertDictEqual(exp, meta)

if __name__ == "__main__":
  unittest.main()
