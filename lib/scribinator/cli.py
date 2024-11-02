#!./venv/bin/python3

import argparse, sys, time, os, logging
from ege.logging import setup_logging

"""
  Standard argument parsing workflow
  
    parser = argparse.ArgumentParser(description="Transcribe and annotate an audio file")
    cli_start(parser)

    # script-specific switches
    parser.add_argument('--title', type=str, default=None, help="The title of the audio file")
    parser.add_argument('files', nargs='*', help="Audio files to be processed.")

    # get everything wrapped up
    args, logger = cli_end(parser)
"""

def cli_start(parser):
  """Call this at the start of your arg parsing"""
  # force recalculation from the ground up
  parser.add_argument('-r', '--reset', action='store_true', default=False, help="Recompute all files from scratch")

  # Define verbosity levels
  parser.add_argument('-q', '--quiet', action='store_const', const=0, help="Run in quiet mode (verbosity level 0).")
  parser.add_argument('-v', '--verbose', action='count', default=0,
                      help="Increase verbosity level (use -vv or -vvv for more).")

  # where the models folder is kept
  parser.add_argument('--models', type=str, default=None, help="Where the model files are kept")


def cli_end(parser):
  """Call this at the end of your arg parsing"""
  # get the args as a namespace and clean up the verbosity/quiet switches
  args = parser.parse_args()
  if args.quiet is not None:
      args.verbosity = args.quiet
  else:
      args.verbosity = max(2, args.verbose)
  del args.quiet
  del args.verbose

  # Setup custom logger and set the verbosity
  logger = setup_logging()
  if args.verbosity == 0:
    logger.setLevel(logging.CRITICAL)
  elif args.verbosity == 1:
    logger.setLevel(logging.WARNING)
  elif args.verbosity == 2:
    logger.setLevel(logging.INFO)
  elif args.verbosity == 3:
    logger.setLevel(logging.DEBUG)
  else:
    logger.setLevel(logging.INFO)

  # show our parameters
  with logger.indent("Settings"):
    for k, v in vars(args).items():
      if k == 'files': continue
      logger.info(f"{k + ':':<20s} {v}")

  return args, logger
