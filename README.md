# GUI Form Toolkit

Tkinter-based toolkit with two desktop windows:

- Dynamic form builder
- DataFrame analysis and editing view

The project also includes centralized logging configuration and a shared GUI log handler.

## Modules

- `main.py`: launcher and root logger setup (file + console)
- `form_builder.py`: reusable form API and field classes
- `analysis_view.py`: DataFrame browser, filter, edit, and return flow
- `utils/gui_logging.py`: shared `GUIHandler` for writing logs into Tk text widgets

## Requirements

- Python 3.10+
- `pandas` for the analysis window

Install dependencies:

```bash
pip install pandas
```

## Run

```bash
python main.py
```

Launcher options:

- `1`: open Form Builder window
- `2`: open Data Analyzer window
- `q`: quit launcher

## Logging Behavior

- Root logger is configured in `main.py`.
- Logs are written to both console and `gui_form.log`.
- Each opened window gets a child logger.
- Window open/close lifecycle logs use `DEBUG` level.
- In-window log panels show `INFO` and above (no debug noise).

## Form Builder

Primary API:

```python
from form_builder import create_form_window, TextField, NumericField

result = create_form_window(
    fields=[
        TextField("username"),
        NumericField("age", default=25, min_value=0, max_value=130),
    ],
    title="My Form",
)

values = result.get_values()
```

Supported field objects:

- `TextField`
- `NumericField`
- `CheckboxField`
- `DropdownField`
- `RadioField`
- `DateField`
- `TimeField`
- `TextAreaField`
- `ButtonField`
- `TableViewField`

Callback context supports:

- Reading values
- Setting values
- Resetting one or many fields
- Writing structured logs (`debug/info/warning/error/...`)

## Data Analyzer

Primary API:

```python
from analysis_view import run_dataframe_analyzer

edited_df = run_dataframe_analyzer(dataframe=my_df)
```

Behavior:

- If `dataframe` is provided, demo data is not loaded.
- If `dataframe` is `None`, demo data is loaded.
- Closing the analyzer returns the current edited DataFrame (or `None` when empty).

Main features:

- Load CSV / Excel
- Multi-filter rows with `AND` / `OR`
- Column visibility selector
- Sort by column header
- Add, edit, and delete rows
- Edit dialog with all columns
- Detailed mutation logs showing changed row data

## Notes

- The DataFrame grid is auto-fitted once after load and then remains user-resizable.
- Shared GUI logging handler lives in `utils/gui_logging.py` to avoid duplicated logic.
