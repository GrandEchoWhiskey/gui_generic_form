# Generic Tk Form Builder

A reusable Tkinter form utility built around one function:

- `create_form_window(fields, title="Generic Tk Form", on_save=None)`

You define fields as dictionaries, and the form is built automatically.

## Features

- One-function window creation
- Supported field types:
  - `textbox`
  - `numeric`
  - `checkbox`
  - `dropdown` / `dropbox`
  - `radio`
  - `date` / `datepicker`
  - `time` / `timepicker`
  - `textarea`
  - `button` / `action`
- Date picker popup with calendar
- Time picker popup with `HH:MM:SS` controls and `Now`
- Read-only log panel
- Save button returns form data as a dictionary
- Custom button callbacks with parent context

## Quick Start

Run:

```bash
python main.py
```

## Basic Usage

```python
from main import create_form_window, FormParentContext


def preview(parent: FormParentContext, values: dict):
    parent.log_info("Preview clicked")
    parent.set_value("username", "JohnDoe")


fields = [
    {"name": "username", "label": "User Name", "type": "textbox"},
    {"name": "age", "label": "Age", "type": "numeric", "default": 25, "min": 0, "max": 130},
    {"name": "start_date", "label": "Start Date", "type": "date"},
    {"name": "start_time", "label": "Start Time", "type": "time"},
    {"name": "notes", "label": "Notes", "type": "textarea", "height": 5},
    {"type": "button", "label": "Preview", "on_click": preview},
]

result = create_form_window(fields, title="Dynamic Tk Form")
print(result)
```

## Field Definition Notes

Common keys:

- `name`: required for all non-button fields
- `label`: text shown on the left
- `type`: one of supported field types
- `default`: initial value

Type-specific keys:

- `dropdown` / `dropbox`:
  - `options`: list of values
- `radio`:
  - `options`: list of values
- `numeric`:
  - `min`, `max`, `default`
- `textarea`:
  - `height`
- `date`:
  - `format` (default: `%Y-%m-%d`)
- `time`:
  - `format` (default: `%H:%M:%S`)
- `button`:
  - `on_click`: callback

## Button Callback Signature

Current callback order is:

- `on_click(parent)`
- `on_click(parent, values)`

Where:

- `parent` is `FormParentContext`
- `values` is current form values dictionary

## FormParentContext API

Methods and properties available in callbacks:

- `parent.root`
- `parent.get_values()`
- `parent.set_value(name, value)`
- `parent.reset_field(name)`
- `parent.reset_fields(names)`
- `parent.reset_all()`
- `parent.log_debug(msg, *args)`
- `parent.log_info(msg, *args)`
- `parent.log_warning(msg, *args)`
- `parent.log_error(msg, *args)`
- `parent.log_critical(msg, *args)`
- `parent.log_exception(msg, *args)`

## Save Behavior

- Clicking Save returns all form values as a dictionary.
- Closing the window without Save returns an empty dictionary.
