from enum import Enum
from scheduler.student import Student
import logging


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
    students: set["Student"]

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
        self.students = set()

    def is_full_day(self) -> bool:
        return self.type == CourseType.FULL

    def num_students(self) -> int:
        return len(self.students)

    def is_over_capacity(self) -> bool:
        return len(self.students) > self.capacity

    def add_student(self, student: Student) -> bool:
        # if student in self.students:
        #    logging.warning(
        #        f"Warning: {student} is already in {self.name}({self.teacher})"
        #    )
        #    return False
        self.students.add(student)

        logging.debug(f"Added student {student} to {self.name}({self.teacher})")
        return True

    def remove_student(self, student: Student) -> bool:
        if student not in self.students:
            logging.warning(
                f"Warning: {student} not found in {self.name}({self.teacher})"
            )
            return False
        self.students.remove(student)
        logging.debug(f"Removed student {student} from {self.name}({self.teacher})")
        return True

    def sort_by_preference_position(self) -> list:
        l = list(self.students)
        l.sort(key=lambda student: student.prefs[self.type].index(self))
        return l

    def __str__(self) -> str:
        return f"""{self.name}({self.teacher}){{
            Type: {self.type.name},
            Capacity: {self.capacity},
            Students: {len(self.students)}/{self.capacity},
            Student List: {", ".join([student.short_str() for student in self.students])}
}}"""

    def short_str(self) -> str:
        return f"{self.name}({self.teacher}){self.type.name}"

    def __repr__(self) -> str:
        return f"{self.name}({self.teacher}){self.type.name}"
