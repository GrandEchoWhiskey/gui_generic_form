from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from analysis_view import run_dataframe_analyzer
from form_builder import (
	ButtonField,
	CheckboxField,
	DateField,
	DropdownField,
	NumericField,
	TextAreaField,
	TextField,
	TimeField,
	create_form_window,
)


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


def open_form_window(root_logger: logging.Logger) -> None:
	logger = create_window_logger(root_logger, "form")
	logger.debug("Form window opening.")

	def preview_values(parent, values):
		parent.log_info("Preview clicked with %s field values.", len(values))

	sample_fields = [
		TextField("username"),
		NumericField("age", default=25, min_value=0, max_value=130),
		DropdownField("role", options=["Admin", "Editor", "Viewer"], default="Editor"),
		CheckboxField("newsletter"),
		DateField("start_date"),
		TimeField("start_time"),
		TextAreaField("notes", height=5),
		ButtonField(on_click=preview_values, label="Preview"),
	]

	create_form_window(
		sample_fields,
		title="Dynamic Tk Form",
		logger=logger,
	)
	logger.debug("Form window closed.")


def open_analysis_window(root_logger: logging.Logger) -> None:
	logger = create_window_logger(root_logger, "analysis")
	logger.debug("Analysis window opening.")
	demo_df = pd.DataFrame(
		{
			"Name": ["Alice", "Bob", "Charlie"],
			"Age": [25, 30, 35],
			"City": ["NY", "LA", "Chicago"],
		}
	)
	result_df = run_dataframe_analyzer(demo_df, logger=logger)
	if result_df is not None:
		logger.debug("Analysis window closed with %s resulting rows.", len(result_df))
	else:
		logger.debug("Analysis window closed without a resulting DataFrame.")


def main() -> None:
	root_logger = build_root_logger()
	root_logger.debug("Application launcher started.")

	menu = (
		"\nSelect window to open:\n"
		"  1 - Form Builder\n"
		"  2 - Data Analyzer\n"
		"  q - Quit\n"
	)

	while True:
		print(menu)
		choice = input("Choice: ").strip().lower()
		if choice == "1":
			open_form_window(root_logger)
		elif choice == "2":
			open_analysis_window(root_logger)
		elif choice in {"q", "quit", "exit"}:
			root_logger.debug("Application launcher stopped.")
			break
		else:
			print("Unknown option. Choose 1, 2, or q.")


if __name__ == "__main__":
	main()
