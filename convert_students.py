#!/usr/bin/env python3
"""
Helper script to convert real_students.csv from Google Form format
to the expected format for the scheduler.
"""

import csv
import re
from pathlib import Path


def clean_grade(grade_str: str) -> str:
    """Extract numeric grade from strings like '10th', '11th', '9th'."""
    match = re.search(r'\d+', grade_str)
    return match.group() if match else grade_str


def parse_preference_type(pref_str: str) -> str:
    """Map Google Form preference type to expected format."""
    if not pref_str or pref_str.strip() == "":
        return "Half"

    pref_lower = pref_str.lower()

    if "full day" in pref_lower:
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


def parse_btc_cte(advisory_text: str) -> str:
    """Extract BTC/CTE time from advisory teacher field or similar.

    Returns 'Morning', 'Afternoon', or 'None'.
    """
    if not advisory_text or advisory_text.strip() == "":
        return "None"

    text_lower = advisory_text.lower()

    if "morning" in text_lower and "btc" in text_lower:
        return "Morning"
    elif "afternoon" in text_lower and "btc" in text_lower:
        return "Afternoon"
    elif "morning" in text_lower and "cte" in text_lower:
        return "Morning"
    elif "afternoon" in text_lower and "cte" in text_lower:
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

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader)

        for row in reader:
            # Extract fields from Google Form format
            # Columns: Timestamp, Email, Last Name, First Name, Current Grade, Advisory Teacher,
            #          Preference Type, Full Day 1-5, spacer, Morning 1-5, spacer, Afternoon 1-5

            first_name = row[3].strip() if len(row) > 3 else ""
            last_name = row[2].strip() if len(row) > 2 else ""
            grade = clean_grade(row[4]) if len(row) > 4 else ""
            pref_type = parse_preference_type(row[6]) if len(row) > 6 else "Half"

            # Parse BTC/CTE time from the "I attend a X BTC/CTE" pattern
            btc_cte_text = row[6] if len(row) > 6 else ""  # Use preference type column
            btc_cte_time = parse_btc_cte(btc_cte_text)

            # Full day preferences (cols 7-11)
            full_prefs = [row[i].strip() for i in range(7, 12) if len(row) > i]
            full_prefs = [p for p in full_prefs if p and not is_comment_row(p)]

            # Morning preferences (cols 14-18) - skip col 12 and 13 which are separators
            # Empty if student has morning BTC/CTE
            if btc_cte_time == "Morning":
                morning_prefs = []
            else:
                morning_prefs = [row[i].strip() for i in range(14, 19) if len(row) > i]
                morning_prefs = [p for p in morning_prefs if p and not is_comment_row(p)]

            # Afternoon preferences (cols 21-25) - skip col 19 and 20 which are separators
            # Empty if student has afternoon BTC/CTE
            if btc_cte_time == "Afternoon":
                afternoon_prefs = []
            else:
                afternoon_prefs = [row[i].strip() for i in range(21, 26) if len(row) > i]
                afternoon_prefs = [p for p in afternoon_prefs if p and not is_comment_row(p)]

            # Pad with empty strings to match 5 slots
            while len(morning_prefs) < 5:
                morning_prefs.append("")
            while len(afternoon_prefs) < 5:
                afternoon_prefs.append("")
            while len(full_prefs) < 5:
                full_prefs.append("")

            # Build output row
            out_row = [
                first_name,
                last_name,
                grade,
                pref_type,
                btc_cte_time,  # "Morning", "Afternoon", or "None"
            ] + morning_prefs[:5] + afternoon_prefs[:5] + full_prefs[:5]

            rows_out.append(out_row)

    # Write output
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "First Name", "Last Name", "Grade", "Pref Class Type", "CTE or BTC",
            "Morning Pref 1", "Morning Pref 2", "Morning Pref 3", "Morning Pref 4", "Morning Pref 5",
            "Afternoon Pref 1", "Afternoon Pref 2", "Afternoon Pref 3", "Afternoon Pref 4", "Afternoon Pref 5",
            "Full Pref 1", "Full Pref 2", "Full Pref 3", "Full Pref 4", "Full Pref 5",
        ])
        writer.writerows(rows_out)

    print(f"✓ Converted {len(rows_out)} students")
    print(f"✓ Output written to {output_path}")


if __name__ == "__main__":
    import sys
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    convert_csv(input_file, output_file)
