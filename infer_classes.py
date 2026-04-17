#!/usr/bin/env python3
"""
Parses a student course preference CSV and outputs a deduplicated list of classes.

Usage:
    python parse_classes.py input.csv [output.csv]

If output.csv is omitted, results are printed to stdout.
"""

import csv
import sys
from collections import OrderedDict

FULL_DAY_COLS  = [7, 8, 9, 10, 11]   # "My FIRST–FIFTH choice for a full day class"
MORNING_COLS   = [13, 14, 15, 16, 17] # "My FIRST–FIFTH choice for a MORNING class"
AFTERNOON_COLS = [19, 20, 21, 22, 23] # "My FIRST–FIFTH choice for an AFTERNOON class"

CAPACITY = 20

SECTIONS = [
    ("Full",   FULL_DAY_COLS),
    ("Morning",    MORNING_COLS),
    ("Afternoon",  AFTERNOON_COLS),
]


def parse_classes(input_path: str) -> list[dict]:
    """
    Read the preference CSV and return a deduplicated list of class dicts.
    Key is (name, type) so the same course offered in different session types
    is treated as a distinct entry.
    """
    seen: dict[tuple[str, str], dict] = OrderedDict()

    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)  # skip header row

        for row in reader:
            if not any(row):  # skip blank rows
                continue

            for session_type, cols in SECTIONS:
                for col in cols:
                    if col >= len(row):
                        continue
                    name = row[col].strip()
                    if not name:
                        continue

                    key = (name, session_type)
                    if key not in seen:
                        seen[key] = {
                            "Name":     name,
                            "Teacher":  "",        # not present in source data
                            "Capacity": CAPACITY,
                            "Type":     session_type,
                        }

    return list(seen.values())


def write_classes(classes: list[dict], output_path: str | None) -> None:
    fieldnames = ["Name", "Teacher", "Capacity", "Type"]

    if output_path:
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(classes)
        print(f"Wrote {len(classes)} classes to {output_path}", file=sys.stderr)
    else:
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(classes)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} input.csv [output.csv]", file=sys.stderr)
        sys.exit(1)

    input_path  = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None

    classes = parse_classes(input_path)
    write_classes(classes, output_path)


if __name__ == "__main__":
    main()
