import logging
import tkinter as tk
from datetime import datetime
from pathlib import Path


class GUIHandler(logging.Handler):
	"""Logging handler that writes formatted messages into a read-only Tk Text widget."""

	def __init__(self, text_widget: tk.Text):
		super().__init__()
		self.text_widget = text_widget

	def emit(self, record: logging.LogRecord) -> None:
		message = self.format(record)
		level_name = record.levelname.upper()

		def append() -> None:
			self.text_widget.configure(state=tk.NORMAL)
			self.text_widget.insert(tk.END, message + "\n", level_name)
			self.text_widget.see(tk.END)
			self.text_widget.configure(state=tk.DISABLED)

		self.text_widget.after(0, append)


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
