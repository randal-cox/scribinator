import os.path
from _ctypes import ArgumentError

from ege.utils import remove_extension
class Paths:
  def __init__(self, args: 'argparse.Namespace', path: str) -> None:
    """Create a class handling where everything is supposed to go"""
    self.args = args

    r = remove_extension(path)
    self.paths: Dict[str, str] = {
      'source':     path,
      'root':       r,
      'segments':   os.path.join(r, "segments"),
      'meta':       os.path.join(r, "meta.json"),
      'audio':      os.path.join(r, "all.mp3"),
      'json':       os.path.join(r, "all.json"),
      'html':       os.path.join(r, "index.html")
    }

  @staticmethod
  def test_number(name: str, number: int) -> None:
    if number is None: raise ValueError(f'{name} requires a number')
    if number < 0 : raise ValueError(f'{name} requires a number 0 and above')
    if not isinstance(number, int): raise ValueError(f'{name} requires an integer for number')

  def path(self, name: str, number=None) -> str:
    if name == 'segment_audio':
      self.test_number(name, number)
      return os.path.join(self.path('segments'), f'{number}.mp3')

    if name == 'segment_info':
      self.test_number(name, number)
      return os.path.join(self.path('segments'), f'{number}.json')

    if number is not None: raise ValueError(f'no number allowed for {name}')

    return self.paths[name]
