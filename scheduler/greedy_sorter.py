from scheduler.data import RawData
from scheduler.course import Course, CourseType
from scheduler.student import Student
from collections import deque
import logging
import statistics
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

    def _remove_student_from_course(self, course: Course | None, student: Student) -> None:
        if course is not None:
            course.remove_student(student)

    def _reset_assignment_state(self) -> None:
        for course in self.courses:
            course.students = set()

        self.unsorted_class.students = set()

        for student in self.students:
            student._full_course = None
            student._half_courses = [None, None]

    def add_to_unsorted(self, student: Student) -> None:
        self._remove_student_from_course(student.full_course, student)
        self._remove_student_from_course(student.half_courses[0], student)
        self._remove_student_from_course(student.half_courses[1], student)

        student._full_course = None
        student._half_courses = [None, None]

        if student.course_type_pref == CourseType.FULL:
            student._full_course = self.unsorted_class
        else:
            student._half_courses[0] = self.unsorted_class
            student._half_courses[1] = self.unsorted_class

        self.unsorted_class.add_student(student)

    def _is_unsorted_student(self, student: Student) -> bool:
        return (
            student.full_course is self.unsorted_class
            or student.half_courses[0] is self.unsorted_class
            or student.half_courses[1] is self.unsorted_class
        )

    def move_student_if_needed(self, student: Student) -> list[Course]:
        moved_to: list[Course] = []

        if student.course_type_pref == CourseType.FULL:
            if (
                student.full_course is not None
                and student.full_course.is_over_capacity()
            ):
                self.move_student_to_next(student)

                if (
                    student.full_course is not None
                    and student.full_course is not self.unsorted_class
                    and student.full_course.is_over_capacity()
                ):
                    moved_to.append(student.full_course)
        else:
            morning_course = student.half_courses[0]
            if (
                student.available_times[0]
                and morning_course is not None
                and morning_course.is_over_capacity()
            ):
                morning_course.remove_student(student)
                self.move_student_to_next(student, 0)

                if (
                    student.half_courses[0] is not None
                    and student.half_courses[0] is not self.unsorted_class
                    and student.half_courses[0].is_over_capacity()
                ):
                    moved_to.append(student.half_courses[0])
            afternoon_course = student.half_courses[1]
            if (
                student.available_times[1]
                and afternoon_course is not None
                and afternoon_course.is_over_capacity()
            ):
                afternoon_course.remove_student(student)
                self.move_student_to_next(student, 1)

                if (
                    student.half_courses[1] is not None
                    and student.half_courses[1] is not self.unsorted_class
                    and student.half_courses[1].is_over_capacity()
                ):
                    moved_to.append(student.half_courses[1])

        return moved_to

    def move_student_to_next(self, student: Student, time: int = -1) -> None:
        logging.debug(
            f"Moving student {student.last_name} to pref {self.student_pref_positions.get(student)}."
        )

        # if time == -1:
        #    student.remove_courses()

        if student.course_type_pref == CourseType.FULL:
            self._move_full_day_student(student)
        else:
            self._move_half_day_student(student, time)

    def _move_full_day_student(self, student: Student) -> None:
        prefs = student.prefs.get(CourseType.FULL, [])
        pref_position = self.student_pref_positions.get(student, -1)
        if not isinstance(pref_position, int):
            logging.warning(
                f"Invalid student_pref_positions type for {student.last_name}"
            )
            self.add_to_unsorted(student)
            return

        current_index = pref_position + 1
        if current_index >= len(prefs):
            logging.debug(
                f"Student {student.last_name} moved to unsorted class (FULL)."
            )
            self.add_to_unsorted(student)
            self.student_pref_positions[student] = current_index

            return

        course = prefs[current_index]
        # course.add_student(student)
        student.add_course_full(course)
        self.student_pref_positions[student] = current_index
        logging.debug(f"Student {student.last_name} added to course {course.name}.")

    def _move_half_day_student(self, student: Student, t: int = -1) -> None:
        if isinstance(self.student_pref_positions[student], list) is False:
            logging.warning(
                f"Invalid student_pref_positions type for {student.last_name}"
            )
            self.add_to_unsorted(student)
            return

        positions = self.student_pref_positions[student]
        if not isinstance(positions, list) or len(positions) != 2:
            logging.warning(
                f"Malformed preference positions for student {student.last_name}"
            )
            self.add_to_unsorted(student)

            return

        updated = self._assign_half_day_courses(student, positions, t)

        if not updated:
            logging.debug(
                f"Student {student.last_name} moved to unsorted class (HALF)."
            )
            self.add_to_unsorted(student)

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
                # course.add_student(student)

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
        self._reset_assignment_state()

        self.student_pref_positions = {
            student: -1 if student.course_type_pref == CourseType.FULL else [-1, -1]
            for student in self.students
        }

        for student in self.students:
            logging.debug(f"Initializing student {student.last_name}.")
            self.move_student_to_next(student)

        def course_is_overpopulated(course: Course) -> bool:
            return course.is_over_capacity() and course.num_students() > 0

        worklist = deque()
        queued_courses: set[Course] = set()

        for course in self.courses:
            if course_is_overpopulated(course):
                worklist.append(course)
                queued_courses.add(course)

        while worklist:
            course = worklist.popleft()
            queued_courses.discard(course)

            if not course_is_overpopulated(course):
                continue

            students = course.sort_by_preference_position()[::-1] # reverse to pop least satisfied students first
            for student in students:
                try:
                    for next_course in self.move_student_if_needed(student):
                        if (
                            next_course not in queued_courses
                            and course_is_overpopulated(next_course)
                        ):
                            worklist.append(next_course)
                            queued_courses.add(next_course)
                except Exception as e:
                    raise e
                    logging.error(
                        f"Error moving student {student.last_name}: {e}"
                    )

            # for student in self.students:
            #    try:
            #        self.move_student_if_needed(student)
            #    except Exception as e:
            #        logging.error(f"Error moving student {student.last_name}: {e}")

        scored_students = [
            student for student in self.students if not self._is_unsorted_student(student)
        ]
        scores = [student.score() for student in scored_students]
        total_score: float = sum(scores)
        avg_score: float = total_score / len(scores) if scores else 0

        # Additional distribution stats help compare scheduling runs quickly.
        sorted_scores = sorted(scores)
        mid = len(sorted_scores) // 2
        if not sorted_scores:
            q1 = 0
            q3 = 0
        else:
            lower = sorted_scores[:mid]
            upper = sorted_scores[mid + (len(sorted_scores) % 2) :]
            q1 = statistics.median(lower) if lower else sorted_scores[0]
            q3 = statistics.median(upper) if upper else sorted_scores[-1]

        modes = statistics.multimode(scores) if scores else []
        mode_score = modes[0] if len(modes) == 1 else None

        satisfied_count = sum(1 for score in scores if score <= 1)
        top3_count = sum(1 for score in scores if score <= 2)
        worst_count = sum(1 for score in scores if score >= 6)
        satisfaction_rate = (
            round((satisfied_count / len(scores)) * 100, 2) if scores else 0
        )
        top3_rate = round((top3_count / len(scores)) * 100, 2) if scores else 0
        worst_rate = round((worst_count / len(scores)) * 100, 2) if scores else 0

        self.meta = {
            "total_score": total_score,
            "avg_score": round(avg_score, 2),
            "median_score": round(statistics.median(scores), 2) if scores else 0,
            "mode_score": mode_score,
            "mode_scores": modes,
            "stddev_score": round(statistics.pstdev(scores), 2) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "q1_score": round(q1, 2),
            "q3_score": round(q3, 2),
            "max_score": max(scores) if scores else 0,
            "students": len(self.students),
            "total_students": len(self.students),
            "scored_students": len(scored_students),
            "satisfied_students": satisfied_count,
            "top3_students": top3_count,
            "worst_score_students": worst_count,
            "satisfaction_rate_pct": satisfaction_rate,
            "top3_rate_pct": top3_rate,
            "worst_rate_pct": worst_rate,
            "courses": len(self.courses),
            "overpopulated": [
                course.name
                for course in self.courses
                if course_is_overpopulated(course)
            ],
            "unsorted": self.unsorted_class.num_students(),
        }
        # print students and their assigned courses
        # for student in self.students:
        #    if student.course_type_pref == CourseType.FULL:
        #        logging.debug(
        #            f"Student {student.last_name} assigned to full course {student.full_course.name if student.full_course else 'None'}"
        #        )
        #    else:
        #        logging.debug(
        #            f"Student {student.last_name} assigned to half courses {(student.half_courses[0].name) if student.half_courses[0] else 'None'} and {student.half_courses[1].name if student.half_courses[1] else 'None'}"
        #        )

    def get_raw_data(self) -> RawData:
        logging.debug("Getting raw data.")
        d = RawData(self.students, self.courses + [self.unsorted_class])
        d.meta = self.meta
        return d
