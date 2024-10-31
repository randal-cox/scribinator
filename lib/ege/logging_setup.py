import logging, os, sys, time, inspect, datetime
from contextlib import contextmanager
from functools import lru_cache

from .utils import format_elapsed_time

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
    def indent(self, name, timer=False):
        start = time.time()
        self.info(name)
        self.indent_level += 2
        try:
            yield
        finally:
            self.indent_level -= 2
        end = time.time()
        if timer:
            elapsed = format_elapsed_time(end - start)
            self.info(f'{name}: {elapsed} seconds')

    @contextmanager
    def timer(self, name):
        start = time.time()
        #try:
        yield
        #except
        end = time.time()
        elapsed = format_elapsed_time(end - start)
        self.info(f'{name}: {elapsed}')

    def exit(self, message=None):
        previous_frame = inspect.currentframe().f_back
        (filename, line_number, function_name, _, _) = inspect.getframeinfo(previous_frame)
        file_name = os.path.basename(filename)
        prefix = f"Exiting from {file_name}:{line_number} {function_name}"
        message = prefix if message is None else prefix + ': ' + message
        self.critical(message)
        sys.exit()

    def makeRecord(self, *args, **kwargs):
        record = super().makeRecord(*args, **kwargs)
        record.indent_level = self.indent_level
        return record

    @contextmanager
    def progress(self, name, length, width=30):
        with self.indent(name):
            progress_chars = width  # Set exact width
            start_time = time.time()
            last_update = time.time()  # Track last update time

            class Progress:
                def __init__(self, logger, progress_chars, length):
                    self.logger = logger
                    self.progress_chars = progress_chars
                    self.length = length
                    self.completed_steps = 0
                    self.start_time = start_time
                    self.last_update = last_update

                def next(self, steps=1):
                    self.completed_steps += steps
                    fraction_completed = self.completed_steps / self.length
                    completed_chars = int(fraction_completed * self.progress_chars)
                    remaining_chars = self.progress_chars - completed_chars
                    percentage = fraction_completed * 100

                    # Calculate the elapsed and estimated remaining time
                    elapsed_time = time.time() - self.start_time
                    if self.completed_steps > 0:
                        estimated_total_time = elapsed_time / fraction_completed
                        remaining_time = max(0, estimated_total_time - elapsed_time)
                    else:
                        remaining_time = 0

                    bar = '=' * completed_chars + ' ' * remaining_chars
                    progress_message = (
                        f"[{bar}] {percentage:5.1f}% done | "
                        f"{human_time(int(remaining_time)) + ' left':<12} | Step {self.completed_steps:,}/{self.length:,}"
                    )

                    # Update based on time or if steps is specified
                    current_time = time.time()
                    if steps > 1 or current_time - self.last_update >= 1:
                        self.logger.info(progress_message)
                        self.last_update = current_time

            try:
                yield Progress(self, progress_chars, length)
            finally:
                elapsed_time = time.time() - start_time
                self.info(f"{name} completed: {length:,} steps in {human_time(int(elapsed_time))}")


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
