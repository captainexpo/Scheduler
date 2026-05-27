# Scheduler

A small scheduling tool for assigning students to classes using an LP-based optimizer.

**Highlights**
- CLI scheduler that reads student and class CSVs and produces a scheduled CSV (and optional JSON).
- Lightweight Flask web UI for uploading CSVs and previewing results.

## Requirements
- Python 3.12 or newer
- Dependencies are declared in `pyproject.toml`: `faker`, `flask`, `pandas`, `pulp`.

## Installation
1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install the package (from project root):

```bash
python -m pip install .
```

Or install dependencies directly:

```bash
python -m pip install faker flask pandas pulp
```

## Project layout
- `scheduler/` — core package with CLI and web app (`main.py`, `web.py`, loaders, models, sorter).
- `faker/` — `class_faker.py` and `student_faker.py` to generate sample CSV files.
- `fmts/` — example CSV formats for classes and students.
- `data/` — example datasets used in development.

## CLI Usage
The CLI entry point is `scheduler.main`. From the project root run:

```bash
python -m scheduler.main path/to/classes.csv path/to/students.csv --output out.csv
```

Notes:
- The CLI expects the first positional argument to be the classes file and the second to be the students file.
- Use `--output-json` to also write a JSON file alongside the CSV.
- Tweak LP options with `--preference-objective-weight` and `--grade-balance-objective-weight`.

Example:

```bash
python -m scheduler.main data/real_classes.csv data/real_students.csv --output scheduled.csv --output-json
```

## Web UI
Run the Flask app for a simple browser interface:

```bash
python -m scheduler.web
```

Then open `http://127.0.0.1:8000` and upload your classes and students CSV files.

## Output
- CSV: a flattened CSV with assigned classes for each student (default `out.csv` if not specified).
- JSON: when `--output-json` is set the JSON is written next to the CSV with the same base name.