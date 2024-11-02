import json, os, shutil, datetime, functools, subprocess
import sys
from typing import Dict, Any

from ege.logging import setup_logging
from ege.utils import recursive_copy, remove_extension, pp
from .paths import Paths

class Project:
  """
  Describes an audio transcription project for scribinator
  """

  def __init__(self, args: 'argparse.Namespace', path: str) -> None:
    """
      Set up the transcription process.

      Parameters:
      path (str): The path for the transcription audio file.
      args (argparse.Namespace): The command line arguments parsed by argparse.

      Instance Attributes:
      logger: logger object to log messages.
      args (argparse.Namespace): Arguments from the command line.
      paths (Paths): a class that knows about the structure of the project
    """

    self.logger = setup_logging()
    self.args = args
    if not os.path.exists(path): self.logger.critical(f'{path} does not exist')
    self.paths = Paths(args, path)

    # set up the target directory
    self._meta = None
    self.create()

  @functools.lru_cache(maxsize=None)
  def meta(self) -> dict[str, str | Any]:
    """
      Get meta information

      this will cascade from various sources
      - some sensible defaults from the source file
      - any json file of the same name as the source file
      - any existing project info.json file
      - any command-line switches
    """

    # first set up default values based on knowing nothing
    self.logger.info(self.paths.path('source'))
    dt = datetime.datetime.fromtimestamp(
      os.stat(self.paths.path('source')).st_birthtime
    ).strftime('%Y-%m-%d %H:%M:%S')
    self._meta = {
      'title': os.path.basename(self.paths.path('root')),
      'description': f'transcription services by Scribinator 1000',
      'location': 'unknown',
      'author': 'unknown',
      'when': dt,
    }

    # if there is a json file with the same name as the source file, use that
    path = remove_extension(self.paths.path('source')) + '.json'
    if os.path.exists(path):
      with open(self.paths['_meta'], 'r') as f:
        self._meta.update(json.load(f))

    # if a json file already exists in the project, use what is there
    if os.path.exists(self.paths.path('meta')):
      with open(self.paths.path('meta'), 'r') as f:
        self._meta.update(json.load(f))

    # Finally, if there are command line switch values, use those, overriding whatever is present
    for k in 'title,description,location,when,author'.split(','):
      self._meta['title'] = getattr(self.args, k) or self._meta[k]

    with open(self.paths.path('meta'), 'w') as f:
      json.dump(self._meta, f)

    self.logger.info(pp(self._meta, True))

    return self._meta

  def create(self) -> None:
    """Create the directory structure for the project and copy in our template"""
    r = self.paths.path('root')
    s = self.paths.path('segments')

    # delete if required, then make sure segments is present
    if self.args.reset and os.path.exists(r): shutil.rmtree(r)
    if not os.path.exists(s): os.makedirs(s)

    # then copy in our template, omitting a few things we keep for development
    h = os.path.join(os.path.dirname(__file__), 'sources', 'http')
    recursive_copy(
      h,
      r,
      ['segments', 'segments.json', 'cache.js']
    )

    # then copy in the audio file
    if not os.path.exists(self.paths.path('audio')):
      with self.logger.timer("Copied audio file"):
        subprocess.run(
          [
            "ffmpeg",
            "-i", self.paths.path('source'),
            "-vn", "-ac", "2",
            self.paths.path('audio')
          ],
          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        creation_time = os.path.getctime(self.paths.path('source'))
        modification_time = os.path.getmtime(self.paths.path('source'))
        os.utime(self.paths.path('audio'), (creation_time, modification_time))

    # save the meta file
    self.meta()