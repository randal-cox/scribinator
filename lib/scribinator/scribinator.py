from ege.logging import setup_logging

from .models import Models
from .paths import Paths
from .project import Project
from .segments import Segments
class Scribinator:
  def __init__(self, args: 'argparse.Namespace', path: str) -> None:
    """
      Set up the transcription process.

      Parameters:
      args (argparse.Namespace): The command line arguments parsed by argparse.
      path (str): The path for the transcription audio file.

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

    # set up the project
    self.paths = Paths(args, path)
    self.project = Project(args, path)
    self.models = Models(args)
    self.segments = Segments(args, path)

  def run(self):
    # set up the project
    self.project.run()

    # create the segment annotations
    s = self.segments
    s.detect()
    s.extract()
    s.transcribe()
    s.emotions()

    # then create the output files - probably built in another class
    # self.project.cleanup() or self.editor.run()



