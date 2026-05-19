import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import pandas as pd


def _safe_describe(dataframe: pd.DataFrame) -> pd.DataFrame:
	if dataframe.empty:
		return pd.DataFrame({"Info": ["DataFrame is empty"]})

	summary = dataframe.describe(include="all").transpose().reset_index()
	summary = summary.rename(columns={"index": "Column"})
	return summary.fillna("")


def _missing_values_table(dataframe: pd.DataFrame) -> pd.DataFrame:
	if dataframe.empty:
		return pd.DataFrame(columns=["Column", "Missing Count", "Missing %"])

	missing_count = dataframe.isna().sum()
	missing_percent = (missing_count / len(dataframe) * 100).round(2) if len(dataframe) else missing_count
	return pd.DataFrame(
		{
			"Column": dataframe.columns,
			"Missing Count": [int(missing_count[column]) for column in dataframe.columns],
			"Missing %": [float(missing_percent[column]) for column in dataframe.columns],
		}
	)


def _dtypes_table(dataframe: pd.DataFrame) -> pd.DataFrame:
	return pd.DataFrame(
		{
			"Column": dataframe.columns,
			"Dtype": [str(dtype) for dtype in dataframe.dtypes],
			"Non-Null Count": [int(dataframe[column].notna().sum()) for column in dataframe.columns],
		}
	)


def _table_ready(dataframe: pd.DataFrame, include_index: bool = False) -> pd.DataFrame:
	frame = dataframe.copy()
	if include_index:
		frame = frame.reset_index().rename(columns={"index": "Index"})
	return frame.fillna("")


class _DataFrameAnalysisWindow:
	def __init__(
		self,
		dataframe: pd.DataFrame,
		title: str,
		hide_index: bool,
		filter_columns: list[str] | None = None,
		rev_filter_columns: list[str] | None = None,
	):
		self._original_dataframe = dataframe.copy()  # Keep original for cancel scenario
		self._dataframe = dataframe.copy()
		self._hide_index = hide_index
		self._visible_columns = self._resolve_visible_columns(filter_columns, rev_filter_columns)
		self._data_search_filter = ""
		self._data_tree = None
		self._advanced_filters: list[dict] = []  # [{"column": str, "condition": str, "value": str}, ...]
		self._data_filters_frame = None  # Will hold the active filters display frame
		self._sort_column: str | None = None
		self._sort_descending = False
		self._data_row_positions: list[int] = []
		self._done_with_filter_clicked = False
		self._done_clicked = False  # Track if Done button was clicked
		self._notebook = None
		self._tabs: dict[str, ttk.Frame] = {}
		if tk._default_root is None:
			self._root = tk.Tk()
			self._owns_mainloop = True
		else:
			self._root = tk.Toplevel(tk._default_root)
			self._owns_mainloop = False
		self._root.title(title)
		self._root.geometry("1000x640")
		self._root.minsize(700, 420)

		container = ttk.Frame(self._root, padding=12)
		container.pack(fill=tk.BOTH, expand=True)

		self._build_tabs(container)
		self._build_footer(container)

	def _resolve_visible_columns(
		self,
		filter_columns: list[str] | None,
		rev_filter_columns: list[str] | None,
	) -> list[str]:
		all_columns = [str(column) for column in self._dataframe.columns]
		if filter_columns and rev_filter_columns:
			raise ValueError("Pass either filter or rev_filter, not both")

		if rev_filter_columns:
			hidden = {str(column) for column in rev_filter_columns}
			remaining = [column for column in all_columns if column not in hidden]
			if remaining:
				return remaining
			return all_columns

		if not filter_columns:
			return all_columns

		allowed = set(all_columns)
		selected = [str(column) for column in filter_columns if str(column) in allowed]
		if selected:
			return selected
		return all_columns

	def show(self):
		self._root.protocol("WM_DELETE_WINDOW", self._on_window_close)
		if self._owns_mainloop:
			self._root.mainloop()
		else:
			self._root.wait_window(self._root)

	def _on_window_close(self):
		# If Done wasn't clicked, restore original dataframe
		if not self._done_clicked:
			self._dataframe = self._original_dataframe
		self._root.destroy()

	def _on_done_clicked(self):
		self._done_with_filter_clicked = False
		self._done_clicked = True
		self._root.destroy()

	def _on_done_with_filter_clicked(self):
		filtered_rows = self._build_visible_dataframe(apply_search=False, apply_sort=True)
		self._dataframe = self._dataframe.loc[filtered_rows.index].reset_index(drop=True)
		self._done_with_filter_clicked = True
		self._done_clicked = True
		self._root.destroy()

	def destroy(self):
		self._root.update_idletasks()
		self._root.destroy()

	def _build_footer(self, parent):
		footer = ttk.Frame(parent)
		footer.pack(fill=tk.X, pady=(12, 0))

		rows, _ = self._dataframe.shape
		visible_cols = len([column for column in self._visible_columns if column in self._dataframe.columns])
		total_cols = len(self._dataframe.columns)
		missing_values = int(self._dataframe.isna().sum().sum())
		ttk.Label(
			footer,
			text=f"Rows: {rows}    Columns: {visible_cols}/{total_cols}    Missing values: {missing_values}",
		).pack(side=tk.LEFT)

		ttk.Button(footer, text="Done", command=self._on_done_clicked).pack(side=tk.RIGHT, padx=(8, 0))
		ttk.Button(footer, text="Done With Filter", command=self._on_done_with_filter_clicked).pack(
			side=tk.RIGHT,
			padx=(8, 0),
		)

		self._footer = footer
		self._footer_label = footer.winfo_children()[0]

	def _build_tabs(self, parent):
		self._notebook = ttk.Notebook(parent)
		self._notebook.pack(fill=tk.BOTH, expand=True)
		self._render_tabs()

	def _render_tabs(self):
		if self._notebook is None:
			return

		current_tab = self._notebook.select() if self._notebook.tabs() else None
		for tab_id in self._notebook.tabs():
			self._notebook.forget(tab_id)

		self._tabs.clear()

		visible_df = self._build_visible_dataframe(apply_search=False, apply_sort=False)
		data_df = self._build_visible_dataframe(apply_search=True, apply_sort=True)
		self._data_row_positions = [int(position) for position in data_df.index.tolist()]

		views = [
			("Data", _table_ready(data_df, include_index=not self._hide_index)),
			("Summary", _safe_describe(visible_df)),
			("Dtypes", _dtypes_table(visible_df)),
			("Missing", _missing_values_table(visible_df)),
		]

		for tab_name, frame in views:
			tab = ttk.Frame(self._notebook, padding=8)
			self._notebook.add(tab, text=tab_name)
			self._tabs[tab_name] = tab
			self._populate_table(tab, frame, tab_name=tab_name)

		if current_tab:
			available_tabs = self._notebook.tabs()
			if current_tab in available_tabs:
				self._notebook.select(current_tab)

		if hasattr(self, "_footer_label"):
			total_rows, _ = self._dataframe.shape
			cols = len(self._visible_columns)
			total_cols = len(self._dataframe.columns)
			missing_values = int(self._dataframe.isna().sum().sum())

			# Show filtered row count if advanced filters are active
			if self._advanced_filters or self._data_search_filter:
				filtered_rows = len(data_df)
				row_text = f"{filtered_rows}/{total_rows}"
			else:
				row_text = str(total_rows)

			self._footer_label.configure(
				text=f"Rows: {row_text}    Columns: {cols}/{total_cols}    Missing values: {missing_values}"
			)

	def _build_visible_dataframe(self, apply_search: bool, apply_sort: bool) -> pd.DataFrame:
		filtered_df = self._dataframe.copy()
		if self._advanced_filters:
			filtered_df = self._apply_advanced_filters(filtered_df)

		visible_columns = [col for col in self._visible_columns if col in filtered_df.columns]
		if visible_columns:
			visible_df = filtered_df.loc[:, visible_columns].copy()
		else:
			visible_df = pd.DataFrame(index=filtered_df.index)

		if apply_search and self._data_search_filter:
			visible_df = self._apply_search_filter(visible_df, self._data_search_filter)

		if apply_sort:
			visible_df = self._apply_sort(visible_df)

		return visible_df

	def _apply_sort(self, dataframe: pd.DataFrame) -> pd.DataFrame:
		if self._sort_column is None:
			return dataframe

		if self._sort_column == "__index__":
			return dataframe.sort_index(ascending=not self._sort_descending, kind="mergesort")

		if self._sort_column not in dataframe.columns:
			return dataframe

		column = self._sort_column
		series = dataframe[column]
		numeric_series = pd.to_numeric(series, errors="coerce")
		if numeric_series.notna().any():
			sort_frame = dataframe.assign(__sort_value=numeric_series)
			sorted_frame = sort_frame.sort_values(
				"__sort_value",
				ascending=not self._sort_descending,
				na_position="last",
				kind="mergesort",
			)
			return sorted_frame.drop(columns=["__sort_value"])

		return dataframe.sort_values(
			by=column,
			ascending=not self._sort_descending,
			na_position="last",
			kind="mergesort",
			key=lambda s: s.astype(str).str.lower(),
		)

	def _header_text(self, column: str, tab_name: str) -> str:
		if tab_name != "Data":
			return column

		if self._sort_column == column:
			arrow = "▼" if self._sort_descending else "▲"
			return f"{column} {arrow}"

		if self._sort_column == "__index__" and column == "Index":
			arrow = "▼" if self._sort_descending else "▲"
			return f"{column} {arrow}"

		return column

	def _on_data_header_click(self, column: str):
		target = "__index__" if column == "Index" and not self._hide_index else column

		if self._sort_column == target:
			self._sort_descending = not self._sort_descending
		else:
			self._sort_column = target
			self._sort_descending = False

		self._render_tabs()

	def _clear_data_sort(self):
		self._sort_column = None
		self._sort_descending = False
		self._render_tabs()

	def _visible_dataframe(self) -> pd.DataFrame:
		columns = [column for column in self._visible_columns if column in self._dataframe.columns]
		if not columns:
			return pd.DataFrame(index=self._dataframe.index)
		return self._dataframe.loc[:, columns].copy()

	def _populate_table(self, parent, dataframe: pd.DataFrame, tab_name: str):
		if tab_name == "Data":
			action_row = ttk.Frame(parent)
			action_row.pack(fill=tk.X, pady=(0, 8))
			ttk.Button(action_row, text="Add Row", command=self._open_add_row_from_pointer).pack(side=tk.LEFT)
			ttk.Button(action_row, text="Filter Columns", command=self._open_column_filter).pack(side=tk.LEFT, padx=(8, 0))
			ttk.Button(action_row, text="Clear Sort", command=self._clear_data_sort).pack(side=tk.LEFT, padx=(8, 0))
			ttk.Label(action_row, text="Search:").pack(side=tk.LEFT, padx=(16, 4))
			search_entry = ttk.Entry(action_row, width=25)
			search_entry.pack(side=tk.LEFT)
			search_entry.insert(0, self._data_search_filter)
			search_entry.bind(
				"<KeyRelease>",
				lambda _event: self._on_data_search_change(search_entry.get()),
			)

			# Advanced filter row
			adv_row = ttk.Frame(parent)
			adv_row.pack(fill=tk.X, pady=(0, 8))

			ttk.Label(adv_row, text="Advanced:").pack(side=tk.LEFT, padx=(0, 4))

			# Column selector
			ttk.Label(adv_row, text="Column:").pack(side=tk.LEFT, padx=(0, 4))
			col_var = tk.StringVar()
			col_dropdown = ttk.Combobox(
				adv_row,
				textvariable=col_var,
				values=list(self._visible_dataframe().columns),
				state="readonly",
				width=12,
			)
			col_dropdown.pack(side=tk.LEFT, padx=(0, 8))

			# Condition selector
			ttk.Label(adv_row, text="Condition:").pack(side=tk.LEFT, padx=(0, 4))
			cond_var = tk.StringVar(value="contains")
			cond_dropdown = ttk.Combobox(
				adv_row,
				textvariable=cond_var,
				values=["contains", "equals", "regex", "starts with", "ends with", "bigger than", "less than", "bigger or equal", "less or equal", "empty", "not empty"],
				state="readonly",
				width=15,
			)
			cond_dropdown.pack(side=tk.LEFT, padx=(0, 8))

			# Value input
			ttk.Label(adv_row, text="Value:").pack(side=tk.LEFT, padx=(0, 4))
			value_entry = ttk.Entry(adv_row, width=20)
			value_entry.pack(side=tk.LEFT, padx=(0, 8))

			def add_advanced_filter():
				col = col_var.get()
				cond = cond_var.get()
				val = value_entry.get().strip()
				if col and val:
					self._add_advanced_filter(col, cond, val)
					value_entry.delete(0, tk.END)

			ttk.Button(adv_row, text="Add Filter", command=add_advanced_filter).pack(side=tk.LEFT, padx=(0, 8))
			ttk.Button(adv_row, text="Clear All", command=self._clear_advanced_filters).pack(side=tk.LEFT)

			# Active filters display container (will be updated dynamically)
			self._data_filters_frame = ttk.Frame(parent)
			self._data_filters_frame.pack(fill=tk.X, pady=(0, 8))
			self._update_filters_display()

		table_frame = ttk.Frame(parent)
		table_frame.pack(fill=tk.BOTH, expand=True)

		columns = [str(column) for column in dataframe.columns]
		tree = ttk.Treeview(table_frame, columns=columns, show="headings")
		tree.grid(row=0, column=0, sticky="nsew")

		y_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
		y_scroll.grid(row=0, column=1, sticky="ns")

		x_scroll = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=tree.xview)
		x_scroll.grid(row=1, column=0, sticky="ew")

		tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
		table_frame.grid_rowconfigure(0, weight=1)
		table_frame.grid_columnconfigure(0, weight=1)

		if not columns:
			columns = ["Info"]
			tree.configure(columns=columns)
			tree.heading("Info", text="Info")
			tree.column("Info", width=300, anchor=tk.W)
			tree.insert("", tk.END, values=("No columns available",))
			return

		initial_widths: dict[str, int] = {}
		for column in columns:
			width = max(120, min(260, len(column) * 12))
			header_text = self._header_text(column, tab_name)
			if tab_name == "Data":
				tree.heading(column, text=header_text, command=lambda c=column: self._on_data_header_click(c))
			else:
				tree.heading(column, text=header_text)
			tree.column(column, width=width, minwidth=90, anchor=tk.W, stretch=False)
			initial_widths[column] = width

		for row_idx, row in enumerate(dataframe.itertuples(index=False, name=None)):
			iid = str(len(tree.get_children()))
			if tab_name == "Data" and row_idx < len(self._data_row_positions):
				iid = str(self._data_row_positions[row_idx])
			tree.insert("", tk.END, iid=iid, values=tuple("" if value is None else str(value) for value in row))

		if tab_name == "Data":
			self._data_tree = tree

		if tab_name == "Data":
			tree.bind("<Double-1>", lambda event: self._on_data_row_double_click(event, tree))

		bind_id = tree.bind(
			"<Configure>",
			lambda _event: self._fit_columns_to_width(tree, columns, initial_widths, bind_id),
		)

	def _on_data_row_double_click(self, event, tree: ttk.Treeview):
		row_id = tree.identify_row(event.y)
		if not row_id:
			return

		row_position = int(row_id)
		if row_position < 0 or row_position >= len(self._dataframe):
			return

		popup_x = event.x_root + 12
		popup_y = event.y_root + 10

		self._open_row_editor(row_position, popup_x, popup_y)

	def _on_data_search_change(self, search_text: str):
		self._data_search_filter = search_text.strip()
		if not self._data_tree or not self._data_tree.winfo_exists():
			return

		visible_df = self._build_visible_dataframe(apply_search=True, apply_sort=True)
		self._data_row_positions = [int(position) for position in visible_df.index.tolist()]

		display_df = _table_ready(visible_df, include_index=not self._hide_index)
		self._refresh_data_tree(display_df, row_positions=self._data_row_positions)

	def _apply_search_filter(self, dataframe: pd.DataFrame, search_text: str) -> pd.DataFrame:
		if not search_text:
			return dataframe

		search_lower = search_text.lower()
		mask = pd.Series([False] * len(dataframe))
		for column in dataframe.columns:
			col_mask = dataframe[column].astype(str).str.lower().str.contains(search_lower, na=False)
			mask = mask | col_mask

		return dataframe[mask]

	def _refresh_data_tree(self, dataframe: pd.DataFrame, row_positions: list[int] | None = None):
		if not self._data_tree or not self._data_tree.winfo_exists():
			return

		for item in self._data_tree.get_children():
			self._data_tree.delete(item)

		for row_idx, row in enumerate(dataframe.itertuples(index=False, name=None)):
			iid = ""
			if row_positions is not None and row_idx < len(row_positions):
				iid = str(row_positions[row_idx])
			self._data_tree.insert("", tk.END, iid=iid, values=tuple("" if value is None else str(value) for value in row))

	def _add_advanced_filter(self, column: str, condition: str, value: str):
		self._advanced_filters.append({"column": column, "condition": condition, "value": value})
		self._update_filters_display()
		self._refresh_data_display()

	def _remove_advanced_filter(self, index: int):
		if 0 <= index < len(self._advanced_filters):
			self._advanced_filters.pop(index)
		self._update_filters_display()
		self._refresh_data_display()

	def _clear_advanced_filters(self):
		self._advanced_filters.clear()
		self._update_filters_display()
		self._refresh_data_display()

	def _update_filters_display(self):
		if not self._data_filters_frame or not self._data_filters_frame.winfo_exists():
			return

		# Clear existing children
		for child in self._data_filters_frame.winfo_children():
			child.destroy()

		if not self._advanced_filters:
			return

		ttk.Label(self._data_filters_frame, text="Active filters:").pack(side=tk.LEFT, padx=(0, 8))

		for idx, filt in enumerate(self._advanced_filters):
			filter_text = f"{filt['column']} {filt['condition']} '{filt['value']}'"
			filter_label = ttk.Label(self._data_filters_frame, text=filter_text, foreground="blue")
			filter_label.pack(side=tk.LEFT, padx=(0, 4))

			def remove_filter(filter_idx=idx):
				self._remove_advanced_filter(filter_idx)

			ttk.Button(
				self._data_filters_frame,
				text="✕",
				width=2,
				command=remove_filter,
			).pack(side=tk.LEFT, padx=(0, 8))

	def _apply_advanced_filters(self, dataframe: pd.DataFrame) -> pd.DataFrame:
		result = dataframe.copy()
		for filt in self._advanced_filters:
			col = filt["column"]
			cond = filt["condition"]
			val = filt["value"]

			if col not in result.columns:
				continue

			col_data = result[col].astype(str)

			if cond == "contains":
				mask = col_data.str.contains(val, case=False, na=False)
			elif cond == "equals":
				mask = col_data == val
			elif cond == "regex":
				try:
					mask = col_data.str.contains(val, regex=True, case=False, na=False)
				except:
					mask = pd.Series([False] * len(result))
			elif cond == "starts with":
				mask = col_data.str.startswith(val, na=False)
			elif cond == "ends with":
				mask = col_data.str.endswith(val, na=False)
			elif cond in ["bigger than", "less than", "bigger or equal", "less or equal"]:
				try:
					numeric_val = float(val)
					numeric_col = pd.to_numeric(result[col], errors="coerce")
					if cond == "bigger than":
						mask = numeric_col > numeric_val
					elif cond == "less than":
						mask = numeric_col < numeric_val
					elif cond == "bigger or equal":
						mask = numeric_col >= numeric_val
					elif cond == "less or equal":
						mask = numeric_col <= numeric_val
				except:
					mask = pd.Series([False] * len(result))
			elif cond == "empty":
				mask = result[col].isna() | (result[col].astype(str).str.strip() == "")
			elif cond == "not empty":
				mask = ~(result[col].isna() | (result[col].astype(str).str.strip() == ""))
			else:
				mask = pd.Series([True] * len(result))

			result = result[mask]

		return result

	def _refresh_data_display(self):
		if not self._data_tree or not self._data_tree.winfo_exists():
			return

		visible_df = self._build_visible_dataframe(apply_search=True, apply_sort=True)
		self._data_row_positions = [int(position) for position in visible_df.index.tolist()]

		display_df = _table_ready(visible_df, include_index=not self._hide_index)
		self._refresh_data_tree(display_df, row_positions=self._data_row_positions)

		# Update footer with filtered row count
		if hasattr(self, "_footer_label"):
			filtered_rows = len(visible_df)
			total_rows, _ = self._dataframe.shape
			cols = len(self._visible_columns)
			total_cols = len(self._dataframe.columns)
			missing_values = int(self._dataframe.isna().sum().sum())
			row_text = f"{filtered_rows}/{total_rows}" if filtered_rows != total_rows else str(filtered_rows)
			self._footer_label.configure(
				text=f"Rows: {row_text}    Columns: {cols}/{total_cols}    Missing values: {missing_values}"
			)

	def _open_add_row_from_pointer(self):
		popup_x = self._root.winfo_pointerx() + 12
		popup_y = self._root.winfo_pointery() + 10
		self._open_row_editor(None, popup_x, popup_y)

	def _open_column_filter(self):
		dialog = tk.Toplevel(self._root)
		dialog.title("Filter Columns")
		dialog.transient(self._root)
		dialog.grab_set()
		dialog.resizable(True, True)

		container = ttk.Frame(dialog, padding=12)
		container.pack(fill=tk.BOTH, expand=True)
		container.grid_rowconfigure(0, weight=1)
		container.grid_columnconfigure(0, weight=1)

		canvas = tk.Canvas(container, highlightthickness=0, borderwidth=0)
		canvas.grid(row=0, column=0, sticky="nsew")

		scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
		scrollbar.grid(row=0, column=1, sticky="ns")
		canvas.configure(yscrollcommand=scrollbar.set)

		inner = ttk.Frame(canvas)
		inner_window = canvas.create_window((0, 0), window=inner, anchor="nw")

		def _sync_scroll_region(_event=None):
			canvas.configure(scrollregion=canvas.bbox("all"))

		def _sync_inner_width(_event):
			canvas.itemconfigure(inner_window, width=_event.width)

		inner.bind("<Configure>", _sync_scroll_region)
		canvas.bind("<Configure>", _sync_inner_width)

		column_vars: dict[str, tk.BooleanVar] = {}
		select_all_var = tk.BooleanVar(value=True)

		def _sync_select_all_from_items():
			if not column_vars:
				select_all_var.set(False)
				return
			select_all_var.set(all(var.get() for var in column_vars.values()))

		def _toggle_all_from_select_all():
			state = select_all_var.get()
			for var in column_vars.values():
				var.set(state)

		ttk.Checkbutton(
			inner,
			text="Select all",
			variable=select_all_var,
			command=_toggle_all_from_select_all,
		).grid(row=0, column=0, sticky="w", pady=(0, 8))

		for row_index, column in enumerate(self._dataframe.columns):
			column_name = str(column)
			selected = column_name in self._visible_columns
			var = tk.BooleanVar(value=selected)
			column_vars[column_name] = var
			var.trace_add("write", lambda *_args: _sync_select_all_from_items())
			ttk.Checkbutton(inner, text=column_name, variable=var).grid(
				row=row_index + 1,
				column=0,
				sticky="w",
				pady=2,
			)

		_sync_select_all_from_items()

		button_row = ttk.Frame(container)
		button_row.grid(row=1, column=0, columnspan=2, sticky="e", pady=(12, 0))

		ttk.Button(button_row, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=(8, 0))
		ttk.Button(
			button_row,
			text="Apply",
			command=lambda: self._apply_column_filter(column_vars, dialog),
		).pack(side=tk.LEFT, padx=(8, 0))

		dialog.bind(
			"<MouseWheel>",
			lambda event: canvas.yview_scroll(-1 if event.delta > 0 else 1, "units"),
		)

		dialog.update_idletasks()
		self._place_dialog_near_point(dialog, self._root.winfo_pointerx() + 12, self._root.winfo_pointery() + 10)

	def _apply_column_filter(self, column_vars: dict[str, tk.BooleanVar], dialog: tk.Toplevel):
		selected_columns = [column for column in self._dataframe.columns if column_vars[str(column)].get()]
		if not selected_columns:
			messagebox.showwarning("No columns selected", "Select at least one column.", parent=dialog)
			return

		self._visible_columns = [str(column) for column in selected_columns]
		if self._sort_column and self._sort_column not in self._visible_columns and self._sort_column != "__index__":
			self._sort_column = None
			self._sort_descending = False
		dialog.destroy()
		self._render_tabs()

	def _open_row_editor(self, row_position: int | None, popup_x: int, popup_y: int):
		is_add_mode = row_position is None
		edit_columns = [column for column in self._visible_columns if column in self._dataframe.columns]
		if not edit_columns:
			edit_columns = [str(column) for column in self._dataframe.columns]

		if is_add_mode:
			row_series = pd.Series({column: "" for column in edit_columns})
			title_text = "Add Row"
		else:
			row_series = self._dataframe.loc[self._dataframe.index[row_position], edit_columns]
			title_text = f"Edit Row {row_position}"

		dialog = tk.Toplevel(self._root)
		dialog.title(title_text)
		dialog.transient(self._root)
		dialog.grab_set()
		dialog.resizable(True, True)

		container = ttk.Frame(dialog, padding=12)
		container.pack(fill=tk.BOTH, expand=True)
		container.grid_rowconfigure(0, weight=1)
		container.grid_columnconfigure(0, weight=1)

		fields_outer = ttk.Frame(container)
		fields_outer.grid(row=0, column=0, sticky="nsew")
		fields_outer.grid_rowconfigure(0, weight=1)
		fields_outer.grid_columnconfigure(0, weight=1)

		fields_canvas = tk.Canvas(fields_outer, highlightthickness=0, borderwidth=0)
		fields_canvas.grid(row=0, column=0, sticky="nsew")

		fields_scroll = ttk.Scrollbar(fields_outer, orient=tk.VERTICAL, command=fields_canvas.yview)
		fields_scroll.grid(row=0, column=1, sticky="ns")
		fields_canvas.configure(yscrollcommand=fields_scroll.set)

		fields_frame = ttk.Frame(fields_canvas)
		fields_window = fields_canvas.create_window((0, 0), window=fields_frame, anchor="nw")

		def _sync_scroll_region(_event=None):
			fields_canvas.configure(scrollregion=fields_canvas.bbox("all"))

		def _sync_fields_width(_event):
			fields_canvas.itemconfigure(fields_window, width=_event.width)

		fields_frame.bind("<Configure>", _sync_scroll_region)
		fields_canvas.bind("<Configure>", _sync_fields_width)

		entries: dict[str, tk.Entry] = {}
		for row_index, column in enumerate(edit_columns):
			ttk.Label(fields_frame, text=str(column)).grid(row=row_index, column=0, sticky="w", padx=(0, 12), pady=4)
			entry = ttk.Entry(fields_frame)
			entry.grid(row=row_index, column=1, sticky="ew", pady=4)
			value = row_series[column]
			entry.insert(0, "" if pd.isna(value) else str(value))
			entries[str(column)] = entry

		fields_frame.grid_columnconfigure(1, weight=1)

		button_row = ttk.Frame(container)
		button_row.grid(row=1, column=0, sticky="e", pady=(12, 0))

		if not is_add_mode:
			ttk.Button(
				button_row,
				text="Delete",
				command=lambda: self._delete_row(row_position, dialog),
			).pack(side=tk.LEFT)
		ttk.Button(
			button_row,
			text="Cancel",
			command=dialog.destroy,
		).pack(side=tk.LEFT, padx=(8, 0))
		ttk.Button(
			button_row,
			text="Save",
			command=lambda: self._save_row_edits(row_position, entries, dialog),
		).pack(side=tk.LEFT, padx=(8, 0))

		first_entry = next(iter(entries.values()), None)
		if first_entry is not None:
			first_entry.focus_set()

		dialog.bind(
			"<MouseWheel>",
			lambda event: fields_canvas.yview_scroll(-1 if event.delta > 0 else 1, "units"),
		)

		dialog.update_idletasks()
		self._place_dialog_near_point(dialog, popup_x, popup_y)

	def _place_dialog_near_point(self, dialog: tk.Toplevel, x: int, y: int):
		screen_width = dialog.winfo_screenwidth()
		screen_height = dialog.winfo_screenheight()
		window_width = dialog.winfo_reqwidth()
		window_height = dialog.winfo_reqheight()

		if x + window_width > screen_width:
			x = x - window_width - 24
		if y + window_height > screen_height:
			y = y - window_height - 24

		final_x = min(max(0, x), max(0, screen_width - window_width))
		final_y = min(max(0, y), max(0, screen_height - window_height))
		dialog.geometry(f"+{final_x}+{final_y}")

	def _save_row_edits(self, row_position: int | None, entries: dict[str, tk.Entry], dialog: tk.Toplevel):
		if row_position is None:
			new_row: dict[str, object] = {}
			for column in self._dataframe.columns:
				key = str(column)
				if key in entries:
					text_value = entries[key].get()
					new_row[key] = self._coerce_new_value(text_value, self._dataframe[column].dtype)
				else:
					new_row[key] = pd.NA
			self._dataframe.loc[len(self._dataframe)] = new_row
		else:
			for column_name, entry in entries.items():
				text_value = entry.get()
				previous_value = self._dataframe.at[self._dataframe.index[row_position], column_name]
				column_dtype = self._dataframe[column_name].dtype
				converted_value = self._coerce_value(text_value, previous_value, column_dtype)
				self._dataframe.iat[row_position, self._dataframe.columns.get_loc(column_name)] = converted_value

		dialog.destroy()
		self._render_tabs()

	def _delete_row(self, row_position: int, dialog: tk.Toplevel):
		confirmed = messagebox.askyesno(
			"Delete row",
			f"Delete row {row_position}?",
			parent=dialog,
		)
		if not confirmed:
			return

		self._dataframe = self._dataframe.drop(self._dataframe.index[row_position]).reset_index(drop=True)
		dialog.destroy()
		self._render_tabs()

	def _coerce_value(self, text_value: str, previous_value, dtype):
		text = text_value.strip()

		if pd.api.types.is_bool_dtype(dtype):
			if text == "":
				return previous_value
			return text.lower() in {"1", "true", "yes", "y", "on"}

		if pd.api.types.is_integer_dtype(dtype):
			if text == "":
				return previous_value
			try:
				return int(text)
			except ValueError:
				return previous_value

		if pd.api.types.is_float_dtype(dtype):
			if text == "":
				return previous_value
			try:
				return float(text)
			except ValueError:
				return previous_value

		if pd.api.types.is_datetime64_any_dtype(dtype):
			if text == "":
				return previous_value
			try:
				return pd.to_datetime(text)
			except (TypeError, ValueError):
				return previous_value

		if text == "" and pd.isna(previous_value):
			return pd.NA

		return text_value

	def _coerce_new_value(self, text_value: str, dtype):
		text = text_value.strip()
		if text == "":
			return pd.NA

		if pd.api.types.is_bool_dtype(dtype):
			return text.lower() in {"1", "true", "yes", "y", "on"}

		if pd.api.types.is_integer_dtype(dtype):
			try:
				return int(text)
			except ValueError:
				return pd.NA

		if pd.api.types.is_float_dtype(dtype):
			try:
				return float(text)
			except ValueError:
				return pd.NA

		return text_value

	def _fit_columns_to_width(
		self,
		tree: ttk.Treeview,
		columns: list[str],
		initial_widths: dict[str, int],
		bind_id: str,
	):
		if not tree.winfo_exists() or not columns:
			return

		available_width = tree.winfo_width()
		if available_width <= 1:
			return

		tree.unbind("<Configure>", bind_id)

		current_total = sum(initial_widths[column] for column in columns)
		if current_total >= available_width:
			return

		extra_width = available_width - current_total
		base_extra, remainder = divmod(extra_width, len(columns))

		for index, column in enumerate(columns):
			width = initial_widths[column] + base_extra
			if index < remainder:
				width += 1
			tree.column(column, width=width)


def analyze_data(
	dataframe: pd.DataFrame,
	title: str = "Data Analysis",
	hide_index: bool = False,
	filter: list[str] | None = None,
	rev_filter: list[str] | None = None,
) -> pd.DataFrame:
	if not isinstance(dataframe, pd.DataFrame):
		raise TypeError("analyze_data expects a pandas DataFrame")
	if filter is not None and rev_filter is not None:
		raise ValueError("analyze_data received both filter and rev_filter; use only one")

	window = _DataFrameAnalysisWindow(
		dataframe,
		title=title,
		hide_index=hide_index,
		filter_columns=filter,
		rev_filter_columns=rev_filter,
	)
	window.show()
	return window._dataframe
