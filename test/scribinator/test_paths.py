import pytest, os, argparse

from scribinator.paths import Paths


def test_init():
  args = argparse.Namespace(**{})
  r = 'some/path/to/audiofile'
  p = Paths(args, r + '.mp3')
  assert p.path('source') == r + '.mp3'
  assert p.path('root') == r
  assert p.path('segments') == os.path.join(r, 'segments')
  assert p.path('meta') == os.path.join(r, 'meta.json')
  assert p.path('audio') == os.path.join(r, 'all.mp3')
  assert p.path('json') == os.path.join(r, 'all.json')
  assert p.path('html') == os.path.join(r, 'index.html')

def test_segment_audio_info_path():
  args = argparse.Namespace(**{})
  r = 'some/path/to/audiofile'
  p = Paths(args, r + '.mp3')

  assert p.path('segment_audio', 10) == os.path.join(r, 'segments', '10.mp3')
  assert p.path('segment_info', 20) == os.path.join(r, 'segments', '20.json')

def test_exceptions():
  args = argparse.Namespace(**{})
  r = 'some/path/to/audiofile'
  p = Paths(args, r + '.mp3')

  with pytest.raises(ValueError):
    p.path('segment_audio')

  with pytest.raises(ValueError):
    p.path('segment_info')

  with pytest.raises(ValueError):
    p.path('segment_info', -1)

  with pytest.raises(ValueError):
    p.path('segment_info', 1.3)

  with pytest.raises(ValueError):
    p.path('source', 10)

  with pytest.raises(KeyError):
    p.path('non_existent_path_key')

