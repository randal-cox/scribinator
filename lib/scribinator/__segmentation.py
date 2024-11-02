# import json, os, warnings, shutil, datetime, subprocess, platform
# from io import BytesIO
# from typing import Dict
#
# from pydub import AudioSegment
# import torch, torchaudio
#
# from ege.logging import setup_logging
# from ege.utils import format_elapsed_time, recursive_copy, remove_extension, greek_letters
# from .paths import Paths
# class Segmentation:
#   def __init__(args: 'argparse.Namespace', path: str) -> None:
#     """
#         Initialize the AudioSegmentation process.
#
#         Parameters:
#         args (argparse.Namespace): The command line arguments parsed by argparse.
#         paths (Paths): The paths object that lets us figure out where to put everything
#
#         Instance Attributes:
#         logger: logger object to log messages.
#         paths: The paths object that lets us figure out where to put everything
#         args (argparse.Namespace): Arguments from the command line.
#         """
#
#     self.logger = setup_logging()
#     self.args = args
#     self.paths = Paths(path)
#
#   def merge_segments(self, diarization):
#     """Collapse segments where the same speaker is two or more times in a row."""
#     ret = {}
#     current_speaker = current_start = current_end = None
#     for turn, _, speaker in diarization.itertracks(yield_label=True):
#       if speaker != current_speaker:
#         if current_speaker is not None:
#           ret.append({
#             'segment': i,
#             'start': current_start,
#             'end': current_end,
#             'speaker': current_speaker,
#           })
#         current_speaker = speaker
#         current_start = turn.start
#         current_end = turn.end
#       else:
#         current_end = turn.end
#     # Append the last segment
#     if current_speaker is not None:
#       ret.append({
#         'segment': i,
#         'start': current_start,
#         'end': current_end,
#         'speaker': current_speaker,
#       })
#     return ret
#
#   def detect_segments(self):
#     """Find the speakers in the sound file."""
#     # if we've already done the hard work of finding the segments,
#     # just return the cache
#     if os.path.exists(self.paths_json) and not self.args.reset:
#       with open(self.paths_json, 'r') as f: ret = json.load(f)
#       self.logger.info("Loaded speakers")
#       return ret
#
#     # otherwise we have some computationally expensive tasks to do
#     # Detect device (MPS for Apple Silicon or CPU)
#     with self.logger.indent("Detecting Speakers"):
#       # these libraries are slow to load (like 8 or 9 seconds!)
#       # so I only load them as needed
#       with self.logger.timer("Loaded libraries"):
#         from pyannote.audio import Pipeline
#
#       # use graphics acceleration if possible
#       nm = "mps" if torch.backends.mps.is_available() else "cpu"
#       self.logger.info(f"Using {nm}")
#       device = torch.device(nm)
#
#       # Load pre-trained Pyannote diarization model
#       hf_token = os.getenv('HUGGINGFACE_TOKEN')
#       pipeline = Pipeline.from_pretrained(
#         "pyannote/speaker-diarization-3.1",
#         cache_dir='models',
#         use_auth_token=hf_token
#       )
#       with self.logger.timer("Initialized pipeline"):
#         pipeline.to(device)
#
#       # Apply diarization to the audio file to get speakers
#       # I cannot set weights_only=True in torchaudio, so just supress this warning for now
#       with self.logger.indent("Calling speakers", True):
#         self.logger.info("NB: this may take a while for large files")
#         warnings.filterwarnings(action='ignore', message='You are using `torch.load`')
#         waveform, sample_rate = torchaudio.load(self.path_audio) #, weights_only=True)
#         diarization = pipeline({
#           "waveform": waveform,
#           "sample_rate": sample_rate
#         })
#
#       # Merge contiguous speaker segments
#       self.segments = self.merge_segments(diarization)
#       with self.logger.timer("Saved"):
#         with open(self.path_json, 'w') as f:
#           json.dump(self.segments, f)
#
#   def abs_from_rel(self, rel):
#     return os.path.join(self.paths.path('segments'), os.path.basename(rel))
#
#   def extract_segments(self):
#     """Extract the segments to individual files"""
#
#     # add in the file name and figure which ones are outstanding
#     fmt = '{:0' + str(len(str(len(self.segments)))) + 'd}.mp3'
#     todo = []
#     for i in range(len(self.segments)):
#       # the project relative path
#       rel = self.segments[i]['path_audio'] = os.path.join('segments', fmt.format(i))
#       # the absolute path
#       abs = self.abs_from_rel(rel)
#       # do we need to run this one?
#       if not os.path.exists(abs) or self.args.reset: todo.append(i)
#
#     # nothing to do so skip the logging
#     if len(todo) == 0: return
#
#     # extract the segments
#     with self.logger.indent("Getting Segments", True):
#       # buffer all the IO up front for faster saves
#       audio = AudioSegment.from_mp3(self.path_audio)
#       segment_buffers = []
#
#       # Just get a list of the coordinates in the audio
#       with self.logger.timer("Buffering"):
#         for i in todo:
#           # Slice the segment and store it in a BytesIO buffer
#           start_ms = int(self.segments[i]['start'] * 1000)
#           end_ms = int(self.segments[i]['end'] * 1000)
#           segment_audio = audio[start_ms:end_ms]
#
#           # Use BytesIO to store audio in memory
#           buffer = BytesIO()
#           segment_audio.export(buffer, format='wav')
#           rel = self.segments[i]['path_audio']
#           abs = self.abs_from_rel(rel)
#           segment_buffers.append((abs, buffer))
#
#       with self.logger.progress("Writing", len(todo)) as prog:
#         # Now, export each buffered segment to disk
#         for path, buffer in segment_buffers:
#           with open(path, 'wb') as f:
#             f.write(buffer.getvalue())
#           buffer.close()
#           prog.next()
#
#   def run(self):
#     with self.logger.indent("Identifying speakers", True):
#       self.detect_segments()
#       self.extract_segments()