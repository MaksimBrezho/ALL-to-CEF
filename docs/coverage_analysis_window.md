<p align="right"><a href="coverage_analysis_window.ru.md">🇷🇺 Русская версия</a></p>

# 📊 Coverage Analysis Window

This dialog shows how well the loaded log is covered by active patterns. It opens from the main window via the **Commands** menu entry **Coverage Analysis**.

## Contents

The window displays:

- Overall character coverage percentage.
- Percentage of lines containing at least one `name` field.
- Percentage of lines containing at least one `severity` field.
- Percentage of lines containing at least one `msg` field.
- Percentage of lines containing at least one `signatureID` field.
- For each metric, line number ranges where the field is missing.

The statistics are displayed in a resizable table with vertical and horizontal
scrollbars that appear as needed. Long lists of missing line numbers are
wrapped onto multiple lines in their column. Use **Copy** to place the table
data on the clipboard. Press **OK** or `Esc` to close the dialog.
