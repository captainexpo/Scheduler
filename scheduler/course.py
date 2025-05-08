from enum import Enum
from scheduler.student import Student


class CourseType(Enum):
    MORNING = -2
    AFTERNOON = -1
    HALF = 0
    FULL = 1


class Course:
    name: str
    teacher: str
    capacity: int
    type: CourseType
    students: list["Student"]

    def __init__(
        self,
        name: str,
        teacher: str,
        capacity: int,
        course_type: CourseType,
    ) -> None:
        self.name = name
        self.teacher = teacher
        self.capacity = capacity
        self.type = course_type
        self.students = []

    def is_full_day(self) -> bool:
        return self.type == CourseType.FULL

    def num_students(self) -> int:
        return len(self.students)

    def is_over_capacity(self) -> bool:
        return len(self.students) >= self.capacity

    def add_student(self, student: Student) -> bool:
        self.students.append(student)
        return True

    def remove_student(self, student: Student) -> bool:
        self.students.remove(student)
        return True

    def __str__(self) -> str:
        return f"""{self.name}({self.teacher}){{
            Type: {self.type.name},
            Capacity: {self.capacity},
            Students: {len(self.students)}/{self.capacity},
            Student List: {[student.first_name + " " + student.last_name for student in self.students]}
}}"""
