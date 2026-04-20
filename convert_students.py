#!/usr/bin/env python3
"""
Helper script to convert real_students.csv from Google Form format
to the expected format for the scheduler.
"""

import csv
import re


def clean_grade(grade_str: str) -> str:
    """Extract numeric grade from strings like '10th', '11th', '9th'."""
    match = re.search(r"\d+", grade_str)
    return match.group() if match else grade_str


def parse_preference_type(pref_str: str) -> str:
    """Map Google Form preference type to expected format."""
    if not pref_str or pref_str.strip() == "":
        return "Half"

    pref_lower = pref_str.lower()

    if "no preference" in pref_lower:
        return "No Preference"
    elif "full day" in pref_lower:
        return "Full"
    elif "half day" in pref_lower:
        return "Half"
    elif "morning" in pref_lower and "afternoon" in pref_lower:
        return "Half"
    elif "morning" in pref_lower:
        return "Morning"
    elif "afternoon" in pref_lower:
        return "Afternoon"
    else:
        return "Half"


def parse_btc_cte(text: str) -> str:
    """Extract BTC/CTE time from advisory teacher field or similar.

    Returns 'Morning', 'Afternoon', or 'None'.
    """
    if not text or text.strip() == "":
        return "None"

    if text in ("I attend a MORNING BTC course, so I will only be enrolling in an AFTERNOON YES class.",
                "I am enrolled in a morning BTC class"
    ):
        return "Morning"
    if text in (
        "I attend a AFTERNOON BTC course, so I will only be enrolling in a MORNING YES class.",
        "I have an afternoon BTC class.  I am ready to submit."
    ):
        return "Afternoon"

    return "None"


def is_comment_row(value: str) -> bool:
    """Check if this is a meta-comment rather than a course name."""
    if not value or value.strip() == "":
        return True

    comments = [
        "I prefer",
        "I am ready",
        "I am enrolled",
    ]

    return any(comment.lower() in value.lower() for comment in comments)


def convert_csv(input_path: str, output_path: str) -> None:
    """Convert Google Form CSV to scheduler format."""

    rows_out = []
    fieldnames = [
        "Timestamp",
        "First Name",
        "Last Name",
        "Grade",
        "Pref Class Type",
        "CTE or BTC",
        "Morning Pref 1",
        "Morning Pref 2",
        "Morning Pref 3",
        "Morning Pref 4",
        "Morning Pref 5",
        "Afternoon Pref 1",
        "Afternoon Pref 2",
        "Afternoon Pref 3",
        "Afternoon Pref 4",
        "Afternoon Pref 5",
        "Full Pref 1",
        "Full Pref 2",
        "Full Pref 3",
        "Full Pref 4",
        "Full Pref 5",
    ]

    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        def get_value(row: dict[str, str], *keys: str) -> str:
            for key in keys:
                value = row.get(key, "")
                if value and value.strip():
                    return value.strip()
            return ""

        def collect_values(row: dict[str, str], keys: list[str]) -> list[str]:
            values: list[str] = []
            for key in keys:
                value = get_value(row, key)
                if value and not is_comment_row(value):
                    values.append(value)
            return values

        def extract_btc_cte(row: dict[str, str]) -> str:
            for value in row.values():
                parsed = parse_btc_cte(value)
                if parsed != "None":
                    return parsed
            return "None"

        morning_keys = [
            "Morning Pref 1",
            "Morning Pref 2",
            "Morning Pref 3",
            "Morning Pref 4",
            "Morning Pref 5",
            "My FIRST choice for a MORNING class is",
            "My SECOND choice for a MORNING class is",
            "My THIRD choice for a MORNING class is",
            "My FOURTH choice for a MORNING class is",
            "My FIFTH choice for a MORNING class is",
        ]
        afternoon_keys = [
            "Afternoon Pref 1",
            "Afternoon Pref 2",
            "Afternoon Pref 3",
            "Afternoon Pref 4",
            "Afternoon Pref 5",
            "My FIRST choice for an AFTERNOON class is",
            "My SECOND choice for an AFTERNOON class is",
            "My THIRD choice for an AFTERNOON class is",
            "My FOURTH choice for an AFTERNOON class is",
            "My FIFTH choice for an AFTERNOON class is",
        ]
        full_keys = [
            "Full Pref 1",
            "Full Pref 2",
            "Full Pref 3",
            "Full Pref 4",
            "Full Pref 5",
            "My FIRST choice for a full day class is",
            "My SECOND choice for a full day class is",
            "My THIRD choice for a full day class is",
            "My FOURTH choice for a full day class is",
            "My FIFTH choice for a full day class is",
        ]

        for row in reader:
            # Extract fields from Google Form format and preserve the output schema
            timestamp = get_value(row, "Timestamp")
            first_name = get_value(row, "First Name")
            last_name = get_value(row, "Last Name")
            grade = clean_grade(get_value(row, "Grade", "Current Grade"))
            pref_type = parse_preference_type(
                get_value(
                    row,
                    "Pref Class Type",
                    "Please identify if you prefer a full day or half day",
                    "Please identify if you prefer a full day or half day class",
                )
            )

            btc_cte_time = extract_btc_cte(row)

            full_prefs = collect_values(row, full_keys)
            morning_prefs = collect_values(row, morning_keys)
            afternoon_prefs = collect_values(row, afternoon_keys)

            # Pad with empty strings to match 5 slots
            while len(morning_prefs) < 5:
                morning_prefs.append("")
            while len(afternoon_prefs) < 5:
                afternoon_prefs.append("")
            while len(full_prefs) < 5:
                full_prefs.append("")

            # Build output row
            out_row = {
                "Timestamp": timestamp,
                "First Name": first_name,
                "Last Name": last_name,
                "Grade": grade,
                "Pref Class Type": pref_type,
                "CTE or BTC": btc_cte_time,
                "Morning Pref 1": morning_prefs[0],
                "Morning Pref 2": morning_prefs[1],
                "Morning Pref 3": morning_prefs[2],
                "Morning Pref 4": morning_prefs[3],
                "Morning Pref 5": morning_prefs[4],
                "Afternoon Pref 1": afternoon_prefs[0],
                "Afternoon Pref 2": afternoon_prefs[1],
                "Afternoon Pref 3": afternoon_prefs[2],
                "Afternoon Pref 4": afternoon_prefs[3],
                "Afternoon Pref 5": afternoon_prefs[4],
                "Full Pref 1": full_prefs[0],
                "Full Pref 2": full_prefs[1],
                "Full Pref 3": full_prefs[2],
                "Full Pref 4": full_prefs[3],
                "Full Pref 5": full_prefs[4],
            }

            rows_out.append(out_row)

    # Write output
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)

    print(f"✓ Converted {len(rows_out)} students")
    print(f"✓ Output written to {output_path}")


if __name__ == "__main__":
    import sys

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    convert_csv(input_file, output_file)
