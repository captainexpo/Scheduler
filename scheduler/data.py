from scheduler.student import Student
from scheduler.course import Course
from typing import Any


class RawData:
    students: list[Student]
    courses: list[Course]
    meta: dict[str, Any] = {}

    def __init__(self, students: list[Student], courses: list[Course]) -> None:
        self.students = students
        self.courses = courses
        self.meta = {
            "students": len(students),
            "courses": len(courses),
        }

    def __str__(self) -> str:
        o = ""
        o += "Students:\n"
        for student in self.students:
            o += f"{student.short_str()}\n"
        o += "\nCourses:\n"
        for course in self.courses:
            o += f"{course}\n"
        return o

    def __repr__(self) -> str:
        return self.__str__()
