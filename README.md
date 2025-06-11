<p align="right"><a href="README.ru.md">🇷🇺 Русская версия</a></p>

<p align="center">
  <img src="icon/ALLtoCEF.png" alt="ALL to CEF icon" width="200">
</p>

<h1 align="center">ALL to CEF</h1>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue?logo=python">
  <img alt="License" src="https://img.shields.io/badge/license-Non--commercial-lightgrey">
</p>

ALL to CEF is a collection of utilities and a desktop GUI for
experimenting with log formats. It lets you build regular expressions,
highlight log files, and generate code that converts logs to the CEF
(Common Event Format).

## Features

- 🖥️ **Tkinter GUI** for viewing logs and toggling regex patterns.
- 🧙 **Pattern Wizard** builds draft regular expressions from selected
  log lines with controls for numbers, case sensitivity and prefix merging.
- 📚 **Built‑in patterns** for common timestamps and messages plus
  user‑defined extensions.
- 🎨 **Coverage highlighting** shows which parts of the log are matched
  and calculates the percentage of covered characters.
- 📊 **Coverage analysis** lists lines missing key CEF fields and overall coverage statistics.
- 🛠️ **Code generator** produces a Python converter for CEF with
  transformations, replacements, token reordering and incremental counters.
- 🗂️ **Sample logs** in `data/sample_logs` for quick experimentation.

## Installation

1. Ensure Python 3.11 or newer is available.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

If the environment lacks internet access, preinstall the packages from
`requirements.txt` into a virtual environment and reuse it.

## Running the application

Launch the GUI with:

```bash
python main.py
```

Open a log file from the **Commands** menu, select lines and run the
**Create Pattern** wizard to build new patterns. Use **Save Patterns** from
the same menu to store per‑log patterns, or choose **Code Generator** to
produce a CEF converter.

## Building an installer

To produce a standalone executable you need [PyInstaller](https://pyinstaller.org).
Install it and run the helper script:

```bash
pip install pyinstaller
python build_installer.py
```

The resulting installer binary `ALLtoCEF` will be placed in the `dist`
directory and will use the icon from `icon/ALLtoCEF.png`. The helper script
also bundles this icon together with the required built-in pattern, CEF and
translation data files.

## Running the tests

The repository includes an extensive test suite. Execute it with:

```bash
pytest -q
```

All tests should pass after the dependencies are installed.

## Transformations

When defining mapping rules for the code generator, several helper
transformations are supported:

- `lower`, `upper`, `capitalize`, `sentence`
- `time` – detects many common date/time formats via `python-dateutil`
  and converts them to `YYYY-MM-DDTHH:MM:SSZ`.

Transformations can also specify token reordering, value replacement and
value maps. See `utils/transform_logic.py` for full details.
Mappings created automatically for CEF fields of the `Time` category
use this transformation by default.

## Project structure

```
core/   – regex builder, tokenizer and highlighting logic
utils/  – JSON helpers, color utilities and the code generator
gui/    – Tkinter user interface modules
data/   – built‑in patterns, CEF field definitions and sample logs
```

## Documentation

Detailed explanations of each window and tool are available in the
[docs](docs/) directory.

## UML Diagrams

Automatically generated class and package diagrams are in [docs/uml](docs/uml).

## Citation

Log examples used in this project come from the [loghub](https://github.com/logpai/loghub) repository. This project uses the following work:

Jieming Zhu, Shilin He, Pinjia He, Jinyang Liu, Michael R. Lyu. [Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics](https://arxiv.org/abs/2008.06448). IEEE International Symposium on Software Reliability Engineering (ISSRE), 2023.

## License

This project is licensed under the [Non-commercial License](LICENSE).
