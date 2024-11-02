from transformers import AutoModel

from ege.logging import setup_logging
from ege.utils import format_elapsed_time, pp

from .paths import Paths


class Segments:
  def __init__(self, args: 'argparse.Namespace', path: str) -> None:
    self.args = args
    self.paths = Paths(args, path)
    self.logger = setup_logging()
    self.models = Models(self.args)
    self.segments = []

  @staticmethod
  def merge(diarization):
    """Collapse segments where the same speaker is two or more times in a row."""
    ret = {}
    current_speaker = current_start = current_end = None
    for turn, _, speaker in diarization.itertracks(yield_label=True):
      if speaker != current_speaker:
        if current_speaker is not None:
          ret.append({
            'segment': i,
            'start': current_start,
            'end': current_end,
            'speaker': current_speaker,
          })
        current_speaker = speaker
        current_start = turn.start
        current_end = turn.end
      else:
        current_end = turn.end
    # Append the last segment
    if current_speaker is not None:
      ret.append({
        'segment': i,
        'start': current_start,
        'end': current_end,
        'speaker': current_speaker,
      })
    return ret

  def detect(self) -> None:
    """Detect who is speaking when - these are defined as our segments of the audio"""
    # if we've already done the hard work of finding the segments,
    # just return the cache
    if os.path.exists(self.paths.path('json')) and not self.args.reset:
      with open(self.paths_json, 'r') as f: ret = json.load(f)
      self.logger.info("Loaded speakers")
      return ret

    # otherwise we have some computationally expensive tasks to do
    # Detect device (MPS for Apple Silicon or CPU)
    with self.logger.indent("Detecting Speakers"):
      # these libraries are slow to load (like 8 or 9 seconds!)
      # so I only load them as needed
      with self.logger.timer("Loaded libraries"):
        from pyannote.audio import Pipeline

      # use gpu acceleration if possible
      nm = "mps" if torch.backends.mps.is_available() else "cpu"
      self.logger.info(f"Using {nm}")
      device = torch.device(nm)

      # Load pre-trained Pyannote diarization model
      hf_token = os.getenv('HUGGINGFACE_TOKEN')
      pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        #cache_dir='models',
        cache_dir=self.models.path('detect'),
        use_auth_token=hf_token
      )
      with self.logger.timer("Initialized pipeline"):
        pipeline.to(device)

      # Apply diarization to the audio file to get speakers
      # I cannot set weights_only=True in torchaudio, so just supress this warning for now
      with self.logger.indent("Calling speakers", True):
        self.logger.info("NB: this may take a while for large files")
        warnings.filterwarnings(action='ignore', message='You are using `torch.load`')
        waveform, sample_rate = torchaudio.load(self.path_audio)  # , weights_only=True)
        diarization = pipeline({
          "waveform": waveform,
          "sample_rate": sample_rate
        })

      # Merge contiguous speaker segments
      self.segments = self.merge_segments(diarization)
      with self.logger.timer("Saved"):
        with open(self.path_json, 'w') as f:
          json.dump(self.segments, f)

  def abs_from_rel(self, rel):
    """
      Convenience function to get the real path to various
      segments files based on the path relative to the project
    """
    return os.path.join(self.paths.path('segments'), os.path.basename(rel))

  def extract(self):
    """Extract snippets of audio for each segment"""

    # add in the file name and figure which ones are outstanding
    fmt = '{:0' + str(len(str(len(self.segments)))) + 'd}.mp3'
    todo = []
    for i in range(len(self.segments)):
      # the project relative path
      relp = self.segments[i]['path_audio'] = os.path.join('segments', fmt.format(i))
      # the absolute path
      absp = self.abs_from_rel(relp)
      # do we need to run this one?
      if not os.path.exists(absp) or self.args.reset: todo.append(i)

    # nothing to do so skip the logging
    if len(todo) == 0: return

    # extract the segments
    with self.logger.indent("Getting Segments", True):
      # buffer all the IO up front for faster saves
      audio = AudioSegment.from_mp3(self.path_audio)
      segment_buffers = []

      # Just get a list of the coordinates in the audio
      with self.logger.timer("Buffering"):
        for i in todo:
          # Slice the segment and store it in a BytesIO buffer
          start_ms = int(self.segments[i]['start'] * 1000)
          end_ms = int(self.segments[i]['end'] * 1000)
          segment_audio = audio[start_ms:end_ms]

          # Use BytesIO to store audio in memory
          buffer = BytesIO()
          segment_audio.export(buffer, format='wav')
          relp = self.segments[i]['path_audio']
          absp = self.abs_from_rel(relp)
          segment_buffers.append((absp, buffer))

      with self.logger.progress("Writing", len(todo)) as prog:
        # Now, export each buffered segment to disk
        for path, buffer in segment_buffers:
          with open(path, 'wb') as f:
            f.write(buffer.getvalue())
          buffer.close()
          prog.next()

  def transcribe(self) -> None:
    """Transcribe the audio into text"""
    pass

  def emotions(self) -> None:
    """Annotate the emotional valences of each segment"""
    pass