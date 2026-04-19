#!/usr/bin/env python3
"""Validate LP scheduling output against core invariants.

Usage:
    uv run python verify_lp_solution.py classes.csv students.csv
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

import scheduler.dataloader as dataloader
from scheduler.course import Course, CourseType
from scheduler.lp_sorter import LPSorter
from scheduler.student import Student


@dataclass
class ValidationResult:
    ok: bool
    messages: list[str]


def is_no_preference_valid(student: Student) -> bool:
    has_full = student.full_course is not None
    has_half = student.half_courses[0] is not None or student.half_courses[1] is not None
    return not (has_full and has_half)


def is_student_unsorted(student: Student) -> bool:
    if student.course_type_pref == CourseType.FULL:
        return student.full_course is None

    if student.course_type_pref == CourseType.HALF:
        return (
            (student.available_times[0] and student.half_courses[0] is None)
            or (student.available_times[1] and student.half_courses[1] is None)
        )

    # NO_PREFERENCE: full assignment is acceptable; otherwise evaluate needed half slots.
    if student.full_course is not None:
        return False
    return (
        (student.available_times[0] and student.half_courses[0] is None)
        or (student.available_times[1] and student.half_courses[1] is None)
    )


def validate_solution(courses: list[Course], students: list[Student], meta: dict) -> ValidationResult:
    messages: list[str] = []

    over_capacity = [
        c for c in courses if c.name != "Unsorted" and c.num_students() > c.capacity
    ]
    if over_capacity:
        messages.append(
            "Over-capacity classes: "
            + ", ".join(f"{c.name} ({c.num_students()}/{c.capacity})" for c in over_capacity)
        )

    wrong_full_type = [
        s
        for s in students
        if s.full_course is not None and s.full_course.type != CourseType.FULL
    ]
    if wrong_full_type:
        messages.append(
            f"{len(wrong_full_type)} students have non-FULL courses in full slot."
        )

    wrong_morning_type = [
        s
        for s in students
        if s.half_courses[0] is not None and s.half_courses[0].type != CourseType.MORNING
    ]
    if wrong_morning_type:
        messages.append(
            f"{len(wrong_morning_type)} students have non-MORNING course in morning slot."
        )

    wrong_afternoon_type = [
        s
        for s in students
        if s.half_courses[1] is not None and s.half_courses[1].type != CourseType.AFTERNOON
    ]
    if wrong_afternoon_type:
        messages.append(
            f"{len(wrong_afternoon_type)} students have non-AFTERNOON course in afternoon slot."
        )

    np_invalid = [
        s for s in students if s.course_type_pref == CourseType.NO_PREFERENCE and not is_no_preference_valid(s)
    ]
    if np_invalid:
        messages.append(
            f"{len(np_invalid)} No Preference students were assigned both full and half-day modes."
        )

    full_missing = sum(
        1
        for s in students
        if s.course_type_pref == CourseType.FULL and s.full_course is None
    )
    half_missing_slots = sum(
        (1 if s.available_times[0] and s.half_courses[0] is None else 0)
        + (1 if s.available_times[1] and s.half_courses[1] is None else 0)
        for s in students
        if s.course_type_pref == CourseType.HALF
    )

    # For No Preference, assignment state does not uniquely identify whether
    # the model chose full-day mode unsorted or half-day mode unsorted.
    # Keep these as lower-bound checks only.
    np_missing_half_slots = 0
    for s in students:
        if s.course_type_pref != CourseType.NO_PREFERENCE:
            continue
        if s.full_course is not None:
            continue
        # No full assignment implies half-day mode (or unsorted fallback), count missing slots.
        np_missing_half_slots += 1 if s.available_times[0] and s.half_courses[0] is None else 0
        np_missing_half_slots += 1 if s.available_times[1] and s.half_courses[1] is None else 0

    recomputed_unsorted_students = sum(1 for s in students if is_student_unsorted(s))

    meta_unsorted = meta.get("unsorted")
    meta_unsorted_full = meta.get("unsorted_full_students")
    meta_unsorted_half = meta.get("unsorted_half_slots")

    if isinstance(meta_unsorted_full, int) and meta_unsorted_full < full_missing:
        messages.append(
            "Meta mismatch: unsorted_full_students="
            f"{meta_unsorted_full}, minimum expected {full_missing}."
        )

    if isinstance(meta_unsorted_half, int) and meta_unsorted_half < half_missing_slots:
        messages.append(
            "Meta mismatch: unsorted_half_slots="
            f"{meta_unsorted_half}, minimum expected {half_missing_slots}."
        )

    if (
        isinstance(meta_unsorted_full, int)
        and isinstance(meta_unsorted_half, int)
        and (meta_unsorted_full + meta_unsorted_half) < (full_missing + half_missing_slots)
    ):
        messages.append(
            "Meta mismatch: unsorted_full_students + unsorted_half_slots="
            f"{meta_unsorted_full + meta_unsorted_half}, "
            f"minimum expected {full_missing + half_missing_slots}."
        )

    if isinstance(meta_unsorted, int) and meta_unsorted != recomputed_unsorted_students:
        messages.append(
            f"Meta mismatch: unsorted={meta_unsorted}, expected {recomputed_unsorted_students}."
        )

    summary = (
        "Summary: "
        f"students={len(students)}, courses={len(courses)}, "
        f"over_capacity={len(over_capacity)}, "
        f"unsorted_students={recomputed_unsorted_students}, "
        f"unsorted_full={full_missing}, "
        f"unsorted_half_slots={half_missing_slots + np_missing_half_slots}."
    )
    messages.insert(0, summary)

    return ValidationResult(ok=len(messages) == 1, messages=messages)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate LP scheduler solution invariants.")
    parser.add_argument("classes", help="Path to classes CSV")
    parser.add_argument("students", help="Path to students CSV")
    args = parser.parse_args()

    raw_data = dataloader.load_data(args.students, args.classes)
    sorter = LPSorter()
    sorter.sort(raw_data)
    solved = sorter.get_raw_data()

    result = validate_solution(solved.courses, solved.students, solved.meta)
    for line in result.messages:
        print(line)

    if result.ok:
        print("VALID: all checks passed")
        return 0

    print("INVALID: one or more checks failed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
