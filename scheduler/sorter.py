from scheduler.data import RawData
from scheduler.course import Course, CourseType
from scheduler.student import Student
import logging
from typing import Union

logging.basicConfig(level=logging.CRITICAL)


class Sorter:
    def __init__(self):
        self.students: list[Student] = []
        self.courses: list[Course] = []
        self.unsorted_class: Course = Course(
            "Unsorted", "Unsorted", 999999, CourseType.FULL
        )
        self.student_pref_positions: dict[Student, Union[int, list[int]]] = {}

    def move_student_if_needed(self, student: Student) -> None:
        if student.course_type_pref == CourseType.FULL:
            if student.full_course.is_over_capacity():
                self.move_student_to_next(student)
        else:
            if (
                student.available_times[0]
                and student.half_courses[0].is_over_capacity()
            ):
                student.half_courses[0].remove_student(student)
                student.half_courses[0] = None
                self.move_student_to_next(student, 0)
            if (
                student.available_times[1]
                and student.half_courses[1].is_over_capacity()
            ):
                student.half_courses[1].remove_student(student)
                student.half_courses[1] = None
                self.move_student_to_next(student, 1)

    def move_student_to_next(self, student: Student, time: int = -1) -> None:
        logging.debug(
            f"Moving student {student.last_name} to pref {self.student_pref_positions.get(student)}."
        )

        if time == -1:
            student.remove_courses()

        if student.course_type_pref == CourseType.FULL:
            self._move_full_day_student(student)
        else:
            self._move_half_day_student(student, time)

    def _move_full_day_student(self, student: Student) -> None:
        prefs = student.prefs.get(CourseType.FULL, [])
        current_index = self.student_pref_positions.get(student, -1) + 1
        if current_index >= len(prefs):
            logging.debug(
                f"Student {student.last_name} moved to unsorted class (FULL)."
            )
            self.unsorted_class.add_student(student)
            self.student_pref_positions[student] = current_index
            return

        course = prefs[current_index]
        course.add_student(student)
        student.add_course_full(course)
        self.student_pref_positions[student] = current_index
        logging.debug(f"Student {student.last_name} added to course {course.name}.")

    def _move_half_day_student(self, student: Student, t: int = -1) -> None:
        if isinstance(self.student_pref_positions[student], list) is False:
            logging.warning(
                f"Invalid student_pref_positions type for {student.last_name}"
            )
            self.unsorted_class.add_student(student)
            return

        positions = self.student_pref_positions[student]
        if not isinstance(positions, list) or len(positions) != 2:
            logging.warning(
                f"Malformed preference positions for student {student.last_name}"
            )
            self.unsorted_class.add_student(student)
            return

        updated = self._assign_half_day_courses(student, positions, t)

        if not updated:
            logging.debug(
                f"Student {student.last_name} moved to unsorted class (HALF)."
            )
            self.unsorted_class.add_student(student)

    def _assign_half_day_courses(
        self, student: Student, positions: list[int], t: int = -1
    ) -> bool:
        updated = False
        for i, time in enumerate(["MORNING", "AFTERNOON"]):
            if t == 0 and i == 1:
                continue
            if t == 1 and i == 0:
                continue
            if student.available_times[i]:
                prefs = student.prefs.get(getattr(CourseType, time), [])
                if not prefs:
                    continue

                pos = positions[i] + 1
                if pos >= len(prefs):
                    continue

                course = prefs[pos]
                course.add_student(student)

                if time == "MORNING":
                    student.add_course_morning(course)
                else:
                    student.add_course_afternoon(course)

                positions[i] = pos
                updated = True

        return updated

    def sort(self, raw_data: RawData) -> None:
        logging.debug("Starting sorting process.")
        self.students = raw_data.students
        self.courses = raw_data.courses
        self.unsorted_class.students = []

        self.student_pref_positions = {
            student: -1 if student.course_type_pref == CourseType.FULL else [-1, -1]
            for student in self.students
        }

        for student in self.students:
            logging.debug(f"Initializing student {student.last_name}.")
            self.move_student_to_next(student)

        def course_is_overpopulated(course: Course) -> bool:
            return course.is_over_capacity() and course.num_students() > 0

        for i in range(250):
            for course in self.courses:
                if course_is_overpopulated(course):
                    students = course.sort_by_preference_position()
                    for student in students:
                        try:
                            self.move_student_if_needed(student)
                        except Exception as e:
                            logging.error(
                                f"Error moving student {student.last_name}: {e}"
                            )

            # for student in self.students:
            #    try:
            #        self.move_student_if_needed(student)
            #    except Exception as e:
            #        logging.error(f"Error moving student {student.last_name}: {e}")

        total_score: int = 0
        avg_score: float = 0
        mode = [0 for _ in range(6)]
        for student in self.students:
            total_score += student.score()
            avg_score += student.score() / len(self.students)
            mode[student.position()] += 1
        self.meta = {
            "total_score": total_score,
            "avg_score": round(avg_score, 2),
            "mode": mode,
            "students": len(self.students),
            "courses": len(self.courses),
            "overpopulated": [
                course.name
                for course in self.courses
                if course_is_overpopulated(course)
            ],
            "unsorted": self.unsorted_class.num_students(),
        }

    def get_raw_data(self) -> RawData:
        logging.debug("Getting raw data.")
        d = RawData(self.students, self.courses + [self.unsorted_class])
        d.meta = self.meta
        return d
