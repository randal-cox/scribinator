import logging
import time
from contextlib import contextmanager
from functools import lru_cache

import logging
import time
from contextlib import contextmanager

import logging
import time
from contextlib import contextmanager

def human_time(seconds):
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    result = []
    if days > 0:
        result.append(f"{days}d")
    if hours > 0:
        result.append(f"{hours}h")
    if minutes > 0:
        result.append(f"{minutes}m")
    if seconds > 0 or len(result) == 0:
        result.append(f"{seconds}s")

    return ' '.join(result[:2])

# Set up logging with a custom format
class CustomFormatter(logging.Formatter):
    def __init__(self, start_time):
        super().__init__()
        self.start_time = start_time

    def format(self, record):
        elapsed_seconds = int(time.time() - self.start_time)
        elapsed_time_formatted = f"{human_time(elapsed_seconds):<8}"

        level = record.levelname.ljust(5)
        indent = ' ' * getattr(record, 'indent_level', 0)  # Handle indentation

        log_format = f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {elapsed_time_formatted} | {level} | {indent}{record.getMessage()}"
        return log_format

class CustomLogger(logging.getLoggerClass()):
    def __init__(self, name):
        super().__init__(name)
        self.indent_level = 0

    @contextmanager
    def indent(self, name):
        self.info(name)
        self.indent_level += 2  # Increase indent level
        try:
            yield
        finally:
            self.indent_level -= 2  # Reset indent level after context ends

    def makeRecord(self, *args, **kwargs):
        """Override the method to include the current indent level."""
        record = super().makeRecord(*args, **kwargs)
        record.indent_level = self.indent_level  # Apply indent level to the log record
        return record

    @contextmanager
    def progress(self, name, length, width=30):
        progress_chars = width - 2  # Subtracting 2 for the edges of the progress bar
        start_time = time.time()

        class Progress:
            def __init__(self, logger, progress_chars, length):
                self.logger = logger
                self.progress_chars = progress_chars
                self.length = length
                self.completed_steps = 0
                self.start_time = start_time

            def next(self):
                self.completed_steps += 1
                fraction_completed = self.completed_steps / self.length
                completed_chars = int(fraction_completed * self.progress_chars)
                remaining_chars = self.progress_chars - completed_chars
                percentage = fraction_completed * 100

                # Calculate the elapsed time
                elapsed_time = time.time() - self.start_time

                bar = '=' * completed_chars + ' ' * remaining_chars

                # Log the progress
                self.logger.info(
                    f"{name} | [{bar}] {percentage:.1f}% done | {self.completed_steps}/{self.length} "
                )

        try:
            yield Progress(self, progress_chars, length)
        finally:
            elapsed_time = time.time() - start_time
            self.info(f"{name} completed in {human_time(int(elapsed_time))}")

@lru_cache
def setup_logging(file_path=None):
    logging.setLoggerClass(CustomLogger)
    logger = logging.getLogger('custom_logger')
    logger.setLevel(logging.DEBUG)

    # Avoid adding multiple handlers by checking if handlers already exist
    if not logger.hasHandlers():
        start_time = time.time()

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(CustomFormatter(start_time))
        logger.addHandler(console_handler)

        if file_path:
            file_handler = logging.FileHandler(file_path)
            file_handler.setFormatter(CustomFormatter(start_time))
            logger.addHandler(file_handler)

    return logger
