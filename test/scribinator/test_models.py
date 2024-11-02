import os, unittest, pytest, argparse

from unittest.mock import patch, MagicMock
from contextlib import contextmanager
from tempfile import TemporaryDirectory

from scribinator.models import Models

@contextmanager
def slow(args):
  """Slow context manager"""
  args = argparse.Namespace(**args)
  with TemporaryDirectory() as temp_dir:
    args.models = temp_dir
    yield Models(args)


# noinspection DuplicatedCode
@contextmanager
def fast(args):
  """Fast context manager"""
  def dummy_func(): pass

  args = argparse.Namespace(**args)
  with TemporaryDirectory() as temp_dir:
    args.models = temp_dir
    with patch('scribinator.models.Models.fetch_detect', new_callable=MagicMock()) as detect, \
        patch('scribinator.models.Models.fetch_transcribe', new_callable=MagicMock()) as transcribe, \
        patch('scribinator.models.Models.fetch_emotions', new_callable=MagicMock()) as emotions:
      detect.side_effect = dummy_func
      transcribe.side_effect = dummy_func
      emotions.side_effect = dummy_func
      yield Models(args)

# noinspection DuplicatedCode
@contextmanager
def error(args):
  """Error context manager"""

  def error_func(): raise Exception("Mocked error")

  args = argparse.Namespace(**args)
  with TemporaryDirectory() as temp_dir:
    args.models = temp_dir
    with patch('scribinator.models.Models.fetch_detect', new_callable=MagicMock()) as detect, \
        patch('scribinator.models.Models.fetch_transcribe', new_callable=MagicMock()) as transcribe, \
        patch('scribinator.models.Models.fetch_emotions', new_callable=MagicMock()) as emotions:
      detect.side_effect = error_func
      transcribe.side_effect = error_func
      emotions.side_effect = error_func
      yield Models(args)

def verify_models_behavior(models):
  """Helper function to verify models behavior"""
  assert models.names() == ['detect', 'transcribe', 'emotions']

  for model_name in models.names():
    # Verify current todo state
    initial_todo_size = len(models.todo())

    models.fetch_one(model_name)

    # Verify todo state after fetch
    final_todo_size = len(models.todo())
    assert final_todo_size == initial_todo_size - 1

    model_path = models.path(model_name)
    # Assert the path of the model is indeed a directory
    assert os.path.isdir(model_path)
  # Assert that all models are done
  assert len(models.todo()) == 0

def verify_models_behavior_with_errors(models):
  """Helper function to verify models behavior with errors"""
  assert models.names() == ['detect', 'transcribe', 'emotions']

  model_names = models.names()
  for model_name in model_names:
    # Verify current todo state
    initial_todo_size = len(models.todo())

    try:
      models.fetch_one(model_name)
    except Exception as e:
      # Verify that exception is thrown
      assert str(e) == "Mocked error"

    # Verify todo state after fetch
    final_todo_size = len(models.todo())
    # Assert that the size remains same after error
    assert final_todo_size == initial_todo_size

  # Models should all be in 'todo' state after errors occurred.
  assert models.todo() == models.names()

class TestModels(unittest.TestCase):
  @pytest.mark.slow
  def test_slow(self):
    with slow({}) as m:
      verify_models_behavior(m)
      assert len(m.todo()) == 0

  def test_fast(self):
    with fast({}) as m:
      verify_models_behavior(m)
      assert len(m.todo()) == 0

  def test_error(self):
    with error({}) as m:
      verify_models_behavior_with_errors(m)
      assert len(m.todo()) == len(m.names())

if __name__ == "__main__":
  unittest.main()

