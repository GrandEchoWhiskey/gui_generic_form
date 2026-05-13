import logging
import inspect
import tkinter as tk
import calendar as pycalendar
from datetime import datetime
from tkinter import ttk


class ReadOnlyTextHandler(logging.Handler):
	"""Logging handler that writes colored log messages into a read-only Text widget."""

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


def _parse_datetime(value: str, fmt: str, fallback: datetime | None = None) -> datetime:
	if fallback is None:
		fallback = datetime.now()
	try:
		return datetime.strptime(value, fmt)
	except (TypeError, ValueError):
		return fallback


def _open_date_picker(root, anchor_widget, text_var, date_format, logger):
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


def _open_time_picker(root, anchor_widget, text_var, time_format, logger):
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
		# Write zero-padded text directly so the popup always shows HH:MM:SS.
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


def create_form_window(fields, title="Generic Tk Form", on_save=None):
	"""
	Create and run a generic Tkinter form.

	Args:
		fields (list[dict]): List of field definitions.
			Supported field types: textbox, numeric, checkbox, dropdown/dropbox, radio, date, time, textarea, button.
			Button field callback supports both forms:
				on_click(parent)
				on_click(parent, values)
			where parent provides reset_field/reset_fields/reset_all helpers.
			Example field:
				{
					"name": "country",
					"label": "Country",
					"type": "dropdown",
					"options": ["PL", "DE", "US"],
					"default": "PL"
				}
		title (str): Window title.
		on_save (callable|None): Optional callback receiving the result dict.

	Returns:
		dict: Submitted field values. Returns empty dict if closed without Save.
	"""

	root = tk.Tk()
	root.title(title)
	root.minsize(700, 500)

	container = ttk.Frame(root, padding=12)
	container.pack(fill=tk.BOTH, expand=True)

	form_frame = ttk.Frame(container)
	form_frame.pack(fill=tk.BOTH, expand=True)

	state = {}
	result = {}
	parent = None

	logger = logging.getLogger("tk_generic_form")
	logger.setLevel(logging.DEBUG)
	logger.handlers.clear()

	def normalize_type(raw_type):
		return (raw_type or "textbox").strip().lower()

	def collect_values():
		values = {}
		for key, meta in state.items():
			if meta["kind"] == "var":
				values[key] = meta["value"].get()
			else:
				values[key] = meta["value"].get("1.0", "end-1c")
		return values

	def _set_value(meta, value):
		if meta["kind"] == "var":
			meta["value"].set(value)
		else:
			meta["value"].delete("1.0", tk.END)
			if value:
				meta["value"].insert("1.0", str(value))

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

	for row_idx, field in enumerate(fields):
		field_type = normalize_type(field.get("type", "textbox"))
		name = field.get("name")

		if field_type not in {"button", "action"} and not name:
			raise ValueError("Every non-button field must include a non-empty 'name'.")

		if field_type in {"button", "action"}:
			label_text = field.get("label", "")
		else:
			label_text = field.get("label", name)

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
				command=lambda w=widget, v=var, f=date_format: _open_date_picker(root, w, v, f, logger),
			).pack(side="left", padx=(6, 0))
			widget.bind(
				"<Button-1>",
				lambda _e, w=widget, v=var, f=date_format: _open_date_picker(root, w, v, f, logger),
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
				command=lambda w=widget, v=var, f=time_format: _open_time_picker(root, w, v, f, logger),
			).pack(side="left", padx=(6, 0))
			widget.bind(
				"<Button-1>",
				lambda _e, w=widget, v=var, f=time_format: _open_time_picker(root, w, v, f, logger),
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

		else:
			raise ValueError(
				f"Unsupported field type '{field_type}' for field '{name}'."
			)

	form_frame.columnconfigure(1, weight=1)

	ttk.Separator(container, orient="horizontal").pack(fill="x", pady=8)

	ttk.Label(container, text="Logs").pack(anchor="w")
	log_text = tk.Text(container, height=8, state=tk.DISABLED, wrap="word")
	log_text.pack(fill=tk.BOTH, expand=True, pady=(4, 8))
	log_text.tag_configure("DEBUG", foreground="#4a4a4a")
	log_text.tag_configure("INFO", foreground="#1f6f3a")
	log_text.tag_configure("WARNING", foreground="#a66a00")
	log_text.tag_configure("ERROR", foreground="#b00020")
	log_text.tag_configure("CRITICAL", foreground="#b00020")

	text_handler = ReadOnlyTextHandler(log_text)
	text_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
	logger.addHandler(text_handler)

	button_row = ttk.Frame(container)
	button_row.pack(fill="x")

	def save():
		nonlocal result
		values = collect_values()
		result = values
		if on_save:
			on_save(values)
		root.quit()
		root.destroy()

	def on_close():
		logger.warning("Window closed without saving.")
		root.quit()
		root.destroy()

	ttk.Button(button_row, text="Save", command=save).pack(side="right")

	root.protocol("WM_DELETE_WINDOW", on_close)
	root.mainloop()
	return result


if __name__ == "__main__":
	def preview_values(parent: FormParentContext, values: dict):
		print("Current values:", values)
		parent.reset_fields(["notes", "start_time"])
		parent.log_info("Fields 'notes' and 'start_time' have been reset to default.")
		parent.log_error("This is an example error log entry.")
		parent.log_debug(values)
		parent.log_warning("This is a warning message. Remember to check your inputs!")
		parent.set_value("username", "JohnDoe")
	

	sample_fields = [
		{"name": "username", "label": "User Name", "type": "textbox"},
		{"name": "age", "label": "Age", "type": "numeric", "default": 25, "min": 0, "max": 130},
		{
			"name": "role",
			"label": "Role",
			"type": "dropdown",
			"options": ["Admin", "Editor", "Viewer"],
			"default": "Editor",
		},
		{"name": "newsletter", "label": "Newsletter", "type": "checkbox", "default": True},
		{
			"name": "priority",
			"label": "Priority",
			"type": "radio",
			"options": ["Low", "Medium", "High"],
			"default": "Medium",
		},
		{"name": "start_date", "label": "Start Date", "type": "date"},
		{"name": "start_time", "label": "Start Time", "type": "time"},
		{"name": "notes", "label": "Notes", "type": "textarea", "height": 5},
		{"type": "button", "label": "Preview", "on_click": preview_values},
	]

	submitted = create_form_window(sample_fields, title="Dynamic Tk Form")
	print("Submitted values:", submitted)
