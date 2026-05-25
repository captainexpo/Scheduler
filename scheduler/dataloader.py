import csv
from datetime import datetime
import os
from typing import Optional
from scheduler.data import RawData
from scheduler.course import Course, CourseType
from scheduler.student import Student

# student fmt = First Name, Last Name, Grade, Pref Class Type, CTE or BTC, Morning Pref 1, Morning Pref 2, Morning Pref 3, Morning Pref 4, Morning Pref 5, Afternoon Pref 1, Afternoon Pref 2, Afternoon Pref 3, Afternoon Pref 4, Afternoon Pref 5, Full Pref 1, Full Pref 2, Full Pref 3, Full Pref 4, Full Pref 5
# course fmt = Name, Teacher, Capacity, Type

courses: dict[str, Course] = {}


def load_course(row: list[str]) -> Course:
    name = row[0]
    teacher = row[1]
    capacity = int(row[2])
    course_type = CourseType[row[3].upper()]
    return Course(name, teacher, capacity, course_type)


def remove_pref_duplicates(prefs: list[Course]) -> list[Course]:
    seen = set()
    unique_prefs = []
    for pref in prefs:
        if pref not in seen:
            seen.add(pref)
            unique_prefs.append(pref)
    return unique_prefs


def parse_course_type_pref(pref: str) -> CourseType:
    if "Half" in pref:
        return CourseType.HALF
    elif "Full" in pref:
        return CourseType.FULL
    else:
        return CourseType.HALF


# (first_name, last_name, grade) -> (student, timestamp)
students_actual: dict[tuple[str, str, str], tuple[Student, datetime]] = {}


def load_student(format: list[str], row: list[str]) -> Optional[Student]:
    timestamp = datetime.strptime(row[0], "%m/%d/%Y %H:%M:%S")  # google forms timestamp

    # row = row[1:]
    first_name = row[format.index("First Name")]
    last_name = row[format.index("Last Name")]
    grade = row[format.index("Grade")]
    email = row[format.index("Email")]

    if (first_name, last_name, grade) in students_actual:
        print(f"Duplicate {first_name} {last_name} grade {grade}")
        _, existing_timestamp = students_actual[(first_name, last_name, grade)]
        if timestamp <= existing_timestamp:
            return None

    course_type_pref = row[format.index("Pref Class Type")]
    btc_cte_time = row[format.index("CTE or BTC")]
    available_times = (btc_cte_time != "Morning", btc_cte_time != "Afternoon")
    morning_prefs = row[format.index("Morning Pref 1"):format.index("Morning Pref 5") + 1]
    afternoon_prefs = row[format.index("Afternoon Pref 1"):format.index("Afternoon Pref 5") + 1]
    full_prefs = row[format.index("Full Pref 1"):format.index("Full Pref 5") + 1]

    flex_pref_str = row[format.index("Flex Pref")]
    flex_pref = CourseType.NO_PREFERENCE
    if flex_pref_str == "Half":
        flex_pref = CourseType.HALF
    elif flex_pref_str == "Full":
        flex_pref = CourseType.FULL
    else:
        flex_pref = CourseType.NO_PREFERENCE


    prefs = {
        CourseType.MORNING: remove_pref_duplicates(
            [courses[i] for i in morning_prefs if i != ""]
        ),
        CourseType.AFTERNOON: remove_pref_duplicates(
            [courses[i] for i in afternoon_prefs if i != ""]
        ),
        CourseType.FULL: remove_pref_duplicates(
            [courses[i] for i in full_prefs if i != ""]
        ),
    }

    student = Student(
        first_name,
        last_name,
        grade,
        email,
        CourseType[course_type_pref.replace(" ", "_").upper()],
        available_times,
        prefs,
        flex_pref,
    )

    students_actual[(first_name, last_name, grade)] = (student, timestamp)

    return student


def load_data(student_csv: str, classes_csv: str) -> RawData:
    courses.clear()
    students_actual.clear()

    student_format = (
        open(
            os.path.join(os.path.dirname(__file__), "../fmts/student_format.txt"),
            "r",
        )
        .read()
        .split("\n")
    )

    students: list[Student] = []
    _courses: list[Course] = []
    with open(classes_csv, "r") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            course = load_course(row)
            _courses.append(course)
            courses[course.name] = course

    with open(student_csv, "r") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            _ = load_student(
                student_format,
                row
            )  # we only care about the latest submission for each student, so we can ignore the return value for now

    print(len(students_actual), "students loaded")
    for student, _ in students_actual.values():
        students.append(student)

    d = RawData(students, _courses)
    return d


if __name__ == "__main__":
    import sys

    student_csv = sys.argv[1]
    classes_csv = sys.argv[2]
    data: RawData = load_data(student_csv, classes_csv)
    print(data.as_text_output(format="csv"))
