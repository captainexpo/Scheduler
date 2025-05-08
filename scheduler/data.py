from dataclasses import dataclass
from scheduler.student import Student
from scheduler.course import Course


@dataclass
class RawData:
    students: list[Student]
    courses: list[Course]

    def __str__(self) -> str:
        o = ""
        o += "Students:\n"
        for student in self.students:
            o += f"{student}\n"
        o += "\nCourses:\n"
        for course in self.courses:
            o += f"{course}\n"
        return o

    def __repr__(self) -> str:
        return self.__str__()
