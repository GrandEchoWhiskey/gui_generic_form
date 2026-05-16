import logging
import tkinter as tk


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
