from scheduler.data import RawData
from scheduler.course import Course, CourseType
from scheduler.student import Student
import logging

logging.basicConfig(level=logging.DEBUG)


class Sorter:
    students: list[Student]
    courses: list[Course]

    # students get moved here if they can't fit in their preferences
    unsorted_class: Course

    student_pref_positions: dict[Student, int] = {}

    def __init__(self):
        pass

    def move_student_to_next(self, student: Student) -> None:
        """
        Move the student to the next preference in their list of preferences.
        If the student is already at the last preference, they are moved to the unsorted class.
        """
        logging.debug(f"Moving student {student.last_name} to the next preference.")
        student.remove_courses()
        if student.course_type_pref == CourseType.FULL:
            if self.student_pref_positions[student] >= len(
                student.prefs[CourseType.FULL]
            ):
                # move to unsorted class
                logging.debug(f"Student {student.last_name} moved to unsorted class.")
                self.unsorted_class.add_student(student)
                return
            # move to next preference in full courses
            self.student_pref_positions[student] += 1
            c = student.prefs[CourseType.FULL][self.student_pref_positions[student]]
            c.add_student(student)
            student.full_course = c
            logging.debug(f"Student {student.last_name} added to course {c.name}.")
            return

        # half day students
        if student.available_times[0]:
            if self.student_pref_positions[student][0] >= len(
                student.prefs[CourseType.MORNING]
            ):
                # move to unsorted class
                logging.debug(f"Student {student.last_name} moved to unsorted class.")
                self.unsorted_class.add_student(student)
                return
            # move to next preference in morning courses
            self.student_pref_positions[student][0] += 1
            c = student.prefs[CourseType.MORNING][
                self.student_pref_positions[student][0]
            ]
            c.add_student(student)
            student.add_course_morning(c)
            logging.debug(
                f"Student {student.last_name} added to morning course {c.name}."
            )
        if student.available_times[1]:
            if self.student_pref_positions[student][1] >= len(
                student.prefs[CourseType.AFTERNOON]
            ):
                # move to unsorted class
                logging.debug(f"Student {student.last_name} moved to unsorted class.")
                self.unsorted_class.add_student(student)
                return
            # move to next preference in afternoon courses
            self.student_pref_positions[student][1] += 1
            c = student.prefs[CourseType.AFTERNOON][
                self.student_pref_positions[student][1]
            ]
            c.add_student(student)
            student.add_course_afternoon(c)
            logging.debug(
                f"Student {student.last_name} added to afternoon course {c.name}."
            )

    def sort(self, raw_data: RawData) -> None:
        logging.debug("Starting sorting process.")
        self.students = raw_data.students
        self.courses = raw_data.courses
        self.unsorted_class = Course("Unsorted", "Unsorted", 999999, CourseType.FULL)
        self.unsorted_class.students = []
        self.student_pref_positions = {
            student: -1 if student.course_type_pref == CourseType.FULL else [-1, -1]
            for student in self.students
        }

        # initialize classes
        for student in self.students:
            logging.debug(f"Initializing student {student.last_name}.")
            self.move_student_to_next(student)
