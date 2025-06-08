<p align="right"><a href="main_window.ru.md">🇷🇺 Русская версия</a></p>

# 🖥️ ALL to CEF Main Window

This document describes the purpose and elements of the application's main window.

## Overview

The window is created in `main.py` as an instance of `tk.Tk` with an embedded [`AppWindow`](../gui/app_window.py) widget that fills the available space. Its minimum size is 1000×700 pixels and the title is *"ALL to CEF"*.

All content is split into two areas:

1. **Log viewer** — occupies most of the window and contains a text widget with both horizontal and vertical scrollbars.
2. **Pattern panel** — located on the right and shows the list of available regular expressions with enable/disable toggles.

A control panel with buttons and status indicators sits below these areas.

## Interface Elements

### Log viewer

- `self.text_area` — the `tk.Text` widget that displays the current log lines.
- Horizontal (`x_scroll`) and vertical (`y_scroll`) scrollbars connected to the text widget.
- When hovering over highlighted fragments, a tooltip (`ToolTip`) appears if multiple patterns matched that spot.
- Text highlighting is applied via `apply_highlighting`, coloring matches according to their categories.

### Pattern panel

- Created via [`PatternPanel`](../gui/pattern_panel.py) and placed to the right of the text area.
- Each row contains a checkbox with the pattern name and a color indicator for its category.
- Patterns are grouped by category to visually separate rule types.
- Toggling a checkbox immediately updates highlighting in the viewer.

### Menu bar

- Contains a **Commands** menu with file and tool actions.
- Includes a **Language** menu for switching between English and Russian.

### Control panel

Located under the text area and includes:

| Element | Purpose |
|---------|---------|
| **Commands ▾** | Drop-down with **Load Log** (`Ctrl+O`), **Save Patterns** (`Ctrl+S`), **Code Generator** (`Ctrl+G`), **Coverage Analysis** (`Ctrl+L`) and **Edit User Patterns** (`Ctrl+U`). |
| **← Prev** / **Next →** | Switch pages when viewing logs page by page (`Alt+Left`/`Alt+Right`). |
| `Lines per page` | Input/spin box for the number of lines per page. |
| **Page X of Y** | Shows the current page and total pages. |
| **Coverage** | Displays the percentage of characters covered by active patterns. |
| **Create Pattern** | Launches the wizard for creating a new pattern from selected lines (`Ctrl+N`). |

## Behavior

- After a file is loaded, each line is processed by active patterns and the results are cached in `self.match_cache`.
- When the page or pattern set changes, `render_page()` redraws the visible content and recalculates the coverage.
- `get_selected_lines()` returns the selected fragments along with their full lines, used by the pattern wizard.
- `save_current_patterns()` lets you name the pattern set and optionally assign CEF fields before saving.

## Data Used

- Global and user patterns are loaded from JSON files via utilities in `utils/json_utils.py`.
- CEF field information is used by the pattern panel and the save dialog.

## Related Dialogs

The main window can open three additional dialogs:

1. **Pattern Wizard** (`PatternWizardDialog`) — interactive wizard for creating regular expressions.
2. **Code Generator Dialog** (`CodeGeneratorDialog`) — interface for configuring log-to-CEF conversion rules and generating Python code.
3. **Coverage Analysis Dialog** (`CoverageAnalysisDialog`) — shows overall coverage and which lines lack required CEF fields.

## Summary

The `ALL to CEF` main window combines the log viewer, pattern management and tools for creating and saving patterns. It serves as the central point of the application and provides access to all primary log-processing features.

