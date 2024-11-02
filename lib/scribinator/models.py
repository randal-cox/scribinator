import os, os.path

from ege.utils import pp
from ege.logging import setup_logging

class Models:
  """Class to handle the various ML models we use for this project"""
  def __init__(self, args: 'argparse.Namespace') -> None:
    """Set up the models - dir is where to store the models, defaulting to the current working directory"""
    self.args = args
    setattr(self.args, 'reset', getattr(self.args, 'reset', False))
    setattr(self.args, 'verbose', getattr(self.args, 'reset', 2))

    self.dir = self.args.models or os.path.join(os.getcwd(), 'models')
    self.dir = self.dir.rstrip('/')
    self.logger = setup_logging()

  @staticmethod
  def names() -> list[str]:
    """Get a list of the model names we support"""
    return 'detect,transcribe,emotions'.split(',')

  def path(self, name: str) -> str:
    """Get the path to a given model"""
    if name in self.names(): return os.path.join(self.dir, name)
    raise ValueError(f"Illegal model name for model_path: '{name}'")

  def fetch_one(self, name:str):
    """Fetch a single model"""
    with self.logger.indent(f"Getting model for {name}", True):
      # make sure there is a directory for it
      for path in [self.dir, self.path(name)]:
        if os.path.exists(path): continue
        os.makedirs(path, exist_ok=True)
      # make sure the signal file is not there
      if os.path.exists(self.path(name) + '.done'):
        os.unlink(self.path(name) + '.done')
      # then execute the fetch
      getattr(self, 'fetch_' + name)()
      # mark it as done
      with open(self.path(name) + '.done', 'w') as f:
        f.write("")

  def fetch(self, verbose: bool = False, force: bool = False) -> None:
    """Get local copies of all the AI models needed to run this"""
    todo: list = [
      name for name in self.names() if not self.done(name) or force
    ]
    if len(todo) == 0:
      if verbose: self.logger.info("Models already downloaded")
      return

    # We have some to do, so go fetch those models
    with self.logger.indent("Saving local copies of all models", True):
      self.logger.info("# This will access various servers to download model parameters")
      self.logger.info("# All subsequent transcriptions and annotations will use these local copies")
      for name in todo:
        self.fetch_one(name)

  def todo(self):
    """Get a list of models that need to be fetched"""
    return [ name for name in self.names() if not self.done(name) ]

  def done(self, name: str = None) -> bool:
    """Detect if a model is fetched. If no model name is specified, check if ALL models are done"""
    if self.args.reset: return False
    if name is None:    return len(self.todo()) == 0
    path: str = self.path(name) + ".done"
    return os.path.exists(path)

  def fetch_detect(self):
    """Fetch the pyannotate diarization model used for detecting speakers"""
    with self.logger.timer("Loaded libraries"):
      from pyannote.audio import Pipeline

    hf_token = os.getenv('HUGGINGFACE_TOKEN')
    Pipeline.from_pretrained(
      "pyannote/speaker-diarization-3.1",
      cache_dir=self.path('detect'),
      use_auth_token=hf_token
    )
  def fetch_transcribe(self):
    """Fetch the whisper model for voice transcription"""
    self.logger.info("No saving implemented")

  def fetch_emotions(self):
    """Fetch the emotion-detection module for Ekman emotions"""
    self.logger.info("No saving implemented")

