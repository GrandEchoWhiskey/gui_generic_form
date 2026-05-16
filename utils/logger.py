import logging
from datetime import datetime
from pathlib import Path


def build_root_logger(log_file: str = "gui_form.log") -> logging.Logger:
	"""Create shared file+console logger once for the whole app."""
	logger = logging.getLogger("gui_form")
	logger.setLevel(logging.DEBUG)
	logger.propagate = False

	if logger.handlers:
		return logger

	formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

	file_handler = logging.FileHandler(Path(log_file), encoding="utf-8")
	file_handler.setFormatter(formatter)
	logger.addHandler(file_handler)

	console_handler = logging.StreamHandler()
	console_handler.setFormatter(formatter)
	logger.addHandler(console_handler)

	return logger


def create_window_logger(root_logger: logging.Logger, window_name: str) -> logging.Logger:
	"""Create a child logger for each opened window."""
	stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
	child = logging.getLogger(f"{root_logger.name}.{window_name}.{stamp}")
	child.setLevel(root_logger.level)
	child.handlers.clear()
	child.propagate = True
	return child
