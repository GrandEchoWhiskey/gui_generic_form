import inspect
import os
import logging
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import textwrap
import calendar
from datetime import date, datetime
from dataclasses import dataclass
from typing import Optional

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD  # pyright: ignore[reportMissingImports]
except ImportError:
    DND_FILES = None
    TkinterDnD = None


@dataclass
class TextField:
    label: str
    default: str = ""
    read_only: bool = False
    on_changed: Optional[str] = None


@dataclass
class PasswordField:
    label: str
    default: str = ""
    show_char: str = "*"
    can_show: bool = False
    on_changed: Optional[str] = None


@dataclass
class TextArea:
    label: str
    default: str = ""
    read_only: bool = False
    on_changed: Optional[str] = None


@dataclass
class Button:
    label: str
    on_click: str


@dataclass
class CheckBox:
    label: str
    default: bool = False
    on_changed: Optional[str] = None


@dataclass
class Radio:
    label: str
    default: bool = False


@dataclass
class CheckBoxGroup:
    label: str
    options: list[CheckBox]
    on_changed: Optional[str] = None


@dataclass
class RadioGroup:
    label: str
    options: list[Radio]
    on_changed: Optional[str] = None

    def __post_init__(self):
        defaults_count = sum(1 for opt in self.options if opt.default)
        if defaults_count == 0:
            raise ValueError(f"RadioGroup '{self.label}': exactly one option must have default=True, found 0")
        if defaults_count > 1:
            raise ValueError(f"RadioGroup '{self.label}': exactly one option must have default=True, found {defaults_count}")


@dataclass
class Select:
    label: str
    options: list[str]
    default: str = ""
    on_changed: Optional[str] = None

    def __post_init__(self):
        if not self.options:
            raise ValueError(f"Select '{self.label}': options cannot be empty")
        self.options = [str(item) for item in self.options]
        if self.default and self.default not in self.options:
            raise ValueError(f"Select '{self.label}': default '{self.default}' is not in options")


@dataclass
class MultiSelect:
    label: str
    options: list[str]
    default: Optional[list[str]] = None
    sep: str = ", "
    on_changed: Optional[str] = None

    def __post_init__(self):
        if not self.options:
            raise ValueError(f"MultiSelect '{self.label}': options cannot be empty")
        self.options = [str(item) for item in self.options]
        if self.default is None:
            self.default = []
        for item in self.default:
            if item not in self.options:
                raise ValueError(f"MultiSelect '{self.label}': default item '{item}' is not in options")
        if not self.sep:
            self.sep = ", "


@dataclass
class NumberField:
    label: str
    default: float | int | str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: float = 1.0
    integer: bool = False
    read_only: bool = False
    on_changed: Optional[str] = None

    def __post_init__(self):
        if self.step <= 0:
            raise ValueError(f"NumberField '{self.label}': step must be greater than 0")
        if self.min_value is not None and self.max_value is not None and self.min_value > self.max_value:
            raise ValueError(f"NumberField '{self.label}': min_value cannot be greater than max_value")


@dataclass
class FilePath:
    label: str
    default: str = ""
    extensions: dict | list = None
    on_changed: Optional[str] = None

    def __post_init__(self):
        if self.extensions is None:
            self.extensions = ["*.*"]


@dataclass
class DirectoryPath:
    label: str
    default: str = ""
    on_changed: Optional[str] = None


@dataclass
class DatePicker:
    label: str
    default: str = ""
    date_format: str = "%Y-%m-%d"
    on_changed: Optional[str] = None

    def __post_init__(self):
        try:
            sample = date.today().strftime(self.date_format)
            datetime.strptime(sample, self.date_format)
        except ValueError as exc:
            raise ValueError(f"DatePicker '{self.label}': invalid date_format '{self.date_format}'") from exc

        if self.default:
            try:
                datetime.strptime(self.default, self.date_format)
            except ValueError as exc:
                raise ValueError(
                    f"DatePicker '{self.label}': default '{self.default}' does not match date_format '{self.date_format}'"
                ) from exc


@dataclass
class TimePicker:
    label: str
    default: str = ""
    time_format: str = "%H:%M:%S"
    on_changed: Optional[str] = None

    def __post_init__(self):
        try:
            sample = datetime.now().strftime(self.time_format)
            datetime.strptime(sample, self.time_format)
        except ValueError as exc:
            raise ValueError(f"TimePicker '{self.label}': invalid time_format '{self.time_format}'") from exc

        if self.default:
            try:
                datetime.strptime(self.default, self.time_format)
            except ValueError as exc:
                raise ValueError(
                    f"TimePicker '{self.label}': default '{self.default}' does not match time_format '{self.time_format}'"
                ) from exc


def _tokenize_format(format_text: str, supported_directives: set[str]):
    parts: list[tuple[str, str]] = []
    buffer = ""
    index = 0
    while index < len(format_text):
        ch = format_text[index]
        if ch == "%" and index + 1 < len(format_text):
            directive = format_text[index:index + 2]
            if directive == "%%":
                buffer += "%"
                index += 2
                continue
            if directive in supported_directives:
                if buffer:
                    parts.append(("sep", buffer))
                    buffer = ""
                parts.append(("dir", directive))
                index += 2
                continue
        buffer += ch
        index += 1

    if buffer:
        parts.append(("sep", buffer))

    return parts


class _ChangeAwareBoundField:
    def __init__(self):
        self._on_changed_callback = None

    def set_on_changed(self, callback):
        self._on_changed_callback = callback

    def _notify_changed(self):
        if callable(self._on_changed_callback):
            self._on_changed_callback()


class _BoundTextField(_ChangeAwareBoundField):
    def __init__(self, widget: tk.Entry, default: str = "", read_only: bool = False):
        super().__init__()
        self._widget = widget
        self._read_only = bool(read_only)
        if default:
            self._set_widget_text(default)
        if self._read_only:
            self._widget.configure(state="readonly")
        self._last_value = self.value
        self._widget.bind("<KeyRelease>", self._on_widget_changed)
        self._widget.bind("<FocusOut>", self._on_widget_changed)

    @property
    def value(self) -> str:
        return self._widget.get()

    @value.setter
    def value(self, new_value: Optional[str]):
        old_value = self.value
        self._set_widget_text("" if new_value is None else str(new_value))
        new_text = self.value
        self._last_value = new_text
        if new_text != old_value:
            self._notify_changed()

    def get_value(self) -> str:
        return self.value

    def _on_widget_changed(self, _event):
        current = self.value
        if current != self._last_value:
            self._last_value = current
            self._notify_changed()

    def _set_widget_text(self, text: str):
        if self._read_only:
            self._widget.configure(state="normal")
            self._widget.delete(0, tk.END)
            self._widget.insert(0, text)
            self._widget.configure(state="readonly")
            return
        self._widget.delete(0, tk.END)
        self._widget.insert(0, text)


class _BoundPasswordField(_ChangeAwareBoundField):
    def __init__(
        self,
        entry_widget: tk.Entry,
        toggle_button: Optional[tk.Button],
        show_char: str = "*",
        default: str = "",
        can_show: bool = True,
    ):
        super().__init__()
        self._entry = entry_widget
        self._toggle = toggle_button
        self._show_char = show_char if show_char else "*"
        self._can_show = bool(can_show)
        self._is_visible = False

        self._entry.configure(show=self._show_char)
        if self._can_show and self._toggle is not None:
            self._toggle.configure(command=self.toggle_visibility)
        if default:
            self._entry.insert(0, default)
        self._last_value = self.value
        self._entry.bind("<KeyRelease>", self._on_widget_changed)
        self._entry.bind("<FocusOut>", self._on_widget_changed)

    @property
    def value(self) -> str:
        return self._entry.get()

    @value.setter
    def value(self, new_value: Optional[str]):
        old_value = self.value
        self._entry.delete(0, tk.END)
        self._entry.insert(0, "" if new_value is None else str(new_value))
        new_text = self.value
        self._last_value = new_text
        if new_text != old_value:
            self._notify_changed()

    def toggle_visibility(self):
        if not self._can_show or self._toggle is None:
            return
        self._is_visible = not self._is_visible
        if self._is_visible:
            self._entry.configure(show="")
            self._toggle.configure(text="Hide")
        else:
            self._entry.configure(show=self._show_char)
            self._toggle.configure(text="Show")

    def _on_widget_changed(self, _event):
        current = self.value
        if current != self._last_value:
            self._last_value = current
            self._notify_changed()


class _BoundSelect(_ChangeAwareBoundField):
    def __init__(self, variable: tk.StringVar, options: list[str], default: str = ""):
        super().__init__()
        self._variable = variable
        self._options = options
        initial = default if default else options[0]
        self._variable.set(initial)
        self._last_value = self._variable.get()
        self._suspend_trace = False
        self._variable.trace_add("write", self._on_variable_changed)

    @property
    def value(self) -> str:
        return self._variable.get()

    @value.setter
    def value(self, new_value: Optional[str]):
        candidate = "" if new_value is None else str(new_value)
        if candidate not in self._options:
            return
        if candidate == self.value:
            return
        self._suspend_trace = True
        self._variable.set(candidate)
        self._suspend_trace = False
        self._last_value = candidate
        self._notify_changed()

    def _on_variable_changed(self, *_args):
        if self._suspend_trace:
            return
        current = self.value
        if current != self._last_value:
            self._last_value = current
            self._notify_changed()


class _BoundMultiSelect(_ChangeAwareBoundField):
    def __init__(
        self,
        widget: tk.Listbox,
        dropdown_frame: tk.Frame,
        summary_var: tk.StringVar,
        toggle_button: tk.Button,
        options: list[str],
        default: list[str],
        sep: str,
    ):
        super().__init__()
        self._widget = widget
        self._dropdown_frame = dropdown_frame
        self._summary_var = summary_var
        self._toggle_button = toggle_button
        self._options = options
        self._sep = sep
        self._expanded = False

        for option in options:
            self._widget.insert(tk.END, option)

        default_set = set(default)
        for index, option in enumerate(options):
            if option in default_set:
                self._widget.selection_set(index)

        self._widget.bind("<<ListboxSelect>>", self._on_listbox_select)
        self._toggle_button.configure(command=self.toggle_dropdown)
        self._refresh_summary()
        self._last_value = self.value

    @property
    def value(self) -> list[str]:
        return [self._options[index] for index in self._widget.curselection()]

    @value.setter
    def value(self, new_value):
        old_value = self.value
        self._widget.selection_clear(0, tk.END)
        if not isinstance(new_value, list):
            return
        selected = {str(item) for item in new_value}
        for index, option in enumerate(self._options):
            if option in selected:
                self._widget.selection_set(index)
        self._refresh_summary()
        current = self.value
        self._last_value = current
        if current != old_value:
            self._notify_changed()

    def toggle_dropdown(self):
        if self._expanded:
            self._dropdown_frame.pack_forget()
            self._expanded = False
            self._toggle_button.configure(text="▼")
            self._refresh_summary()
            return

        self._dropdown_frame.pack(fill=tk.BOTH, pady=(6, 0))
        self._expanded = True
        self._toggle_button.configure(text="▲")

    def _on_listbox_select(self, _event):
        self._refresh_summary()
        current = self.value
        if current != self._last_value:
            self._last_value = current
            self._notify_changed()

    def _refresh_summary(self):
        selected = self.value
        self._summary_var.set(self._sep.join(selected))


class _BoundNumberField(_ChangeAwareBoundField):
    def __init__(self, widget: tk.Spinbox, spec: NumberField):
        super().__init__()
        self._widget = widget
        self._spec = spec
        self._read_only = bool(spec.read_only)
        self._widget.configure(command=self._on_widget_changed)
        self._widget.bind("<KeyRelease>", self._on_widget_changed)
        self._widget.bind("<FocusOut>", self._on_widget_changed)
        if spec.default != "":
            self.value = spec.default
        if self._read_only:
            self._widget.configure(state="readonly")
        self._last_value = self.value

    @property
    def value(self):
        text = self._widget.get().strip()
        if text == "":
            return 0 if self._spec.integer else 0.0
        try:
            raw = float(text)
        except ValueError:
            raw = 0.0

        if self._spec.min_value is not None:
            raw = max(raw, float(self._spec.min_value))
        if self._spec.max_value is not None:
            raw = min(raw, float(self._spec.max_value))

        if self._spec.integer:
            return int(round(raw))
        return raw

    @value.setter
    def value(self, new_value):
        old_value = self.value
        try:
            raw = float(new_value)
        except (TypeError, ValueError):
            raw = 0.0

        if self._spec.min_value is not None:
            raw = max(raw, float(self._spec.min_value))
        if self._spec.max_value is not None:
            raw = min(raw, float(self._spec.max_value))

        if self._spec.integer:
            display = str(int(round(raw)))
        else:
            display = str(raw)

        self._set_widget_text(display)
        current = self.value
        self._last_value = current
        if current != old_value:
            self._notify_changed()

    def _on_widget_changed(self, _event=None):
        current = self.value
        if current != self._last_value:
            self._last_value = current
            self._notify_changed()

    def _set_widget_text(self, text: str):
        if self._read_only:
            self._widget.configure(state="normal")
            self._widget.delete(0, tk.END)
            self._widget.insert(0, text)
            self._widget.configure(state="readonly")
            return
        self._widget.delete(0, tk.END)
        self._widget.insert(0, text)


class _FormLogHandler(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.INFO)
        self._widget = None
        self._buffer: list[tuple[str, Optional[int]]] = []
        self.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s", "%H:%M:%S"))

    def set_widget(self, widget: tk.Text):
        self._widget = widget
        if not self._buffer:
            return

        pending = self._buffer[:]
        self._buffer.clear()
        for line, levelno in pending:
            self._append_line(line, levelno)

    def emit(self, record: logging.LogRecord):
        try:
            if record.levelno < self.level:
                return
            message = self.format(record)
            self._append_line(message, record.levelno)
        except Exception:
            self.handleError(record)

    def _append_line(self, message: str, levelno: Optional[int] = None):
        if self._widget is None:
            self._buffer.append((message, levelno))
            return

        self._widget.after(0, self._write_to_widget, message, levelno)

    def _write_to_widget(self, message: str, levelno: Optional[int] = None):
        if self._widget is None:
            self._buffer.append((message, levelno))
            return

        tag = self._tag_for_level(levelno)
        self._widget.configure(state=tk.NORMAL)
        if tag:
            self._widget.insert(tk.END, message + "\n", tag)
        else:
            self._widget.insert(tk.END, message + "\n")
        self._widget.configure(state=tk.DISABLED)
        self._widget.see(tk.END)

    def _tag_for_level(self, levelno: Optional[int]) -> Optional[str]:
        if levelno is None:
            return None
        if levelno >= logging.ERROR:
            return "log_error"
        if levelno >= logging.WARNING:
            return "log_warning"
        if levelno >= logging.INFO:
            return "log_info"
        return "log_debug"


class _BoundTextArea(_ChangeAwareBoundField):
    def __init__(self, widget: tk.Text, default: str = "", read_only: bool = False):
        super().__init__()
        self._widget = widget
        self._read_only = bool(read_only)
        if default:
            self._set_widget_text(default)
        if self._read_only:
            self._widget.configure(state=tk.DISABLED)
        self._last_value = self.value
        self._widget.bind("<KeyRelease>", self._on_widget_changed)
        self._widget.bind("<FocusOut>", self._on_widget_changed)

    @property
    def value(self) -> str:
        return self._widget.get("1.0", tk.END).rstrip("\n")

    @value.setter
    def value(self, new_value: Optional[str]):
        old_value = self.value
        self._set_widget_text("" if new_value is None else str(new_value))
        current = self.value
        self._last_value = current
        if current != old_value:
            self._notify_changed()

    def get_value(self) -> str:
        return self.value

    def _on_widget_changed(self, _event):
        current = self.value
        if current != self._last_value:
            self._last_value = current
            self._notify_changed()

    def _set_widget_text(self, text: str):
        if self._read_only:
            self._widget.configure(state=tk.NORMAL)
            self._widget.delete("1.0", tk.END)
            self._widget.insert("1.0", text)
            self._widget.configure(state=tk.DISABLED)
            return
        self._widget.delete("1.0", tk.END)
        self._widget.insert("1.0", text)


class _BoundCheckBox(_ChangeAwareBoundField):
    def __init__(self, variable: tk.BooleanVar, default: bool = False):
        super().__init__()
        self._variable = variable
        self._suspend_trace = False
        self._last_value = bool(self._variable.get())
        if self._last_value != bool(default):
            self._variable.set(bool(default))
            self._last_value = bool(default)
        self._variable.trace_add("write", self._on_variable_changed)

    @property
    def value(self) -> bool:
        return bool(self._variable.get())

    @value.setter
    def value(self, new_value):
        normalized = bool(new_value)
        if normalized == self.value:
            return
        self._suspend_trace = True
        self._variable.set(normalized)
        self._suspend_trace = False
        self._last_value = normalized
        self._notify_changed()

    def get_value(self) -> bool:
        return self.value

    def _on_variable_changed(self, *_args):
        if self._suspend_trace:
            return
        if not hasattr(self, "_last_value"):
            self._last_value = self.value
            return
        current = self.value
        if current != self._last_value:
            self._last_value = current
            self._notify_changed()


class _BoundCheckBoxGroup(_ChangeAwareBoundField):
    def __init__(self, variables: dict[str, tk.BooleanVar]):
        super().__init__()
        self._variables = variables
        self._suspend_trace = False
        for variable in self._variables.values():
            variable.trace_add("write", self._on_variable_changed)
        self._last_value = self.value

    @property
    def value(self) -> dict[str, bool]:
        return {label: bool(var.get()) for label, var in self._variables.items()}

    @value.setter
    def value(self, new_value: dict[str, bool]):
        if not isinstance(new_value, dict):
            return
        changed = False
        self._suspend_trace = True
        for label, var in self._variables.items():
            if label in new_value:
                candidate = bool(new_value[label])
                if bool(var.get()) != candidate:
                    var.set(candidate)
                    changed = True
        self._suspend_trace = False
        if changed:
            self._last_value = self.value
            self._notify_changed()

    def get_value(self) -> dict[str, bool]:
        return self.value

    def _on_variable_changed(self, *_args):
        if self._suspend_trace:
            return
        current = self.value
        if current != self._last_value:
            self._last_value = current
            self._notify_changed()


class _BoundRadioGroup(_ChangeAwareBoundField):
    def __init__(self, variable: tk.StringVar):
        super().__init__()
        self._variable = variable
        self._suspend_trace = False
        self._variable.trace_add("write", self._on_variable_changed)
        self._last_value = self.value

    @property
    def value(self) -> str:
        return self._variable.get()

    @value.setter
    def value(self, new_value: str):
        normalized = str(new_value) if new_value is not None else ""
        if normalized == self.value:
            return
        self._suspend_trace = True
        self._variable.set(normalized)
        self._suspend_trace = False
        self._last_value = normalized
        self._notify_changed()

    def get_value(self) -> str:
        return self.value

    def _on_variable_changed(self, *_args):
        if self._suspend_trace:
            return
        current = self.value
        if current != self._last_value:
            self._last_value = current
            self._notify_changed()


class _BoundFilePath(_ChangeAwareBoundField):
    def __init__(self, widget: tk.Entry, default: str = ""):
        super().__init__()
        self._widget = widget
        if default:
            self._widget.insert(0, default)
        self._last_value = self.value
        self._widget.bind("<KeyRelease>", self._on_widget_changed)
        self._widget.bind("<FocusOut>", self._on_widget_changed)

    @property
    def value(self) -> str:
        return self._widget.get()

    @value.setter
    def value(self, new_value: Optional[str]):
        old_value = self.value
        self._widget.delete(0, tk.END)
        self._widget.insert(0, "" if new_value is None else str(new_value))
        current = self.value
        self._last_value = current
        if current != old_value:
            self._notify_changed()

    def get_value(self) -> str:
        return self.value

    def _on_widget_changed(self, _event):
        current = self.value
        if current != self._last_value:
            self._last_value = current
            self._notify_changed()


class _BoundDirectoryPath(_ChangeAwareBoundField):
    def __init__(self, widget: tk.Entry, default: str = ""):
        super().__init__()
        self._widget = widget
        if default:
            self._widget.insert(0, default)
        self._last_value = self.value
        self._widget.bind("<KeyRelease>", self._on_widget_changed)
        self._widget.bind("<FocusOut>", self._on_widget_changed)

    @property
    def value(self) -> str:
        return self._widget.get()

    @value.setter
    def value(self, new_value: Optional[str]):
        old_value = self.value
        self._widget.delete(0, tk.END)
        self._widget.insert(0, "" if new_value is None else str(new_value))
        current = self.value
        self._last_value = current
        if current != old_value:
            self._notify_changed()

    def _on_widget_changed(self, _event):
        current = self.value
        if current != self._last_value:
            self._last_value = current
            self._notify_changed()


class _BoundDatePicker(_ChangeAwareBoundField):
    def __init__(
        self,
        segmented_frame: tk.Frame,
        part_widgets: dict[str, tk.Spinbox],
        text_entry: tk.Entry,
        toggle_button: tk.Button,
        date_format: str = "%Y-%m-%d",
        default: str = "",
    ):
        super().__init__()
        self._segmented_frame = segmented_frame
        self._parts = part_widgets
        self._text_entry = text_entry
        self._toggle_button = toggle_button
        self._date_format = date_format
        self._text_mode = False
        self._last_valid_value = self._format_date(date.today())
        self._text_entry.bind("<FocusOut>", self._on_text_focus_out)

        initial = default if default else ""
        self.value = initial
        self._show_text_mode()
        self._last_value = self.value

        for widget in self._parts.values():
            widget.bind("<FocusOut>", self._on_widget_changed)
            widget.bind("<KeyRelease>", self._on_widget_changed)

    def on_split_change(self):
        self._sync_day_limit()
        self._notify_if_changed()

    @property
    def value(self) -> str:
        if self._text_mode:
            parsed = self._normalize_date(self._text_entry.get())
            if parsed is not None:
                self._last_valid_value = parsed
                return parsed
            return self._resolve_invalid_text_value("date")
        return self._get_split_date()

    @value.setter
    def value(self, new_value: Optional[str]):
        old_value = self.value
        normalized = self._normalize_date(new_value)
        if normalized is None:
            fallback = self._last_valid_value
            self._set_split_date(fallback)
            self._set_text_date("" if new_value is None else str(new_value))
            if not new_value:
                self._set_text_date(self._date_format)
            self._last_value = self.value
            if self._last_value != old_value:
                self._notify_changed()
            return

        self._last_valid_value = normalized
        self._set_split_date(normalized)
        self._set_text_date(normalized)
        self._last_value = self.value
        if self._last_value != old_value:
            self._notify_changed()

    def toggle_input_mode(self):
        if self._text_mode:
            parsed = self._normalize_date(self._text_entry.get())
            if parsed is None:
                parsed = self._resolve_invalid_text_value("date")
                if parsed is None:
                    return
            self._last_valid_value = parsed
            self._set_split_date(parsed)
            self._show_split_mode()
            return

        self._set_text_date(self._get_split_date())
        self._show_text_mode()

    def set_date(self, new_value: str):
        self.value = new_value

    def set_today(self):
        self.value = self._format_date(date.today())

    def _show_text_mode(self):
        self._text_mode = True
        self._segmented_frame.pack_forget()
        self._text_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, before=self._toggle_button)
        self._toggle_button.configure(text="Split")

    def _show_split_mode(self):
        self._text_mode = False
        self._text_entry.pack_forget()
        self._segmented_frame.pack(side=tk.LEFT, before=self._toggle_button)
        self._toggle_button.configure(text="Text")

    def _set_text_date(self, value: str):
        self._text_entry.delete(0, tk.END)
        self._text_entry.insert(0, value)

    def _set_split_date(self, value: str):
        parsed = self._parse_date(value)
        if parsed is None:
            parsed = date.today()

        if "%Y" in self._parts:
            self._parts["%Y"].delete(0, tk.END)
            self._parts["%Y"].insert(0, f"{parsed.year:04d}")
        if "%m" in self._parts:
            self._parts["%m"].delete(0, tk.END)
            self._parts["%m"].insert(0, f"{parsed.month:02d}")
        if "%d" in self._parts:
            self._parts["%d"].delete(0, tk.END)
            self._parts["%d"].insert(0, f"{parsed.day:02d}")
        self._sync_day_limit()

    def _get_split_date(self) -> str:
        today = date.today()
        year = self._clean_int(self._parts["%Y"].get(), 1, 9999) if "%Y" in self._parts else today.year
        month = self._clean_int(self._parts["%m"].get(), 1, 12) if "%m" in self._parts else today.month
        max_day = calendar.monthrange(year, month)[1]
        if "%d" in self._parts:
            day_value = self._clean_int(self._parts["%d"].get(), 1, max_day)
        else:
            day_value = min(today.day, max_day)
        return self._format_date(date(year, month, day_value))

    def _sync_day_limit(self):
        if "%d" not in self._parts:
            return

        today = date.today()
        year = self._clean_int(self._parts["%Y"].get(), 1, 9999) if "%Y" in self._parts else today.year
        month = self._clean_int(self._parts["%m"].get(), 1, 12) if "%m" in self._parts else today.month
        max_day = calendar.monthrange(year, month)[1]
        day_widget = self._parts["%d"]
        day_widget.configure(to=max_day)

        day_value = self._clean_int(day_widget.get(), 1, max_day)
        day_widget.delete(0, tk.END)
        day_widget.insert(0, f"{day_value:02d}")

    def _normalize_date(self, value: Optional[str]):
        parsed = self._parse_date(value)
        if parsed is None:
            return None
        return self._format_date(parsed)

    def _parse_date(self, value: Optional[str]):
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        try:
            return datetime.strptime(text, self._date_format).date()
        except ValueError:
            return None

    def _format_date(self, value: date) -> str:
        return value.strftime(self._date_format)

    def _resolve_invalid_text_value(self, field_name: str):
        keep_previous = not messagebox.askretrycancel(
            f"Invalid {field_name}",
            f"The entered {field_name} is invalid.\n\n"
            f"Choose Retry to edit it, or Cancel to keep previous value ({self._last_valid_value}).",
            parent=self._text_entry.winfo_toplevel(),
        )
        if keep_previous:
            self._set_text_date(self._last_valid_value)
            return self._last_valid_value

        self._text_entry.focus_set()
        self._text_entry.selection_range(0, tk.END)
        return None

    def _on_text_focus_out(self, _event):
        if not self._text_mode:
            return
        text = self._text_entry.get().strip()
        if not text:
            return
        parsed = self._normalize_date(text)
        if parsed is not None:
            self._last_valid_value = parsed
            self._set_text_date(parsed)
            self._notify_if_changed()
            return
        self._resolve_invalid_text_value("date")

    def _clean_int(self, value: str, min_value: int, max_value: int) -> int:
        try:
            number = int(str(value).strip())
        except ValueError:
            number = min_value
        if number < min_value:
            number = min_value
        if number > max_value:
            number = max_value
        return number

    def _on_widget_changed(self, _event):
        self._notify_if_changed()

    def _notify_if_changed(self):
        current = self.value
        if current != self._last_value:
            self._last_value = current
            self._notify_changed()


class _BoundTimePicker(_ChangeAwareBoundField):
    def __init__(
        self,
        segmented_frame: tk.Frame,
        part_widgets: dict[str, tk.Spinbox],
        text_entry: tk.Entry,
        toggle_button: tk.Button,
        time_format: str = "%H:%M:%S",
        default: str = "",
    ):
        super().__init__()
        self._segmented_frame = segmented_frame
        self._parts = part_widgets
        self._text_entry = text_entry
        self._toggle_button = toggle_button
        self._time_format = time_format
        self._text_mode = False
        self._last_valid_value = self._format_time(datetime.now().time())
        self._text_entry.bind("<FocusOut>", self._on_text_focus_out)

        initial = default if default else self._last_valid_value
        self._set_segmented_time(initial)
        self._set_text_time(initial)
        normalized_initial = self._normalize_time(initial)
        if normalized_initial is not None:
            self._last_valid_value = normalized_initial
        self._show_text_mode()
        self._last_value = self.value

        for widget in self._parts.values():
            widget.bind("<FocusOut>", self._on_widget_changed)
            widget.bind("<KeyRelease>", self._on_widget_changed)

    @property
    def value(self) -> str:
        if self._text_mode:
            text_value = self._normalize_time(self._text_entry.get())
            if text_value is None:
                restored = self._resolve_invalid_text_value("time")
                if restored is None:
                    return self._last_valid_value
                return restored
            self._last_valid_value = text_value
            return text_value
        return self._get_segmented_time()

    @value.setter
    def value(self, new_value: Optional[str]):
        old_value = self.value
        normalized = self._normalize_time(new_value)
        if normalized is None:
            normalized = self._last_valid_value
        self._last_valid_value = normalized
        self._set_segmented_time(normalized)
        self._set_text_time(normalized)
        self._last_value = self.value
        if self._last_value != old_value:
            self._notify_changed()

    def toggle_input_mode(self):
        if self._text_mode:
            parsed = self._normalize_time(self._text_entry.get())
            if parsed is None:
                parsed = self._resolve_invalid_text_value("time")
                if parsed is None:
                    return
            self._last_valid_value = parsed
            self._set_segmented_time(parsed)
            self._show_segmented_mode()
            return

        self._set_text_time(self._get_segmented_time())
        self._show_text_mode()

    def set_now(self):
        now_value = self._format_time(datetime.now().time())
        self.value = now_value

    def _show_segmented_mode(self):
        self._text_mode = False
        self._text_entry.pack_forget()
        self._segmented_frame.pack(side=tk.LEFT, before=self._toggle_button)
        self._toggle_button.configure(text="Text")

    def _show_text_mode(self):
        self._text_mode = True
        self._segmented_frame.pack_forget()
        self._text_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, before=self._toggle_button)
        self._toggle_button.configure(text="Split")

    def _get_segmented_time(self) -> str:
        now = datetime.now().time()
        h = int(self._clean_part(self._parts["%H"].get(), 23)) if "%H" in self._parts else now.hour
        m = int(self._clean_part(self._parts["%M"].get(), 59)) if "%M" in self._parts else now.minute
        s = int(self._clean_part(self._parts["%S"].get(), 59)) if "%S" in self._parts else now.second
        return self._format_time(datetime(2000, 1, 1, h, m, s).time())

    def _set_segmented_time(self, value: str):
        parsed = self._parse_time(value)
        if parsed is None:
            parsed = self._parse_time(self._last_valid_value)
        if parsed is None:
            parsed = datetime.now().time()

        if "%H" in self._parts:
            self._parts["%H"].delete(0, tk.END)
            self._parts["%H"].insert(0, f"{parsed.hour:02d}")
        if "%M" in self._parts:
            self._parts["%M"].delete(0, tk.END)
            self._parts["%M"].insert(0, f"{parsed.minute:02d}")
        if "%S" in self._parts:
            self._parts["%S"].delete(0, tk.END)
            self._parts["%S"].insert(0, f"{parsed.second:02d}")

    def _set_text_time(self, value: str):
        self._text_entry.delete(0, tk.END)
        self._text_entry.insert(0, value)

    def _normalize_time(self, value: Optional[str]):
        parsed = self._parse_time(value)
        if parsed is None:
            return None
        return self._format_time(parsed)

    def _parse_time(self, value: Optional[str]):
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        try:
            return datetime.strptime(text, self._time_format).time()
        except ValueError:
            return None

    def _format_time(self, value):
        return datetime.combine(date.today(), value).strftime(self._time_format)

    def _clean_part(self, text: str, max_value: int) -> str:
        try:
            number = int(str(text).strip())
        except ValueError:
            number = 0
        if number < 0:
            number = 0
        if number > max_value:
            number = max_value
        return f"{number:02d}"

    def _resolve_invalid_text_value(self, field_name: str):
        keep_previous = not messagebox.askretrycancel(
            f"Invalid {field_name}",
            f"The entered {field_name} is invalid.\n\n"
            f"Choose Retry to edit it, or Cancel to keep previous value ({self._last_valid_value}).",
            parent=self._text_entry.winfo_toplevel(),
        )
        if keep_previous:
            self._set_text_time(self._last_valid_value)
            return self._last_valid_value

        self._text_entry.focus_set()
        self._text_entry.selection_range(0, tk.END)
        return None

    def _on_text_focus_out(self, _event):
        if not self._text_mode:
            return
        text = self._text_entry.get().strip()
        if not text:
            return
        parsed = self._normalize_time(text)
        if parsed is not None:
            self._last_valid_value = parsed
            self._set_text_time(parsed)
            self._notify_if_changed()
            return
        self._resolve_invalid_text_value("time")

    def get_value(self) -> str:
        return self.value

    def _on_widget_changed(self, _event):
        self._notify_if_changed()

    def _notify_if_changed(self):
        current = self.value
        if current != self._last_value:
            self._last_value = current
            self._notify_changed()


class _CalendarPopup:
    def __init__(self, parent: tk.Tk, initial_value: str, on_select, date_format: str = "%Y-%m-%d"):
        self._parent = parent
        self._on_select = on_select
        self._date_format = date_format
        self._cal = calendar.Calendar(firstweekday=0)

        parsed = self._parse_date(initial_value) or date.today()
        self._year = parsed.year
        self._month = parsed.month

        self._window = tk.Toplevel(parent)
        self._window.title("Select date")
        self._window.transient(parent)
        self._window.resizable(False, False)
        self._window.grab_set()

        header = tk.Frame(self._window, padx=8, pady=8)
        header.pack(fill=tk.X)

        prev_btn = tk.Button(header, text="<", width=3, command=lambda: self._change_month(-1))
        prev_btn.pack(side=tk.LEFT)

        center_controls = tk.Frame(header)
        center_controls.pack(side=tk.LEFT, expand=True)

        self._month_button = tk.Button(center_controls, width=10, command=self._open_month_picker)
        self._month_button.pack(side=tk.LEFT, padx=(0, 6))

        self._year_button = tk.Button(center_controls, width=6, command=self._open_year_picker)
        self._year_button.pack(side=tk.LEFT)

        next_btn = tk.Button(header, text=">", width=3, command=lambda: self._change_month(1))
        next_btn.pack(side=tk.RIGHT)

        self._grid_frame = tk.Frame(self._window, padx=8)
        self._grid_frame.pack(fill=tk.BOTH, pady=(0, 8))

        self._render()
        self._center_on_parent()

    def _parse_date(self, value: str):
        if not value:
            return None
        try:
            return datetime.strptime(value.strip(), self._date_format).date()
        except ValueError:
            return None

    def _change_month(self, delta: int):
        month_index = (self._year * 12 + (self._month - 1)) + delta
        self._year = month_index // 12
        self._month = (month_index % 12) + 1
        self._render()

    def _open_month_picker(self):
        dialog = tk.Toplevel(self._window)
        dialog.title("Select month")
        dialog.transient(self._window)
        dialog.resizable(False, False)
        dialog.grab_set()

        body = tk.Frame(dialog, padx=8, pady=8)
        body.pack(fill=tk.BOTH)

        for index in range(12):
            month_number = index + 1
            tk.Button(
                body,
                text=calendar.month_name[month_number],
                width=10,
                command=lambda m=month_number, d=dialog: self._choose_month(m, d),
            ).grid(row=index // 3, column=index % 3, padx=4, pady=4, sticky="ew")

        self._center_child_window(dialog, self._window)

    def _choose_month(self, month: int, dialog: tk.Toplevel):
        self._month = month
        dialog.destroy()
        self._render()

    def _open_year_picker(self):
        dialog = tk.Toplevel(self._window)
        dialog.title("Select year")
        dialog.transient(self._window)
        dialog.resizable(False, False)
        dialog.grab_set()

        body = tk.Frame(dialog, padx=10, pady=10)
        body.pack(fill=tk.BOTH)

        tk.Label(body, text="Year").grid(row=0, column=0, sticky="w")
        year_entry = tk.Entry(body, width=8)
        year_entry.grid(row=1, column=0, pady=(4, 8), sticky="w")
        year_entry.insert(0, str(self._year))
        year_entry.focus_set()

        button_row = tk.Frame(body)
        button_row.grid(row=2, column=0, sticky="w")

        tk.Button(
            button_row,
            text="Apply",
            width=7,
            command=lambda: self._apply_year_from_entry(year_entry, dialog),
        ).pack(side=tk.LEFT)
        tk.Button(button_row, text="Cancel", width=7, command=dialog.destroy).pack(side=tk.LEFT, padx=(6, 0))

        year_entry.bind("<Return>", lambda _event: self._apply_year_from_entry(year_entry, dialog))

        self._center_child_window(dialog, self._window)

    def _apply_year_from_entry(self, year_entry: tk.Entry, dialog: tk.Toplevel):
        text = year_entry.get().strip()
        if not text:
            return
        try:
            year = int(text)
        except ValueError:
            return
        if year < 1 or year > 9999:
            return

        self._year = year
        dialog.destroy()
        self._render()

    def _render(self):
        self._month_button.configure(text=calendar.month_name[self._month])
        self._year_button.configure(text=str(self._year))

        for child in self._grid_frame.winfo_children():
            child.destroy()

        weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for col, name in enumerate(weekday_names):
            tk.Label(self._grid_frame, text=name, width=4, anchor="center").grid(row=0, column=col, padx=1, pady=1)

        for row_index, week in enumerate(self._cal.monthdayscalendar(self._year, self._month), start=1):
            for col_index, day_number in enumerate(week):
                if day_number == 0:
                    tk.Label(self._grid_frame, text="", width=4).grid(row=row_index, column=col_index, padx=1, pady=1)
                    continue

                tk.Button(
                    self._grid_frame,
                    text=f"{day_number:02d}",
                    width=4,
                    command=lambda d=day_number: self._select_day(d),
                ).grid(row=row_index, column=col_index, padx=1, pady=1)

    def _select_day(self, day_number: int):
        selected = date(self._year, self._month, day_number).strftime(self._date_format)
        self._on_select(selected)
        self._window.destroy()

    def _center_on_parent(self):
        self._center_child_window(self._window, self._parent)

    def _center_child_window(self, child: tk.Toplevel, parent):
        child.update_idletasks()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()

        ww = child.winfo_reqwidth()
        wh = child.winfo_reqheight()

        x = px + max((pw - ww) // 2, 0)
        y = py + max((ph - wh) // 2, 0)
        child.geometry(f"+{x}+{y}")


class Form:
    def __new__(cls, *args, **kwargs):
        # Supports @Form decorator usage as a no-op class decorator.
        if len(args) == 1 and inspect.isclass(args[0]) and issubclass(args[0], Form):
            return args[0]
        return super().__new__(cls)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.__field_specs__ = []
        for name, value in cls.__dict__.items():
            if isinstance(
                value,
                (
                    TextField,
                    PasswordField,
                    TextArea,
                    Button,
                    CheckBox,
                    CheckBoxGroup,
                    RadioGroup,
                    Select,
                    MultiSelect,
                    NumberField,
                    FilePath,
                    DirectoryPath,
                    DatePicker,
                    TimePicker,
                ),
            ):
                cls.__field_specs__.append((name, value))

    def __init__(self, **kwargs):
        default_title = self.__class__.__name__
        default_logging_enabled = True
        default_logging_debug = False

        self.title = kwargs.pop("title", default_title)
        self.logging_enabled = bool(kwargs.pop("logging_enabled", default_logging_enabled))
        self.logging_debug = bool(kwargs.pop("logging_debug", default_logging_debug))

        if kwargs:
            unknown = ", ".join(sorted(kwargs.keys()))
            raise TypeError(f"Unexpected Form constructor arguments: {unknown}")

        self._logging_handler = None
        if self.logging_enabled:
            self._logging_handler = _FormLogHandler()
            if self.logging_debug:
                self._logging_handler.setLevel(logging.DEBUG)
            logging.getLogger().addHandler(self._logging_handler)

        if TkinterDnD is not None:
            self.root = TkinterDnD.Tk()
            self._dnd_enabled = True
        else:
            self.root = tk.Tk()
            self._dnd_enabled = False
        self.root.title(str(self.title))
        self._checkbox_groups = []
        self._radio_groups = []
        self._single_checkbox_widgets = []
        self._layout_update_job = None

        self._container = tk.Frame(self.root)
        self._container.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(self._container, highlightthickness=0)
        self._scrollbar = tk.Scrollbar(self._container, orient=tk.VERTICAL, command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._scrollbar.set)
        self._scrollbar_visible = False

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._frame = tk.Frame(self._canvas, padx=12, pady=12)
        self._frame_window = self._canvas.create_window((0, 0), window=self._frame, anchor="nw")

        self._frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self.root.bind("<Configure>", self._on_root_configure)
        self._bind_mousewheel()

        self._build_declared_fields()
        self._add_logging_area()
        self.root.after_idle(self._initialize_window)

    def _build_declared_fields(self):
        row = 0
        for name, spec in self.__class__.__field_specs__:
            if isinstance(spec, TextField):
                tk.Label(self._frame, text=spec.label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=(0, 8))
                entry = tk.Entry(self._frame, width=60)
                entry.grid(row=row, column=1, sticky="ew", pady=(0, 8))
                bound = _BoundTextField(entry, default=spec.default, read_only=spec.read_only)
                self._bind_on_changed(bound, spec.on_changed)
                setattr(self, name, bound)
                row += 1
            elif isinstance(spec, PasswordField):
                tk.Label(self._frame, text=spec.label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=(0, 8))
                pass_frame = tk.Frame(self._frame)
                pass_frame.grid(row=row, column=1, sticky="ew", pady=(0, 8))

                entry = tk.Entry(pass_frame)
                entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

                toggle_btn = None
                if spec.can_show:
                    toggle_btn = tk.Button(pass_frame, text="Show", width=6)
                    toggle_btn.pack(side=tk.LEFT, padx=(8, 0))

                bound = _BoundPasswordField(
                    entry,
                    toggle_btn,
                    show_char=spec.show_char,
                    default=spec.default,
                    can_show=spec.can_show,
                )
                self._bind_on_changed(bound, spec.on_changed)
                setattr(self, name, bound)
                row += 1
            elif isinstance(spec, TextArea):
                tk.Label(self._frame, text=spec.label).grid(row=row, column=0, sticky="nw", padx=(0, 10), pady=(0, 8))
                text = tk.Text(self._frame, width=60, height=6)
                text.grid(row=row, column=1, sticky="ew", pady=(0, 8))
                bound = _BoundTextArea(text, default=spec.default, read_only=spec.read_only)
                self._bind_on_changed(bound, spec.on_changed)
                setattr(self, name, bound)
                row += 1
            elif isinstance(spec, Select):
                tk.Label(self._frame, text=spec.label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=(0, 8))
                selected = tk.StringVar()
                combo = ttk.Combobox(self._frame, textvariable=selected, values=spec.options, state="readonly")
                combo.grid(row=row, column=1, sticky="ew", pady=(0, 8))
                bound = _BoundSelect(selected, options=spec.options, default=spec.default)
                self._bind_on_changed(bound, spec.on_changed)
                setattr(self, name, bound)
                row += 1
            elif isinstance(spec, MultiSelect):
                tk.Label(self._frame, text=spec.label).grid(row=row, column=0, sticky="nw", padx=(0, 10), pady=(0, 8))

                multi_frame = tk.Frame(self._frame)
                multi_frame.grid(row=row, column=1, sticky="ew", pady=(0, 8))

                top_row = tk.Frame(multi_frame)
                top_row.pack(fill=tk.BOTH)

                summary_var = tk.StringVar()
                summary_entry = tk.Entry(top_row, textvariable=summary_var, state="readonly")
                summary_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

                toggle_btn = tk.Button(top_row, text="▼", width=3)
                toggle_btn.pack(side=tk.LEFT, padx=(6, 0))

                dropdown_frame = tk.Frame(multi_frame)

                visible_rows = max(3, min(8, len(spec.options)))
                listbox = tk.Listbox(dropdown_frame, selectmode=tk.MULTIPLE, exportselection=False, height=visible_rows)
                listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

                scrollbar = tk.Scrollbar(dropdown_frame, orient=tk.VERTICAL, command=listbox.yview)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                listbox.configure(yscrollcommand=scrollbar.set)

                bound = _BoundMultiSelect(
                    listbox,
                    dropdown_frame,
                    summary_var,
                    toggle_btn,
                    options=spec.options,
                    default=spec.default or [],
                    sep=spec.sep,
                )
                self._bind_on_changed(bound, spec.on_changed)
                setattr(self, name, bound)
                row += 1
            elif isinstance(spec, NumberField):
                tk.Label(self._frame, text=spec.label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=(0, 8))

                min_value = spec.min_value if spec.min_value is not None else -1_000_000_000
                max_value = spec.max_value if spec.max_value is not None else 1_000_000_000
                increment = 1 if spec.integer else spec.step

                number_spinbox = tk.Spinbox(
                    self._frame,
                    from_=min_value,
                    to=max_value,
                    increment=increment,
                    width=14,
                )
                number_spinbox.grid(row=row, column=1, sticky="w", pady=(0, 8))

                bound = _BoundNumberField(number_spinbox, spec)
                self._bind_on_changed(bound, spec.on_changed)
                setattr(self, name, bound)
                row += 1
            elif isinstance(spec, Button):
                command = self._make_button_handler(spec.on_click)
                button = tk.Button(self._frame, text=spec.label, command=command)
                button.grid(row=row, column=1, sticky="w", pady=(4, 12))
                row += 1
            elif isinstance(spec, CheckBox):
                variable = tk.BooleanVar(value=spec.default)
                checkbox = tk.Checkbutton(self._frame, text=spec.label, variable=variable)
                checkbox.grid(row=row, column=1, sticky="w", pady=(0, 8))
                self._single_checkbox_widgets.append({"widget": checkbox, "label": spec.label})
                bound = _BoundCheckBox(variable, default=spec.default)
                self._bind_on_changed(bound, spec.on_changed)
                setattr(self, name, bound)
                row += 1
            elif isinstance(spec, CheckBoxGroup):
                tk.Label(self._frame, text=spec.label).grid(row=row, column=0, sticky="nw", padx=(0, 10), pady=(0, 8))

                options_frame = tk.Frame(self._frame)
                options_frame.grid(row=row, column=1, sticky="ew", pady=(0, 8))
                options_frame.grid_propagate(False)

                variables: dict[str, tk.BooleanVar] = {}
                option_widgets = []
                option_labels = []
                for index, option in enumerate(spec.options):
                    var = tk.BooleanVar(value=option.default)
                    checkbox = tk.Checkbutton(options_frame, text=option.label, variable=var)
                    checkbox.place(x=0, y=0)
                    variables[option.label] = var
                    option_widgets.append(checkbox)
                    option_labels.append(option.label)

                self._checkbox_groups.append({"frame": options_frame, "widgets": option_widgets, "labels": option_labels})

                bound = _BoundCheckBoxGroup(variables)
                self._bind_on_changed(bound, spec.on_changed)
                setattr(self, name, bound)
                row += 1
            elif isinstance(spec, RadioGroup):
                tk.Label(self._frame, text=spec.label).grid(row=row, column=0, sticky="nw", padx=(0, 10), pady=(0, 8))

                options_frame = tk.Frame(self._frame)
                options_frame.grid(row=row, column=1, sticky="ew", pady=(0, 8))
                options_frame.grid_propagate(False)

                radio_variable = tk.StringVar()
                default_value = next((opt.label for opt in spec.options if opt.default), None)
                if default_value:
                    radio_variable.set(default_value)

                option_widgets = []
                option_labels = []
                for index, option in enumerate(spec.options):
                    radio = tk.Radiobutton(options_frame, text=option.label, variable=radio_variable, value=option.label)
                    radio.place(x=0, y=0)
                    option_widgets.append(radio)
                    option_labels.append(option.label)

                self._radio_groups.append({"frame": options_frame, "widgets": option_widgets, "labels": option_labels})

                bound = _BoundRadioGroup(radio_variable)
                self._bind_on_changed(bound, spec.on_changed)
                setattr(self, name, bound)
                row += 1
            elif isinstance(spec, FilePath):
                tk.Label(self._frame, text=spec.label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=(0, 8))
                
                path_frame = tk.Frame(self._frame)
                path_frame.grid(row=row, column=1, sticky="ew", pady=(0, 8))
                
                entry = tk.Entry(path_frame)
                entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                if spec.default:
                    entry.insert(0, spec.default)
                
                bound = _BoundFilePath(entry, default=spec.default)
                self._bind_on_changed(bound, spec.on_changed)

                def make_file_handler(bound_field, extensions):
                    def _handler():
                        if isinstance(extensions, dict):
                            filetypes = [(desc, " ".join(exts)) for desc, exts in extensions.items()]
                        else:
                            filetypes = [(f"Files ({ext})", ext) for ext in extensions]
                        filepath = filedialog.askopenfilename(filetypes=filetypes)
                        if filepath:
                            bound_field.value = filepath
                    return _handler
                
                browse_btn = tk.Button(path_frame, text="Browse", command=make_file_handler(bound, spec.extensions))
                browse_btn.pack(side=tk.LEFT, padx=(8, 0))

                self._attach_drop_target(entry, entry, target_type="file", bound_field=bound)
                
                setattr(self, name, bound)
                row += 1
            elif isinstance(spec, DirectoryPath):
                tk.Label(self._frame, text=spec.label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=(0, 8))
                
                path_frame = tk.Frame(self._frame)
                path_frame.grid(row=row, column=1, sticky="ew", pady=(0, 8))
                
                entry = tk.Entry(path_frame)
                entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                if spec.default:
                    entry.insert(0, spec.default)
                
                bound = _BoundDirectoryPath(entry, default=spec.default)
                self._bind_on_changed(bound, spec.on_changed)

                def make_dir_handler(bound_field):
                    def _handler():
                        dirpath = filedialog.askdirectory()
                        if dirpath:
                            bound_field.value = dirpath
                    return _handler
                
                browse_btn = tk.Button(path_frame, text="Browse", command=make_dir_handler(bound))
                browse_btn.pack(side=tk.LEFT, padx=(8, 0))

                self._attach_drop_target(entry, entry, target_type="directory", bound_field=bound)
                
                setattr(self, name, bound)

                row += 1
            elif isinstance(spec, DatePicker):
                tk.Label(self._frame, text=spec.label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=(0, 8))
                effective_date_default = spec.default if spec.default else date.today().strftime(spec.date_format)

                date_frame = tk.Frame(self._frame)
                date_frame.grid(row=row, column=1, sticky="ew", pady=(0, 8))

                segmented_frame = tk.Frame(date_frame)
                segmented_frame.pack(side=tk.LEFT)

                date_widgets: dict[str, tk.Spinbox] = {}
                for part_type, part_value in _tokenize_format(spec.date_format, {"%Y", "%m", "%d"}):
                    if part_type == "sep":
                        if part_value:
                            tk.Label(segmented_frame, text=part_value).pack(side=tk.LEFT, padx=2)
                        continue

                    if part_value == "%Y":
                        widget = tk.Spinbox(segmented_frame, from_=1, to=9999, width=5, format="%04.0f", wrap=True)
                    elif part_value == "%m":
                        widget = tk.Spinbox(segmented_frame, from_=1, to=12, width=3, format="%02.0f", wrap=True)
                    else:
                        widget = tk.Spinbox(segmented_frame, from_=1, to=31, width=3, format="%02.0f", wrap=True)

                    widget.pack(side=tk.LEFT)
                    date_widgets[part_value] = widget

                entry = tk.Entry(date_frame, width=12)

                toggle_btn = tk.Button(date_frame, text="Split")
                toggle_btn.pack(side=tk.LEFT, padx=(8, 0))

                today_btn = tk.Button(date_frame, text="Today")
                today_btn.pack(side=tk.LEFT, padx=(6, 0))

                bound_date = _BoundDatePicker(
                    segmented_frame=segmented_frame,
                    part_widgets=date_widgets,
                    text_entry=entry,
                    toggle_button=toggle_btn,
                    date_format=spec.date_format,
                    default=effective_date_default,
                )

                for widget in date_widgets.values():
                    widget.configure(command=bound_date.on_split_change)

                toggle_btn.configure(command=bound_date.toggle_input_mode)
                today_btn.configure(command=bound_date.set_today)
                self._bind_on_changed(bound_date, spec.on_changed)

                def make_date_handler(date_picker, date_format):
                    def _handler():
                        _CalendarPopup(
                            parent=self.root,
                            initial_value=date_picker.value,
                            on_select=lambda selected: date_picker.set_date(selected),
                            date_format=date_format,
                        )

                    return _handler

                pick_btn = tk.Button(date_frame, text="Pick", command=make_date_handler(bound_date, spec.date_format))
                pick_btn.pack(side=tk.LEFT, padx=(8, 0))
                
                setattr(self, name, bound_date)
                row += 1
            
            elif isinstance(spec, TimePicker):
                tk.Label(self._frame, text=spec.label).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=(0, 8))
                if spec.default:
                    try:
                        datetime.strptime(spec.default, spec.time_format)
                    except ValueError as exc:
                        raise ValueError(
                            f"TimePicker '{spec.label}': default '{spec.default}' does not match time_format '{spec.time_format}'"
                        ) from exc
                effective_time_default = spec.default if spec.default else datetime.now().strftime(spec.time_format)
                
                time_frame = tk.Frame(self._frame)
                time_frame.grid(row=row, column=1, sticky="ew", pady=(0, 8))

                segmented_frame = tk.Frame(time_frame)
                segmented_frame.pack(side=tk.LEFT)

                time_widgets: dict[str, tk.Spinbox] = {}
                for part_type, part_value in _tokenize_format(spec.time_format, {"%H", "%M", "%S"}):
                    if part_type == "sep":
                        if part_value:
                            tk.Label(segmented_frame, text=part_value).pack(side=tk.LEFT, padx=2)
                        continue

                    max_value = 23 if part_value == "%H" else 59
                    widget = tk.Spinbox(segmented_frame, from_=0, to=max_value, width=3, format="%02.0f", wrap=True)
                    widget.pack(side=tk.LEFT)
                    time_widgets[part_value] = widget

                text_entry = tk.Entry(time_frame, width=10)

                toggle_btn = tk.Button(time_frame, text="Text")
                toggle_btn.pack(side=tk.LEFT, padx=(8, 0))

                now_btn = tk.Button(time_frame, text="Now")
                now_btn.pack(side=tk.LEFT, padx=(6, 0))

                bound_time = _BoundTimePicker(
                    segmented_frame=segmented_frame,
                    part_widgets=time_widgets,
                    text_entry=text_entry,
                    toggle_button=toggle_btn,
                    time_format=spec.time_format,
                    default=effective_time_default,
                )
                toggle_btn.configure(command=bound_time.toggle_input_mode)
                now_btn.configure(command=bound_time.set_now)
                self._bind_on_changed(bound_time, spec.on_changed)

                setattr(self, name, bound_time)
                row += 1

        self._frame.grid_columnconfigure(1, weight=1)
        self._next_row = row

    def _make_button_handler(self, method_name: str):
        def _handler():
            callback = getattr(self, method_name, None)
            if callable(callback):
                callback()

        return _handler

    def _bind_on_changed(self, bound_field, method_name: Optional[str]):
        callback = self._make_on_changed_handler(method_name)
        if hasattr(bound_field, "set_on_changed"):
            bound_field.set_on_changed(callback)

    def _make_on_changed_handler(self, method_name: Optional[str]):
        if not method_name:
            return None

        def _handler():
            callback = getattr(self, method_name, None)
            if callable(callback):
                callback()

        return _handler

    def _attach_drop_target(self, widget, entry_widget: tk.Entry, target_type: str, bound_field=None):
        if not self._dnd_enabled or DND_FILES is None:
            return

        widget.drop_target_register(DND_FILES)
        widget.dnd_bind(
            "<<Drop>>",
            lambda event: self._handle_drop_event(event, entry_widget, target_type, bound_field=bound_field),
        )

    def _handle_drop_event(self, event, entry_widget: tk.Entry, target_type: str, bound_field=None):
        paths = self._parse_drop_paths(event.data)
        if not paths:
            return

        selected_path = ""
        if target_type == "file":
            for item in paths:
                if os.path.isfile(item):
                    selected_path = item
                    break
        elif target_type == "directory":
            for item in paths:
                if os.path.isdir(item):
                    selected_path = item
                    break
            if not selected_path:
                for item in paths:
                    if os.path.isfile(item):
                        selected_path = os.path.dirname(item)
                        break

        if not selected_path:
            return

        if bound_field is not None and hasattr(bound_field, "value"):
            bound_field.value = selected_path
            return

        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, selected_path)

    def _parse_drop_paths(self, drop_data: str) -> list[str]:
        if not drop_data:
            return []

        try:
            items = list(self.root.tk.splitlist(drop_data))
        except tk.TclError:
            items = [drop_data]

        cleaned: list[str] = []
        for item in items:
            value = item.strip()
            if value.startswith("{") and value.endswith("}"):
                value = value[1:-1]
            if value:
                cleaned.append(value)
        return cleaned

    def _add_logging_area(self):
        # Automatically generated log area placeholder for future logger integration.
        logging_enabled = bool(getattr(self, "logging_enabled", True))
        if not logging_enabled:
            self.log_text_area = None
            return

        row = getattr(self, "_next_row", 0)
        log_widget = tk.Text(self._frame, width=60, height=8)
        log_widget.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        log_widget.tag_configure("log_debug", foreground="#6e7781")
        log_widget.tag_configure("log_info", foreground="#1f6feb")
        log_widget.tag_configure("log_warning", foreground="#9a6700")
        log_widget.tag_configure("log_error", foreground="#cf222e")
        log_widget.configure(state=tk.DISABLED)

        self.log_text_area = _BoundTextArea(log_widget)
        if self._logging_handler is not None:
            self._logging_handler.set_widget(log_widget)

    def _on_frame_configure(self, _event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._update_scroll_state()

    def _on_canvas_configure(self, event):
        self._canvas.itemconfigure(self._frame_window, width=event.width)
        self._schedule_layout_update()

    def _on_root_configure(self, _event):
        self._schedule_layout_update()

    def _initialize_window(self):
        self._reflow_checkbox_groups()
        self._set_initial_window_size()
        self._schedule_layout_update()

    def _schedule_layout_update(self):
        if self._layout_update_job is not None:
            self.root.after_cancel(self._layout_update_job)
        self._layout_update_job = self.root.after(20, self._apply_layout_update)

    def _apply_layout_update(self):
        self._layout_update_job = None
        self._update_checkbox_wraplengths()
        self._reflow_checkbox_groups()
        self._reflow_radio_groups()
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._update_scroll_state()

    def _update_checkbox_wraplengths(self):
        available_main_width = max(self._frame.winfo_width() - 220, 140)
        max_main_chars = max(12, available_main_width // 8)
        for item in self._single_checkbox_widgets:
            checkbox = item["widget"]
            label = item["label"]
            wrapped = textwrap.fill(label, width=max_main_chars, break_long_words=True, break_on_hyphens=False)
            checkbox.configure(text=wrapped, wraplength=available_main_width, justify=tk.LEFT)

        for group in self._checkbox_groups:
            options_frame = group["frame"]
            available_group_width = max(options_frame.winfo_width() - 10, 140)
            max_group_chars = max(10, available_group_width // 8)
            for widget, label in zip(group["widgets"], group["labels"]):
                wrapped = textwrap.fill(label, width=max_group_chars, break_long_words=True, break_on_hyphens=False)
                widget.configure(text=wrapped, wraplength=available_group_width, justify=tk.LEFT)

        for group in self._radio_groups:
            options_frame = group["frame"]
            available_group_width = max(options_frame.winfo_width() - 10, 140)
            max_group_chars = max(10, available_group_width // 8)
            for widget, label in zip(group["widgets"], group["labels"]):
                wrapped = textwrap.fill(label, width=max_group_chars, break_long_words=True, break_on_hyphens=False)
                widget.configure(text=wrapped, wraplength=available_group_width, justify=tk.LEFT)

    def _reflow_checkbox_groups(self):
        for group in self._checkbox_groups:
            options_frame = group["frame"]
            widgets = group["widgets"]
            available_width = options_frame.winfo_width()
            if available_width <= 1:
                continue

            x = 0
            y = 0
            row_height = 0
            h_spacing = 12
            v_spacing = 4

            for widget in widgets:
                required_width = min(widget.winfo_reqwidth(), available_width)
                required_height = widget.winfo_reqheight()

                if x > 0 and x + required_width > available_width:
                    x = 0
                    y += row_height + v_spacing
                    row_height = 0

                widget.place(x=x, y=y, width=required_width)
                x += required_width + h_spacing
                row_height = max(row_height, required_height)

            total_height = y + row_height
            options_frame.configure(width=available_width, height=max(total_height, 1))

    def _reflow_radio_groups(self):
        for group in self._radio_groups:
            options_frame = group["frame"]
            widgets = group["widgets"]
            available_width = options_frame.winfo_width()
            if available_width <= 1:
                continue

            x = 0
            y = 0
            row_height = 0
            h_spacing = 12
            v_spacing = 4

            for widget in widgets:
                required_width = min(widget.winfo_reqwidth(), available_width)
                required_height = widget.winfo_reqheight()

                if x > 0 and x + required_width > available_width:
                    x = 0
                    y += row_height + v_spacing
                    row_height = 0

                widget.place(x=x, y=y, width=required_width)
                x += required_width + h_spacing
                row_height = max(row_height, required_height)

            total_height = y + row_height
            options_frame.configure(width=available_width, height=max(total_height, 1))

    def _set_initial_window_size(self):
        self.root.update_idletasks()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        required_width = self._frame.winfo_reqwidth() + 16
        required_height = self._frame.winfo_reqheight() + 16

        max_width = int(screen_width * 0.95)
        max_height = int(screen_height * 0.95)

        if required_width <= max_width and required_height <= max_height:
            self.root.geometry(f"{required_width}x{required_height}")
            return

        try:
            self.root.state("zoomed")
        except tk.TclError:
            self.root.attributes("-fullscreen", True)

    def _update_scroll_state(self):
        content_height = self._frame.winfo_reqheight()
        viewport_height = self._canvas.winfo_height()
        if viewport_height <= 1:
            return

        needs_scroll = content_height > viewport_height
        if needs_scroll and not self._scrollbar_visible:
            self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self._scrollbar_visible = True
        elif not needs_scroll and self._scrollbar_visible:
            self._scrollbar.pack_forget()
            self._scrollbar_visible = False
            self._canvas.yview_moveto(0)

    def _bind_mousewheel(self):
        # Bind globally so wheel scrolling works regardless of focused child widget.
        self.root.bind_all("<MouseWheel>", self._on_mousewheel_windows)
        self.root.bind_all("<Button-4>", self._on_mousewheel_linux_up)
        self.root.bind_all("<Button-5>", self._on_mousewheel_linux_down)

    def _on_mousewheel_windows(self, event):
        if not self._scrollbar_visible:
            return
        if event.delta == 0:
            return
        step = -1 if event.delta > 0 else 1
        self._canvas.yview_scroll(step, "units")

    def _on_mousewheel_linux_up(self, _event):
        if not self._scrollbar_visible:
            return
        self._canvas.yview_scroll(-1, "units")

    def _on_mousewheel_linux_down(self, _event):
        if not self._scrollbar_visible:
            return
        self._canvas.yview_scroll(1, "units")

    def run(self):
        self.root.mainloop()
