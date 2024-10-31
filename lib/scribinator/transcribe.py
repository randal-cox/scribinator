#!env/bin/python3
import json, os, warnings, shutil, datetime, subprocess, platform
from io import BytesIO
from typing import Dict

from pydub import AudioSegment
import torch, torchaudio

from ege.logging_setup import setup_logging
from ege.utils import format_elapsed_time, recursive_copy, remove_extension, greek_letters

class Transcription:
  """
    Handle transcribing an audio file all the way to a web page with
    voices labeled with what they say and the emotions behind these utterances
  """

  def __init__(self, path: str, args: 'argparse.Namespace') -> None:
    """
      Set up the transcription process.

      Parameters:
      path (str): The path for the transcription audio file.
      args (argparse.Namespace): The command line arguments parsed by argparse.

      Instance Attributes:

      logger: logger object to log messages.
      args (argparse.Namespace): Arguments from the command line.

      info (dict): Dictionary to audio-specific data.
      paths (dict): Dictionary to paths in project.
      segments (list): List to store segment information.
    """

    self.logger = setup_logging()
    self.args = args
    if not os.path.exists(path): self.logger.critical(f'{path} does not exist')

    # set up the target directory
    self.setup_paths(path)

    # get any meta information
    self.setup_info()

  def setup_paths(self, path: str) -> None:
    """Set up standard paths"""

    # the target directory
    r = os.path.splitext(path)[0]
    self.paths: Dict[str, str] = {
      'source': path,
      'root': r,
      'segments': os.path.join(r, "segments"),
      'info': os.path.join(r, "info.json"),
      'audio': os.path.join(r, "segments", "all.mp3"),
      'json': os.path.join(r, "segments", "all.json"),
      'html': os.path.join(r, "index.html")
    }

  def setup_info(self) -> None:
    """Get default or supplied meta information"""

    dt = datetime.datetime.fromtimestamp(
      os.stat(self.paths['source']).st_birthtime
    ).strftime('%Y-%m-%d %H:%M:%S')
    self.info = {
      'title': os.path.basename(self.paths['root']),
      'description': f'transcription services by Scribinator 1000',
      'location': 'unknown',
      'date': dt,
    }
    if os.path.exists(self.paths['info']):
      with open(self.paths['info'], 'r') as f:
        self.info.update(json.load(f))

  def init_project(self) -> None:
    """Create the directory structure for the project and copy in our template"""
    r = self.paths['root']
    s = self.paths['segments']

    # delete if required, then make sure segments is present
    if self.args.reset and os.path.exists(r): shutil.rmtree(r)
    if not os.path.exists(s): os.makedirs(s)

    # then copy in our template
    recursive_copy(
      os.path.join(os.path.splitext(__file__)[0], 'http'),
      r,
      ['segments', 'segments.json', 'cache.js']
    )

    # then copy in the audio file
    if not os.path.exists(self.paths['audio']):
      with self.logger.timer("Copied audio file"):
        audio = AudioSegment.from_file(self.paths['source'])
        audio.export(self.paths['audio'], format="mp3")

  def detect_segments(self):
    # if we've already done the hard work of finding the segments,
    # just return the cache
    if os.path.exists(self.paths['json']) and not self.args.reset:
      with open(self.paths['json'], 'r') as f: self.segments = json.load(f)
      self.logger.info("Loaded speakers")
      return

    # otherwise we have some computationally expensive tasks to do
    # Detect device (MPS for Apple Silicon or CPU)
    with self.logger.indent("Detecting Speakers"):
      # these libraries are slow to load (like 8 or 9 seconds!)
      # so I only load them as needed
      with self.logger.timer("Loaded libraries"):
        from pyannote.audio import Pipeline

      # use graphics acceleration if possible
      nm = "mps" if torch.backends.mps.is_available() else "cpu"
      self.logger.info(f"Using {nm}")
      device = torch.device(nm)

      # Load pre-trained Pyannote diarization model
      hf_token = os.getenv('HUGGINGFACE_TOKEN')
      pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token
      )
      with self.logger.timer("Initialized pipeline"):
        pipeline.to(device)

      # Apply diarization to the audio file to get speakers
      # I cannot set weights_only=True in torchaudio, so just supress this warning for now
      with self.logger.indent("Calling speakers", True):
        self.logger.info("NB: this may take a while for large files")
        warnings.filterwarnings(action='ignore', message='You are using `torch.load`')
        waveform, sample_rate = torchaudio.load(self.paths['audio']) #, weights_only=True)
        diarization = pipeline({
          "waveform": waveform,
          "sample_rate": sample_rate
        })

      # Merge contiguous speaker segments
      segments = []
      current_speaker = current_start = current_end = None
      for turn, _, speaker in diarization.itertracks(yield_label=True):
        if speaker != current_speaker:
          if current_speaker is not None:
            segments.append((current_start, current_end, current_speaker))
          current_speaker = speaker
          current_start = turn.start
          current_end = turn.end
        else:
          current_end = turn.end
      # Append the last segment
      if current_speaker is not None:
        segments.append((current_start, current_end, current_speaker))

      # convert to a nice dict of all of this, and then save the json
      ret = []
      for i, (start, end, speaker) in enumerate(segments):
        speaker = int(speaker.split('_')[1])
        ret.append({
          'segment':      i,
          'start':        start,
          'end':          end,
          'speaker':      speaker,
        })
      with self.logger.timer("Saved"):
        with open(self.paths['json'], 'w') as f:
          json.dump(ret, f)
    self.segments = ret

  def extract_segments(self):
    # add in the file name and figure which ones are outstanding
    fmt = '{:0' + str(len(str(len(self.segments)))) + 'd}.mp3'
    todo = []
    for i in range(len(self.segments)):
      # the project relative path
      rel = self.segments[i]['path_audio'] = os.path.join('segments', fmt.format(i))
      # the absolute path
      abs = os.path.join(self.paths['root'], rel)
      # do we need to run this one?
      if not os.path.exists(abs) or self.args.reset: todo.append(i)

    # extract the segments
    if len(todo) == 0: return

    with self.logger.indent("Getting Segments", True):
      # buffer all the IO up front for faster saves
      audio = AudioSegment.from_mp3(self.paths['audio'])
      segment_buffers = []

      with self.logger.timer("Buffering"):
        for i in todo:
          # Slice the segment and store it in a BytesIO buffer
          start_ms = int(self.segments[i]['start'] * 1000)
          end_ms = int(self.segments[i]['end'] * 1000)
          segment_audio = audio[start_ms:end_ms]

          # Use BytesIO to store audio in memory
          buffer = BytesIO()
          segment_audio.export(buffer, format='wav')
          abs = os.path.join(
            self.paths['root'],
            self.segments[i]['path_audio']
          )
          segment_buffers.append((abs, buffer))


      with self.logger.progress("Writing", len(todo)) as prog:
        # Now, export each buffered segment to disk
        for path, buffer in segment_buffers:
          with open(path, 'wb') as f:
            f.write(buffer.getvalue())
          buffer.close()
          prog.next()

  def transcribe_segments(self):
    """Use whisper to transcribe the text of each segment file."""

    # add in the paths to the transcripts
    for i in range(len(self.segments)):
      self.segments[i]['path_transcript'] = remove_extension(self.segments[i]['path_audio']) + '_transcript.json'
    todo = [i for i in range(len(self.segments)) if not os.path.exists(self.segments[i]['path_transcript'])]

    if len(todo) > 0:
      # I can't seem to get around these warnings
      warnings.filterwarnings(
        "ignore",
        category=UserWarning,
        module='whisper.transcribe',
        message="FP16 is not supported on CPU; using FP32 instead"
      )

      with self.logger.indent("Transcription"):
        with self.logger.timer("Loaded libraries"):
          import whisper
        with self.logger.progress("Transcribing", len(todo)) as prog:
          model = whisper.load_model("base")  # Use "base", "small", "medium", or "large"
          r = self.paths['root']
          for i in todo:
            abs = os.path.join(self.paths['root'], self.segments[i]['path_audio'])
            transcription = model.transcribe(abs)
            # NB: transcription['segments'] has some info about confidence we might investigate later
            j = {
              'language': transcription['language'],
              'text': transcription['text'],
            }
            abs = os.path.join(r, self.segments[i]['path_transcript'])
            with open(abs, 'w') as f: json.dump(j, f)
            prog.next()

    # collect the results and put them into self.segments
    r = self.paths['root']
    for i in range(len(self.segments)):
      abs = os.path.join(r, self.segments[i]['path_transcript'])
      with open(abs) as f:
        j = json.load(f)
        self.segments[i]['transcript'] = j['text']
        self.segments[i]['language'] = j['language']

  def generate_annotated_transcript(self, transcript):
    ret = []
    for segment in transcript:
      start = segment['start']
      end = segment['end']
      speaker = segment['speaker']
      text = segment['transcript'].strip()  # Strip whitespace around the text

      if text:  # Only process non-empty text
        start_time = format_elapsed_time(start)
        elapsed_time = format_elapsed_time(end - start)
        speaker_str = f"Speaker {speaker:02}"  # Format speaker as two digits

        ret.append(f"{start_time} for {elapsed_time} [{speaker_str}]: {text}")
    return ret

  def _detect_emotions(self, wav_path: str, transcription: str, model, tokenizer, feature_extractor):
    # Load audio file
    waveform, sample_rate = torchaudio.load(wav_path)

    # Prepare audio input features
    audio_features = feature_extractor(waveform, sampling_rate=sample_rate, return_tensors="pt")

    # Tokenize transcription text
    text_features = tokenizer(transcription, return_tensors="pt")

    # Use MPS if available, otherwise fallback to CPU
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model.to(device)
    audio_features = {k: v.to(device) for k, v in audio_features.items()}
    text_features = {k: v.to(device) for k, v in text_features.items()}

    # Forward pass
    outputs = model(**audio_features, **text_features)

    # Extract emotion scores
    scores = outputs.logits.softmax(dim=1).squeeze().tolist()  # Convert logits to probabilities
    emotions = model.config.id2label  # Mapping of output ids to emotions

    # Display emotions with their scores
    emotion_scores = {emotions[i]: score * 100 for i, score in enumerate(scores)}
    sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)
    dominant_emotion = sorted_emotions[0][0]

    # Display dominant emotion followed by all emotion scores
    result = f"{dominant_emotion.upper()}: " + ", ".join([f"{e[:1]}{int(s)}" for e, s in sorted_emotions])

    return result, emotion_scores

  def detect_emotions(self):
    # dummy until I get in the emotion detection working
    import random
    for i in range(len(self.segments)):
      e = self.segments[i]['emotions'] = [int(100*random.random()) for _ in range(7)]
      self.segments[i]['emotion'] = e.index(max(e))
    return

    # get the paths for the emotions
    # todos = []
    # for i in range(len(self.segments)):
    #   p = self.segments[i]['path_emotions'] = self.segments[i]['path_audio'].replace('.wav', '_emotions.json')
    #   if not os.path.exists(p): todos.append(i)
    # if len(todos) > 0:
    #   with self.logger.progress("Detecting Emotions", len(todos)) as prog:
    #     with self.logger.timer("Loaded libraries"):
    #       from transformers import AutoModelForSequenceClassification, AutoTokenizer, AutoFeatureExtractor
    #       model = AutoModelForSequenceClassification.from_pretrained("m-a-p/MERT-v1-0")
    #       tokenizer = AutoTokenizer.from_pretrained("m-a-p/MERT-v1-0")
    #       feature_extractor = AutoFeatureExtractor.from_pretrained("m-a-p/MERT-v1-0")
    #
    #     for i in todos:
    #       result, emotion_scores = self.analyze_emotion(
    #         self.segments[i]['path_audio'],
    #         self.segments[i]['transcript'],
    #         model, tokenizer, feature_extractor
    #       )
    #       pp([
    #         self.segments[i]['transcript'],
    #         result,
    #         emotion_scores
    #       ])
    #       prog.next()
    #
    # print("Run emotions on these:", todos)
    # sys.exit()

  def simple_txt(self):
    ret = self.generate_annotated_transcript(self.segments)
    with open(os.path.join(self.paths['root'], "transcript.txt"), 'w') as f:
      f.write('\n'.join(ret))

  def cache_file(self):
    """
    Create the cache.js file in our output directory
    This file has a dictionary of the results of all analysis we have done
    """
    s = self.info['speakers_segments'] = [s['speaker'] for s in self.segments]
    s = sorted(list(set(s)))
    s = [greek_letters(v) for v in s]
    self.info['speakers_all'] = s
    self.info['segments'] = self.segments
    js = 'document.transcriptionator = {};\n'
    js += 'document.transcriptionator.results = '
    js += json.dumps(self.info, indent=2)
    path = os.path.join(self.paths['root'], 'cache.js')
    with open(path, 'w') as f: f.write(js)
    os.chmod(path, 0o644)

  def open_result(self):
    """Open the results in a web browser"""
    path = self.paths['html']
    if platform.system() == "Darwin":
      subprocess.run(['open', path])
    elif platform.system() == "Windows":
      subprocess.run(['start', path], shell=True)
    elif platform.system() == "Linux":
      subprocess.run(['xdg-open', path])
    else:
      self.logger.warning(f"Results are in {self.paths['root']}")

  def run(self):
    with (self.logger.indent(f"Processing {self.paths['source']}")):
      self.init_project()

      # process everything
      self.detect_segments()
      self.extract_segments()
      self.transcribe_segments()
      self.detect_emotions()

      # output
      self.simple_txt()
      self.cache_file()
      self.open_result()
