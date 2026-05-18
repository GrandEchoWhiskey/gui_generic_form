"""
Improved form builder with Field objects instead of dicts.
Features:
  - Field class hierarchy for type-safe field definitions
  - Access to logging textarea widget via FormResult
  - Optional arguments and builder patterns
  - Cleaner, more intuitive API
"""

import logging
import inspect
import tkinter as tk
import calendar as pycalendar
from datetime import datetime
from tkinter import ttk
from dataclasses import dataclass
from typing import Any, Callable, Optional, Dict, List
from utils.logger import GUIHandler


class FormParentContext:
	"""Helper object passed to button callbacks for form-level operations."""

	def __init__(self, root, get_values, set_value, reset_field, reset_fields, reset_all, logger):
		self.root = root
		self.get_values = get_values
		self.set_value = set_value
		self.reset_field = reset_field
		self.reset_fields = reset_fields
		self.reset_all = reset_all
		self._logger = logger

	def log_debug(self, message, *args, **kwargs):
		self._logger.debug(message, *args, **kwargs)

	def log_info(self, message, *args, **kwargs):
		self._logger.info(message, *args, **kwargs)

	def log_warning(self, message, *args, **kwargs):
		self._logger.warning(message, *args, **kwargs)

	def log_error(self, message, *args, **kwargs):
		self._logger.error(message, *args, **kwargs)

	def log_critical(self, message, *args, **kwargs):
		self._logger.critical(message, *args, **kwargs)

	def log_exception(self, message, *args, **kwargs):
		self._logger.exception(message, *args, **kwargs)


@dataclass
class FormResult:
	"""Result object containing submitted values and logger widget."""
	values: Dict[str, Any]
	log_widget: tk.Text
	logger: logging.Logger

	def get_values(self) -> Dict[str, Any]:
		"""Return submitted field values."""
		return self.values

	def get_log_widget(self) -> tk.Text:
		"""Return the logging textarea widget for direct manipulation."""
		return self.log_widget

	def get_logger(self) -> logging.Logger:
		"""Return the logger instance."""
		return self.logger

	def clear_logs(self) -> None:
		"""Clear all log messages."""
		self.log_widget.configure(state=tk.NORMAL)
		self.log_widget.delete("1.0", tk.END)
		self.log_widget.configure(state=tk.DISABLED)


# ============================================================================
# Field Class Hierarchy
# ============================================================================

class Field:
	"""Base class for all form fields."""

	def __init__(
		self,
		name: str,
		label: Optional[str] = None,
		default: Any = "",
		required: bool = False,
		help_text: Optional[str] = None,
	):
		self.name = name
		self.label = label if label is not None else name.title()
		self.default = default
		self.required = required
		self.help_text = help_text

	def to_dict(self) -> Dict[str, Any]:
		"""Convert field to dict format for internal use."""
		raise NotImplementedError


class TextField(Field):
	"""Single-line text input field."""

	def to_dict(self) -> Dict[str, Any]:
		return {
			"name": self.name,
			"label": self.label,
			"type": "textbox",
			"default": self.default,
		}


class NumericField(Field):
	"""Numeric spinbox field."""

	def __init__(
		self,
		name: str,
		label: Optional[str] = None,
		default: int = 0,
		min_value: int = -999999,
		max_value: int = 999999,
		step: int = 1,
		required: bool = False,
		help_text: Optional[str] = None,
	):
		super().__init__(name, label, default, required, help_text)
		self.min_value = min_value
		self.max_value = max_value
		self.step = step

	def to_dict(self) -> Dict[str, Any]:
		return {
			"name": self.name,
			"label": self.label,
			"type": "numeric",
			"default": self.default,
			"min": self.min_value,
			"max": self.max_value,
		}


class CheckboxField(Field):
	"""Checkbox boolean field."""

	def __init__(
		self,
		name: str,
		label: Optional[str] = None,
		default: bool = False,
		required: bool = False,
		help_text: Optional[str] = None,
	):
		super().__init__(name, label, default, required, help_text)

	def to_dict(self) -> Dict[str, Any]:
		return {
			"name": self.name,
			"label": self.label,
			"type": "checkbox",
			"default": self.default,
		}


class DropdownField(Field):
	"""Dropdown/combobox field with predefined options."""

	def __init__(
		self,
		name: str,
		options: List[str],
		label: Optional[str] = None,
		default: Optional[str] = None,
		required: bool = False,
		help_text: Optional[str] = None,
	):
		if default is None:
			default = options[0] if options else ""
		super().__init__(name, label, default, required, help_text)
		self.options = options

	def to_dict(self) -> Dict[str, Any]:
		return {
			"name": self.name,
			"label": self.label,
			"type": "dropdown",
			"options": self.options,
			"default": self.default,
		}


class RadioField(Field):
	"""Radio button field with multiple options."""

	def __init__(
		self,
		name: str,
		options: List[str],
		label: Optional[str] = None,
		default: Optional[str] = None,
		required: bool = False,
		help_text: Optional[str] = None,
	):
		if default is None:
			default = options[0] if options else ""
		super().__init__(name, label, default, required, help_text)
		self.options = options

	def to_dict(self) -> Dict[str, Any]:
		return {
			"name": self.name,
			"label": self.label,
			"type": "radio",
			"options": self.options,
			"default": self.default,
		}


class DateField(Field):
	"""Date picker field."""

	def __init__(
		self,
		name: str,
		label: Optional[str] = None,
		default: Optional[str] = None,
		date_format: str = "%Y-%m-%d",
		required: bool = False,
		help_text: Optional[str] = None,
	):
		if default is None:
			default = datetime.now().strftime(date_format)
		super().__init__(name, label, default, required, help_text)
		self.date_format = date_format

	def to_dict(self) -> Dict[str, Any]:
		return {
			"name": self.name,
			"label": self.label,
			"type": "date",
			"default": self.default,
			"format": self.date_format,
		}


class TimeField(Field):
	"""Time picker field."""

	def __init__(
		self,
		name: str,
		label: Optional[str] = None,
		default: Optional[str] = None,
		time_format: str = "%H:%M:%S",
		required: bool = False,
		help_text: Optional[str] = None,
	):
		if default is None:
			default = datetime.now().strftime(time_format)
		super().__init__(name, label, default, required, help_text)
		self.time_format = time_format

	def to_dict(self) -> Dict[str, Any]:
		return {
			"name": self.name,
			"label": self.label,
			"type": "time",
			"default": self.default,
			"format": self.time_format,
		}


class TextAreaField(Field):
	"""Multi-line textarea field."""

	def __init__(
		self,
		name: str,
		label: Optional[str] = None,
		default: str = "",
		height: int = 4,
		required: bool = False,
		help_text: Optional[str] = None,
	):
		super().__init__(name, label, default, required, help_text)
		self.height = height

	def to_dict(self) -> Dict[str, Any]:
		return {
			"name": self.name,
			"label": self.label,
			"type": "textarea",
			"default": self.default,
			"height": self.height,
		}


class ButtonField:
	"""Action button field."""

	def __init__(
		self,
		on_click: Callable,
		label: Optional[str] = None,
		name: Optional[str] = None,
	):
		self.label = label if label is not None else (name.title() if name else "Action")
		self.on_click = on_click
		self.name = name

	def to_dict(self) -> Dict[str, Any]:
		return {
			"type": "button",
			"label": self.label,
			"text": self.label,
			"on_click": self.on_click,
		}


class TableViewField(Field):
	"""Read-only table view field backed by ttk.Treeview."""

	def __init__(
		self,
		name: str,
		columns: List[str],
		rows: Optional[List[List[Any]]] = None,
		label: Optional[str] = None,
		height: int = 6,
		required: bool = False,
		help_text: Optional[str] = None,
	):
		super().__init__(name, label, rows or [], required, help_text)
		if not columns:
			raise ValueError("TableViewField requires at least one column.")
		self.columns = columns
		self.rows = rows or []
		self.height = height

	def to_dict(self) -> Dict[str, Any]:
		return {
			"name": self.name,
			"label": self.label,
			"type": "tableview",
			"columns": self.columns,
			"rows": self.rows,
			"height": self.height,
		}


# ============================================================================
# Helper Functions (from main.py)
# ============================================================================

def _parse_datetime(value: str, fmt: str, fallback: datetime | None = None) -> datetime:
	if fallback is None:
		fallback = datetime.now()
	try:
		return datetime.strptime(value, fmt)
	except (TypeError, ValueError):
		return fallback


def _open_date_picker(root, anchor_widget, text_var, date_format):
	"""Open a small calendar popup near the target widget and write chosen date to text_var."""
	selected = _parse_datetime(text_var.get(), date_format)
	today = datetime.now()
	state = {"year": selected.year, "month": selected.month, "day": selected.day}

	popup = tk.Toplevel(root)
	popup.title("Pick Date")
	popup.transient(root)
	popup.resizable(False, False)

	x = anchor_widget.winfo_rootx()
	y = anchor_widget.winfo_rooty() + anchor_widget.winfo_height() + 4
	popup.geometry(f"+{x}+{y}")

	main = ttk.Frame(popup, padding=8)
	main.pack(fill="both", expand=True)

	header = ttk.Frame(main)
	header.pack(fill="x")

	month_label = ttk.Label(header, anchor="center")
	month_label.pack(side="left", expand=True)

	body = ttk.Frame(main)
	body.pack(fill="both", expand=True, pady=(6, 4))

	for col, weekday in enumerate(["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]):
		ttk.Label(body, text=weekday, width=4, anchor="center").grid(row=0, column=col, padx=1, pady=1)

	day_buttons = []

	def pick_day(day):
		state["day"] = day
		picked = datetime(state["year"], state["month"], state["day"])
		text_var.set(picked.strftime(date_format))
		popup.destroy()

	def choose_today():
		state["year"] = today.year
		state["month"] = today.month
		pick_day(today.day)

	def render_calendar():
		month_label.config(
			text=f"{pycalendar.month_name[state['month']]} {state['year']}"
		)

		for btn in day_buttons:
			btn.destroy()
		day_buttons.clear()

		matrix = pycalendar.Calendar(firstweekday=0).monthdayscalendar(
			state["year"], state["month"]
		)

		for row, week in enumerate(matrix, start=1):
			for col, day in enumerate(week):
				if day == 0:
					ttk.Label(body, text="", width=4).grid(row=row, column=col, padx=1, pady=1)
					continue

				btn = tk.Button(
					body,
					text=str(day),
					width=3,
					command=lambda d=day: pick_day(d),
				)

				if (
					state["year"] == today.year
					and state["month"] == today.month
					and day == today.day
				):
					btn.configure(relief=tk.SOLID, bd=2)

				if day == state["day"]:
					btn.configure(bg="#d9ebff")

				btn.grid(row=row, column=col, padx=1, pady=1)
				day_buttons.append(btn)

	def change_month(delta):
		month = state["month"] + delta
		year = state["year"]
		if month < 1:
			month = 12
			year -= 1
		elif month > 12:
			month = 1
			year += 1
		state["month"] = month
		state["year"] = year

		last_day = pycalendar.monthrange(year, month)[1]
		state["day"] = min(state["day"], last_day)
		render_calendar()

	ttk.Button(header, text="<", width=3, command=lambda: change_month(-1)).pack(side="left")
	ttk.Button(header, text=">", width=3, command=lambda: change_month(1)).pack(side="right")

	ttk.Button(main, text="Today", command=choose_today).pack(anchor="e", pady=(2, 0))

	render_calendar()
	popup.grab_set()
	popup.focus_force()


def _open_time_picker(root, anchor_widget, text_var, time_format):
	"""Open a popup with HH:MM:SS spinboxes for time selection."""
	parsed = _parse_datetime(text_var.get(), time_format)

	hour_var = tk.IntVar(value=parsed.hour)
	minute_var = tk.IntVar(value=parsed.minute)
	second_var = tk.IntVar(value=parsed.second)

	popup = tk.Toplevel(root)
	popup.title("Pick Time")
	popup.transient(root)
	popup.resizable(False, False)

	x = anchor_widget.winfo_rootx()
	y = anchor_widget.winfo_rooty() + anchor_widget.winfo_height() + 4
	popup.geometry(f"+{x}+{y}")

	main = ttk.Frame(popup, padding=8)
	main.pack(fill="both", expand=True)

	entry_row = ttk.Frame(main)
	entry_row.pack(fill="x", pady=(0, 6))

	ttk.Label(entry_row, text="Time").pack(side="left")
	hour_spin = tk.Spinbox(entry_row, from_=0, to=23, width=3, textvariable=hour_var, format="%02.0f")
	hour_spin.pack(side="left", padx=(4, 0))
	ttk.Label(entry_row, text=":").pack(side="left", padx=2)
	minute_spin = tk.Spinbox(entry_row, from_=0, to=59, width=3, textvariable=minute_var, format="%02.0f")
	minute_spin.pack(side="left")
	ttk.Label(entry_row, text=":").pack(side="left", padx=2)
	second_spin = tk.Spinbox(entry_row, from_=0, to=59, width=3, textvariable=second_var, format="%02.0f")
	second_spin.pack(side="left")

	def _clamp_time_vars():
		hour_var.set(max(0, min(23, int(hour_var.get()))))
		minute_var.set(max(0, min(59, int(minute_var.get()))))
		second_var.set(max(0, min(59, int(second_var.get()))))

	def _set_time_fields(hour: int, minute: int, second: int):
		hour_spin.delete(0, tk.END)
		hour_spin.insert(0, f"{hour:02d}")
		minute_spin.delete(0, tk.END)
		minute_spin.insert(0, f"{minute:02d}")
		second_spin.delete(0, tk.END)
		second_spin.insert(0, f"{second:02d}")

	def apply_time():
		_clamp_time_vars()
		base = datetime.now().replace(
			hour=hour_var.get(), minute=minute_var.get(), second=second_var.get(), microsecond=0
		)
		text_var.set(base.strftime(time_format))
		popup.destroy()

	button_row = ttk.Frame(main)
	button_row.pack(fill="x", pady=(2, 0))
	ttk.Button(
		button_row,
		text="Now",
		command=lambda: _set_time_fields(
			datetime.now().hour,
			datetime.now().minute,
			datetime.now().second,
		),
	).pack(side="left")
	ttk.Button(button_row, text="Apply", command=apply_time).pack(side="right")

	popup.grab_set()
	popup.focus_force()


def _build_default_logger() -> logging.Logger:
	logger = logging.getLogger("tk_form_builder")
	logger.setLevel(logging.INFO)
	logger.handlers.clear()
	return logger


def _create_log_text_handler(log_text: tk.Text) -> GUIHandler:
	text_handler = GUIHandler(log_text)
	text_handler.setLevel(logging.INFO)
	text_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
	return text_handler


def _resolve_logger(
	logger: Optional[logging.Logger],
	logger_setup: Optional[Callable[..., Optional[logging.Logger]]],
) -> logging.Logger:
	resolved_logger = logger or _build_default_logger()

	if logger_setup is None:
		return resolved_logger

	try:
		configured_logger = logger_setup(resolved_logger)
	except TypeError:
		configured_logger = logger_setup()

	if configured_logger is not None:
		return configured_logger

	return resolved_logger


# ============================================================================
# Main Form Builder
# ============================================================================

def create_form_window(
	fields: List,
	title: str = "Generic Tk Form",
	on_save: Optional[Callable] = None,
	window_width: int = 700,
	window_height: int = 500,
	show_logs: bool = True,
	log_height: int = 8,
	logger: Optional[logging.Logger] = None,
	logger_setup: Optional[Callable[..., Optional[logging.Logger]]] = None,
) -> FormResult:
	"""
	Create and run a generic Tkinter form with Field objects.

	Args:
		fields: List of Field objects (TextField, NumericField, etc.) or ButtonField.
		title: Window title.
		on_save: Optional callback receiving the FormResult object.
		window_width: Initial window width.
		window_height: Initial window height.
		show_logs: Whether to display the logging textarea.
		log_height: Height of the logging textarea in lines.
		logger: Optional logging.Logger instance. If None, creates a default logger.
		logger_setup: Optional callable that receives the logger to configure and may
			return the configured logger. A zero-argument callable returning a logger is
			also supported.

	Returns:
		FormResult: Object containing submitted values, log widget, and logger.
	"""

	# Convert Field objects to dicts for internal processing
	field_dicts = []
	for f in fields:
		if hasattr(f, "to_dict"):
			field_dicts.append(f.to_dict())
		elif isinstance(f, dict):
			field_dicts.append(f)
		else:
			raise ValueError(f"Invalid field type: {type(f)}")

	root = tk.Tk()
	root.title(title)
	root.minsize(window_width, window_height)

	container = ttk.Frame(root, padding=12)
	container.pack(fill=tk.BOTH, expand=True)

	form_frame = ttk.Frame(container)
	form_frame.pack(fill=tk.BOTH, expand=True)

	state = {}
	result = {}
	log_text = None

	logger = _resolve_logger(logger, logger_setup)

	def normalize_type(raw_type):
		return (raw_type or "textbox").strip().lower()

	def collect_values():
		values = {}
		for key, meta in state.items():
			if meta["kind"] == "var":
				values[key] = meta["value"].get()
			elif meta["kind"] == "text":
				values[key] = meta["value"].get("1.0", "end-1c")
			elif meta["kind"] == "table":
				tree = meta["value"]
				columns = meta["columns"]
				rows = []
				for item_id in tree.get_children(""):
					item_values = tree.item(item_id, "values")
					rows.append(dict(zip(columns, item_values)))
				values[key] = rows
			else:
				values[key] = meta.get("value")
		return values

	def _set_value(meta, value):
		if meta["kind"] == "var":
			meta["value"].set(value)
		elif meta["kind"] == "text":
			meta["value"].delete("1.0", tk.END)
			if value:
				meta["value"].insert("1.0", str(value))
		elif meta["kind"] == "table":
			tree = meta["value"]
			for item_id in tree.get_children(""):
				tree.delete(item_id)
			for row in value or []:
				if isinstance(row, dict):
					row_values = [row.get(col, "") for col in meta["columns"]]
				else:
					row_values = list(row)
				tree.insert("", tk.END, values=row_values)

	def reset_field(field_name):
		meta = state.get(field_name)
		if not meta:
			logger.warning("Cannot reset '%s': field not found.", field_name)
			return
		_set_value(meta, meta.get("default", ""))

	def set_field_value(field_name, value):
		meta = state.get(field_name)
		if not meta:
			logger.warning("Cannot set '%s': field not found.", field_name)
			return
		_set_value(meta, value)

	def reset_fields(field_names):
		for field_name in field_names:
			reset_field(field_name)

	def reset_all_fields():
		for field_name in list(state.keys()):
			reset_field(field_name)

	parent = FormParentContext(
		root=root,
		get_values=collect_values,
		set_value=set_field_value,
		reset_field=reset_field,
		reset_fields=reset_fields,
		reset_all=reset_all_fields,
		logger=logger,
	)

	def invoke_button_callback(callback, values):
		try:
			signature = inspect.signature(callback)
		except (TypeError, ValueError):
			callback(parent, values)
			return

		params = list(signature.parameters.values())
		has_varargs = any(p.kind == inspect.Parameter.VAR_POSITIONAL for p in params)
		positional = [
			p
			for p in params
			if p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
		]

		if has_varargs or len(positional) >= 2:
			callback(parent, values)
		elif len(positional) == 1:
			callback(parent)
		else:
			callback()

	for row_idx, field in enumerate(field_dicts):
		field_type = normalize_type(field.get("type", "textbox"))
		name = field.get("name")

		if field_type not in {"button", "action"} and not name:
			raise ValueError("Every non-button field must include a non-empty 'name'.")

		if field_type in {"button", "action"}:
			label_text = field.get("label", "")
		else:
			label_text = field.get("label", name)

		if label_text:
			ttk.Label(form_frame, text=label_text).grid(
				row=row_idx, column=0, sticky="w", padx=(0, 8), pady=4
			)

		if field_type in {"textbox", "text", "entry"}:
			var = tk.StringVar(value=str(field.get("default", "")))
			widget = ttk.Entry(form_frame, textvariable=var, width=40)
			widget.grid(row=row_idx, column=1, sticky="ew", pady=4)
			state[name] = {"kind": "var", "value": var, "default": var.get()}

		elif field_type in {"numeric", "number", "int", "integer", "spinbox", "spinner"}:
			minimum = int(field.get("min", -999999))
			maximum = int(field.get("max", 999999))
			default = int(field.get("default", 0))
			default = max(minimum, min(maximum, default))
			var = tk.IntVar(value=default)
			widget = tk.Spinbox(
				form_frame,
				from_=minimum,
				to=maximum,
				increment=1,
				textvariable=var,
				width=38,
			)
			widget.grid(row=row_idx, column=1, sticky="ew", pady=4)
			state[name] = {"kind": "var", "value": var, "default": var.get()}

		elif field_type in {"checkbox", "check", "bool", "boolean"}:
			var = tk.BooleanVar(value=bool(field.get("default", False)))
			widget = ttk.Checkbutton(form_frame, variable=var)
			widget.grid(row=row_idx, column=1, sticky="w", pady=4)
			state[name] = {"kind": "var", "value": var, "default": var.get()}

		elif field_type in {"dropdown", "dropbox", "combobox", "select"}:
			options = list(field.get("options", []))
			default = field.get("default")
			if default is None:
				default = options[0] if options else ""
			var = tk.StringVar(value=str(default))
			widget = ttk.Combobox(
				form_frame,
				textvariable=var,
				values=options,
				state="readonly",
				width=37,
			)
			widget.grid(row=row_idx, column=1, sticky="ew", pady=4)
			state[name] = {"kind": "var", "value": var, "default": var.get()}

		elif field_type in {"radio", "radiobutton"}:
			options = list(field.get("options", []))
			if not options:
				raise ValueError(f"Radio field '{name}' requires an 'options' list.")

			default = field.get("default", options[0])
			var = tk.StringVar(value=str(default))
			holder = ttk.Frame(form_frame)
			holder.grid(row=row_idx, column=1, sticky="w", pady=4)
			for col_idx, option in enumerate(options):
				ttk.Radiobutton(holder, text=str(option), value=str(option), variable=var).grid(
					row=0, column=col_idx, padx=(0, 8), sticky="w"
				)
			state[name] = {"kind": "var", "value": var, "default": var.get()}

		elif field_type in {"date", "datepicker"}:
			date_format = field.get("format", "%Y-%m-%d")
			default = field.get("default")
			if default is None:
				default = datetime.now().strftime(date_format)
			var = tk.StringVar(value=str(default))
			picker_row = ttk.Frame(form_frame)
			picker_row.grid(row=row_idx, column=1, sticky="ew", pady=4)
			widget = ttk.Entry(picker_row, textvariable=var, width=34)
			widget.pack(side="left", fill="x", expand=True)
			ttk.Button(
				picker_row,
				text="Pick",
				command=lambda w=widget, v=var, f=date_format: _open_date_picker(root, w, v, f),
			).pack(side="left", padx=(6, 0))
			widget.bind(
				"<Button-1>",
				lambda _e, w=widget, v=var, f=date_format: _open_date_picker(root, w, v, f),
			)
			state[name] = {
				"kind": "var",
				"value": var,
				"default": var.get(),
				"type": "date",
				"format": date_format,
			}

		elif field_type in {"time", "timepicker"}:
			time_format = field.get("format", "%H:%M:%S")
			default = field.get("default")
			if default is None:
				default = datetime.now().strftime(time_format)
			var = tk.StringVar(value=str(default))
			picker_row = ttk.Frame(form_frame)
			picker_row.grid(row=row_idx, column=1, sticky="ew", pady=4)
			widget = ttk.Entry(picker_row, textvariable=var, width=34)
			widget.pack(side="left", fill="x", expand=True)
			ttk.Button(
				picker_row,
				text="Pick",
				command=lambda w=widget, v=var, f=time_format: _open_time_picker(root, w, v, f),
			).pack(side="left", padx=(6, 0))
			widget.bind(
				"<Button-1>",
				lambda _e, w=widget, v=var, f=time_format: _open_time_picker(root, w, v, f),
			)
			state[name] = {
				"kind": "var",
				"value": var,
				"default": var.get(),
				"type": "time",
				"format": time_format,
			}

		elif field_type in {"textarea", "multiline"}:
			height = int(field.get("height", 4))
			widget = tk.Text(form_frame, height=height, width=40, wrap="word")
			widget.grid(row=row_idx, column=1, sticky="ew", pady=4)
			default = field.get("default", "")
			if default:
				widget.insert("1.0", str(default))
			state[name] = {"kind": "text", "value": widget, "default": str(default)}

		elif field_type in {"button", "action"}:
			button_text = field.get("text") or field.get("label") or "Action"
			on_click = field.get("on_click")

			def handle_custom_click(callback=on_click, text=button_text):
				values = collect_values()
				if callable(callback):
					invoke_button_callback(callback, values)
				else:
					logger.warning("Button '%s' has no callable on_click.", text)

			ttk.Button(
				form_frame,
				text=button_text,
				command=handle_custom_click,
			).grid(row=row_idx, column=1, sticky="w", pady=4)

		elif field_type in {"tableview", "table", "treeview"}:
			columns = [str(col) for col in field.get("columns", [])]
			if not columns:
				raise ValueError(f"Table field '{name}' requires a non-empty 'columns' list.")

			rows = field.get("rows", []) or []
			height = int(field.get("height", 6))

			table_holder = ttk.Frame(form_frame)
			table_holder.grid(row=row_idx, column=1, sticky="nsew", pady=4)
			tree = ttk.Treeview(
				table_holder,
				columns=columns,
				show="headings",
				height=height,
			)
			for column_name in columns:
				tree.heading(column_name, text=column_name)
				tree.column(column_name, anchor="w", width=120, stretch=True)

			for row in rows:
				if isinstance(row, dict):
					row_values = [row.get(col, "") for col in columns]
				else:
					row_values = list(row)
				tree.insert("", tk.END, values=row_values)

			v_scroll = ttk.Scrollbar(table_holder, orient="vertical", command=tree.yview)
			tree.configure(yscrollcommand=v_scroll.set)
			tree.grid(row=0, column=0, sticky="nsew")
			v_scroll.grid(row=0, column=1, sticky="ns")
			table_holder.columnconfigure(0, weight=1)
			table_holder.rowconfigure(0, weight=1)

			state[name] = {
				"kind": "table",
				"value": tree,
				"columns": columns,
				"default": rows,
			}

		else:
			raise ValueError(
				f"Unsupported field type '{field_type}' for field '{name}'."
			)

	form_frame.columnconfigure(1, weight=1)

	ttk.Separator(container, orient="horizontal").pack(fill="x", pady=8)

	if show_logs:
		ttk.Label(container, text="Logs").pack(anchor="w")
		log_text = tk.Text(container, height=log_height, state=tk.DISABLED, wrap="word")
		log_text.pack(fill=tk.BOTH, expand=True, pady=(4, 8))
		log_text.tag_configure("DEBUG", foreground="#4a4a4a")
		log_text.tag_configure("INFO", foreground="#1f6f3a")
		log_text.tag_configure("WARNING", foreground="#a66a00")
		log_text.tag_configure("ERROR", foreground="#b00020")
		log_text.tag_configure("CRITICAL", foreground="#b00020")

		logger.addHandler(_create_log_text_handler(log_text))
		logger.debug("Form window opened: %s", title)

	button_row = ttk.Frame(container)
	button_row.pack(fill="x")

	def save():
		nonlocal result
		values = collect_values()
		result = values
		if on_save:
			on_save(FormResult(values=values, log_widget=log_text, logger=logger))
		logger.debug("Window closed after saving.")
		root.quit()
		root.destroy()

	def on_close():
		logger.debug("Window closed without saving.")
		root.quit()
		root.destroy()

	ttk.Button(button_row, text="Save", command=save).pack(side="right")

	root.protocol("WM_DELETE_WINDOW", on_close)
	root.mainloop()
	
	return FormResult(values=result, log_widget=log_text, logger=logger)


if __name__ == "__main__":
	def build_demo_logger(base_logger: Optional[logging.Logger] = None) -> logging.Logger:
		logger = base_logger or logging.getLogger("tk_form_builder_demo")
		logger.setLevel(logging.DEBUG)
		logger.handlers.clear()

		file_handler = logging.FileHandler("form_builder_demo.log")
		file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
		logger.addHandler(file_handler)

		console_handler = logging.StreamHandler()
		console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
		logger.addHandler(console_handler)

		return logger

	def preview_values(parent: FormParentContext, values: dict):
		print("Current values:", values)
		parent.reset_fields(["notes", "start_time"])
		parent.log_info("Fields 'notes' and 'start_time' have been reset.")
		parent.set_value("username", "JohnDoe")

	# Using Field objects for cleaner, more type-safe definition
	sample_fields = [
		TextField("username"),
		NumericField("age", default=25, min_value=0, max_value=130),
		DropdownField("role", options=["Admin", "Editor", "Viewer"], default="Editor"),
		CheckboxField("newsletter"),
		RadioField("priority", options=["Low", "Medium", "High"], default="Medium"),
		DateField("start_date"),
		TimeField("start_time"),
		TextAreaField("notes", height=5),
		ButtonField(on_click=preview_values, label="Preview"),
	]

	result = create_form_window(
		sample_fields,
		title="Dynamic Tk Form with Field Objects",
		logger_setup=build_demo_logger,
	)
	
	# You can now access the log widget for custom operations if needed
	# log_widget = result.get_log_widget()
	# log_widget.configure(state=tk.NORMAL)
	# log_widget.insert(tk.END, "Custom log entry\n")
	# log_widget.configure(state=tk.DISABLED)
