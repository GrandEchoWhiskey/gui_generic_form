# GUI Form Toolkit

Tkinter-based toolkit with two desktop windows:

- Dynamic form builder
- DataFrame analysis and editing view

The project also includes centralized logging configuration and a shared GUI log handler.

## Modules

- `main.py`: launcher and window orchestration
- `form_builder.py`: reusable form API with 10+ field types
- `analysis_view.py`: DataFrame browser, filter, edit, and return flow
- `utils/logger.py`: root and window logger setup (file + console)
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

## Logging Architecture

- Root logger is initialized via `build_root_logger()` in `utils/logger.py`
- Logs are written to both console and `gui_form.log` with formatter: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`
- Each opened window gets a timestamped child logger via `create_window_logger()`
- Window lifecycle events (open/close) are logged at `DEBUG` level
- In-window log panels display `INFO` and above (DEBUG excluded from GUI)

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
    logger=my_logger,
)

values = result.get_values()
```

Supported field types:

- `TextField` — single-line text input
- `NumericField` — numeric with optional min/max bounds
- `CheckboxField` — boolean checkbox
- `DropdownField` — dropdown selector with options
- `RadioField` — radio button group
- `DateField` — date picker
- `TimeField` — time picker
- `TextAreaField` — multi-line text
- `ButtonField` — clickable button with callback
- `TableViewField` — embedded read-only table

Callback context:

Each button callback receives a `FormParentContext` object supporting:

- `get_values()` — read current form values as dict
- `set_value(field_name, value)` — update field value
- `reset_field(field_name)` — clear single field
- `reset_all()` — clear all fields
- `debug/info/warning/error(msg)` — write structured logs

Window logging:

- Window open/close events logged at DEBUG level
- Form save/cancel logged at DEBUG
- User interactions logged to in-window panel at INFO+ level

## Data Analyzer

Primary API:

```python
from analysis_view import run_dataframe_analyzer

edited_df = run_dataframe_analyzer(dataframe=my_df, logger=my_logger)
```

Behavior:

- If `dataframe` is provided, it loads; otherwise, demo data is used.
- Closing the analyzer returns the edited DataFrame (or `None` if empty).
- All mutations (add/edit/delete rows) are logged with detailed before/after snapshots.

Main features:

- **Load data**: CSV / Excel import
- **Filter rows**: Multi-row filter system with AND/OR logic
- **Sort**: Click column headers to toggle ascending/descending
- **Column visibility**: Right-click column header or use selector to show/hide columns
- **Edit rows**: Scrollable form with automatic type casting for each field
- **Add rows**: New rows logged with row count update
- **Delete rows**: Shows deleted row data in logs
- **Status bar**: Displays current row and column counts
- **Auto-fit columns**: One-time fit on load; user-resizable afterwards

## Architecture & Design

- **Modular logging**: `utils/logger.py` exports setup functions; `main.py` calls them at startup
- **Shared GUI handler**: `utils/gui_logging.py` provides `GUIHandler` to avoid duplicate logging-to-widget logic
- **Optional loggers**: Form builder and analyzer accept optional `logger` parameter; create internal loggers if none provided
- **DEBUG filtering**: Lifecycle events logged at DEBUG; GUI panels display INFO+ only to reduce noise
- **Child logger per window**: Each window gets a timestamped logger for session isolation
- **Column auto-fit**: DataFrame grid auto-fits columns once on load; user can resize afterwards
