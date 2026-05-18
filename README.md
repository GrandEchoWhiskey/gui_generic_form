# simple_form

`simple_form` is a small Tkinter-based form builder for quickly assembling desktop forms with declarative field definitions.

## What you can do

### Build forms declaratively
Define a form as a subclass of `Form`, then declare fields as class attributes.

```python
from simple_form import Form, TextField, Button

@Form
class MyForm(Form):
    name = TextField(label="Name", default="John Doe")
    submit = Button(label="Submit", on_click="submit_form")

    def submit_form(self):
        print(self.name.value)
```

Run the form with:

```python
MyForm(title="Demo", logging_enabled=True).run()
```

`title` and `logging_enabled` are runtime constructor arguments, not class-body settings.

### Use text inputs
- `TextField` for single-line text.
- `TextArea` for multi-line text.
- `PasswordField` for masked input, with optional reveal button control.

#### Syntax
```python
TextField(label="Name", default="John Doe")
TextArea(label="Description", default="")
PasswordField(label="Password", default="", can_show=False)
```

### Use choice inputs
- `CheckBox` for booleans.
- `CheckBoxGroup` for multiple booleans.
- `RadioGroup` for one-of-many selection.
- `Select` for a clean dropdown selection.
- `MultiSelect` for selecting multiple values with a collapsible summary view.

#### Syntax
```python
CheckBox(label="Accept terms", default=False)
CheckBoxGroup(label="Options", options=[CheckBox(label="A"), CheckBox(label="B")])
RadioGroup(label="Mode", options=[Radio(label="A", default=True), Radio(label="B")])
Select(label="Plan", options=["Basic", "Pro"], default="Pro")
MultiSelect(label="Tags", options=["UI", "API"], default=["UI"], sep="; ")
```

### Use numeric inputs
- `NumberField` for integer or floating-point values.
- Supports `min_value`, `max_value`, `step`, and integer mode.

#### Syntax
```python
NumberField(label="Amount", default=10, min_value=0, max_value=100, step=1, integer=True)
```

### Use file and folder inputs
- `FilePath` for file selection.
- `DirectoryPath` for folder selection.
- Both support browse buttons.
- Both also support drag-and-drop textbox input when `tkinterdnd2` is installed.

#### Syntax
```python
FilePath(label="File", default="", extensions={"text files": ["*.txt"], "all files": ["*.*"]})
DirectoryPath(label="Folder", default="")
```

### Use date and time inputs
- `DatePicker` supports configurable `date_format`.
- `TimePicker` supports configurable `time_format`.
- Both include:
  - split/text input modes
  - a picker button
  - a Today button for date
  - a Now button for time
  - validation on focus out / invalid input handling

#### Syntax
```python
DatePicker(label="Date", default="18.05.2026", date_format="%d.%m.%Y")
TimePicker(label="Time", default="14:30", time_format="%H:%M")
```

### Log from the form
When `logging_enabled=True`, the form creates an internal logging area.

You can write log messages using the standard `logging` module:

```python
import logging
logging.info("Started")
logging.warning("Something to check")
logging.error("Something failed")
```

The form automatically hooks into the root logging configuration when it is created, and it forwards `INFO` and above into the form log area.
`DEBUG` messages are ignored by default.

## Available field types

- `TextField`
- `PasswordField`
- `TextArea`
- `Button`
- `CheckBox`
- `CheckBoxGroup`
- `RadioGroup`
- `Select`
- `MultiSelect`
- `NumberField`
- `FilePath`
- `DirectoryPath`
- `DatePicker`
- `TimePicker`

## Field behavior

### `.value`
Each bound field exposes a `.value` property for reading and writing the current value.

Examples:

```python
print(self.name.value)
self.name.value = "New value"
```

For groups and special controls:
- `CheckBoxGroup.value` returns a `dict[str, bool]`
- `RadioGroup.value` returns a `str`
- `Select.value` returns a `str`
- `MultiSelect.value` returns a `list[str]`
- `NumberField.value` returns an `int` or `float`
- `DatePicker.value` returns a formatted string
- `TimePicker.value` returns a formatted string

## Form constructor options

`Form` accepts runtime overrides:

```python
MyForm(title="My App", logging_enabled=True)
```

Supported overrides:
- `title`
- `logging_enabled`

Unknown constructor arguments raise `TypeError`.

## Validation rules

Several controls validate their configuration at setup time:

- `RadioGroup` must have exactly one default option.
- `Select` requires non-empty options and default must be in options.
- `MultiSelect` requires non-empty options and defaults must exist in options.
- `NumberField` requires positive step and valid min/max range.
- `DatePicker` validates `date_format` and `default` against that format.
- `TimePicker` validates `time_format` and `default` against that format.

## Date and time formatting

### DatePicker
Use any `datetime.strptime` / `strftime` compatible format supported by the picker’s token set.

Example:

```python
DatePicker(label="Date", default="18.05.2026", date_format="%d.%m.%Y")
```

### TimePicker
Use a compatible time format for split/text mode.

Example:

```python
TimePicker(label="Time", time_format="%H:%M")
```

The split view adapts to the directives you include in the format string.

## Drag and drop

`FilePath` and `DirectoryPath` can accept drops directly into the textbox when `tkinterdnd2` is installed.

If `tkinterdnd2` is not available, browse buttons still work normally.

## Dependencies

Runtime dependency:

```text
tkinterdnd2
```

Python’s built-in `tkinter` module is used as well.

## Example form

```python
from simple_form import (
    Form,
    TextField,
    PasswordField,
    Select,
    MultiSelect,
    NumberField,
    FilePath,
    DirectoryPath,
    DatePicker,
    TimePicker,
    Button,
)

@Form
class MyForm(Form):
    name = TextField(label="Name")
    secret = PasswordField(label="Secret", can_show=False)
    plan = Select(label="Plan", options=["Basic", "Pro", "Enterprise"], default="Pro")
    tags = MultiSelect(label="Tags", options=["UI", "API", "DB"], default=["UI"], sep="; ")
    amount = NumberField(label="Amount", default=10, min_value=0, max_value=100, step=1, integer=True)
    file_path = FilePath(label="File")
    folder_path = DirectoryPath(label="Folder")
    date = DatePicker(label="Date", default="18.05.2026", date_format="%d.%m.%Y")
    time = TimePicker(label="Time", time_format="%H:%M")
    submit = Button(label="Submit", on_click="on_submit")

    def on_submit(self):
        print(self.name.value)
        print(self.secret.value)
        print(self.plan.value)
        print(self.tags.value)
        print(self.amount.value)
        print(self.file_path.value)
        print(self.folder_path.value)
        print(self.date.value)
        print(self.time.value)

if __name__ == "__main__":
    MyForm(title="My Form", logging_enabled=True).run()
```

## Notes

- `PasswordField.can_show` controls whether reveal is available.
- `MultiSelect.sep` controls how collapsed selections are joined.
- If you want debug output in the log area, configure logging accordingly before using the form.
