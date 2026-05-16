from __future__ import annotations

import logging

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
from utils.logger import build_root_logger, create_window_logger


def open_form_window(root_logger) -> None:
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
