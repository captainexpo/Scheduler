from typing import Any
import logging


def index_def(ls: list[Any], elem: Any, default: Any = -1) -> int:
    """
    Returns the index of the element in the list, or default if not found.
    """
    try:
        return ls.index(elem)
    except ValueError:
        return default


class Student:
    first_name: str
    last_name: str
    course_type_pref: "CourseType"
    prefs: dict["CourseType", "Course"]
    available_times: tuple[bool, bool]
    # full_course: "Course" = None
    # half_courses: list["Course"] = [None, None]

    def __init__(
        self,
        first_name: str,
        last_name: str,
        grade: str,
        course_type_pref: "CourseType",
        available_times: tuple[bool, bool],  # (morning, afternoon) for BTC students
        prefs: dict["CourseType", list["Course"]],
    ) -> None:
        if not isinstance(list(prefs.keys())[0], CourseType):
            raise TypeError("prefs must be a dict of CourseType to Course")
        self.prefs = prefs
        self.first_name = first_name
        self.last_name = last_name
        self.grade = grade
        self.course_type_pref = course_type_pref
        self.available_times = available_times
        self._full_course = None
        self._half_courses = [None, None]

    @property
    def full_course(self) -> "Course":
        return self._full_course

    @property
    def half_courses(self) -> list["Course"]:
        return self._half_courses

    def add_course_full(self, course: "Course") -> bool:
        # logging.debug(
        #    f"Adding full course {course.name}({course.teacher}) to {self.first_name} {self.last_name}"
        # )
        if self._full_course is not None:
            self._full_course.remove_student(self)
        if course.is_full_day():
            self._full_course = course
            course.add_student(self)
            return True
        logging.error(
            f"Error: {self.first_name} {self.last_name} cannot take a full course in a half day class"
        )
        return False

    def add_course_morning(self, course: "Course") -> bool:
        # logging.debug(
        #    f"Adding morning course {course.name}({course.teacher}) to {self.first_name} {self.last_name}"
        # )
        if self._half_courses[0] is not None:
            self.half_courses[0].remove_student(self)

        if course.is_full_day():
            logging.error(
                f"Error: {self.first_name} {self.last_name} cannot take a full course in a half day class"
            )
            return False
        course.add_student(self)
        self._half_courses[0] = course
        return True

    def add_course_afternoon(self, course: "Course") -> bool:
        # logging.debug(
        #    f"Adding afternoon course {course.name}({course.teacher}) to {self.first_name} {self.last_name}"
        # )
        if self.half_courses[1] is not None:
            self.half_courses[1].remove_student(self)
        if course.is_full_day():
            logging.error(
                f"Error: {self.first_name} {self.last_name} cannot take a full course in a half day class"
            )
            return False
        course.add_student(self)
        self._half_courses[1] = course
        return True

    def remove_courses(self) -> None:
        raise Exception("FUCK yoU")
        if self.full_course is not None:
            if self.full_course.remove_student(self):
                self._full_course = None
        for i in range(2):
            if self.half_courses[i] is not None:
                if self.half_courses[i].remove_student(self):
                    self._half_courses[i] = None

    def score(self) -> int:
        """
        Calculates a 'happiness' score from 0 (unhappy) to 100 (perfect).
        """
        if self.course_type_pref == CourseType.FULL:
            return index_def(self.prefs[CourseType.FULL], self.full_course, 0)
        else:
            return (
                index_def(self.prefs[CourseType.MORNING], self.half_courses[0], 0)
                + index_def(self.prefs[CourseType.AFTERNOON], self.half_courses[1], 0)
                / 2
            )

    def __str__(self):
        #
        return f"{self.first_name} {self.last_name}{self.available_times}({self._full_course.name if self._full_course is not None else 'None'})({self._half_courses[0].name if self._half_courses[0] is not None else 'None'})({self._half_courses[1].name if self._half_courses[1] is not None else 'None'})"

    def short_str(self):
        return f"{self.first_name}_{self.last_name}({self.score()})"


if True:
    from scheduler.course import Course, CourseType
