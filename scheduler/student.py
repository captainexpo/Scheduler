import logging


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
        prefs: dict["CourseType", "Course"],
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
            logging.error(
                f"Error: {self.first_name} {self.last_name} already has a full course: {self._full_course}"
            )
            return False
        if course.is_full_day():
            self._full_course = course
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
            logging.error(
                f"Error: {self.first_name} {self.last_name} already has a morning course: {self._half_courses[0]}"
            )
            return False
        if course.is_full_day():
            logging.error(
                f"Error: {self.first_name} {self.last_name} cannot take a full course in a half day class"
            )
            return False
        self._half_courses[0] = course
        return True

    def add_course_afternoon(self, course: "Course") -> bool:
        # logging.debug(
        #    f"Adding afternoon course {course.name}({course.teacher}) to {self.first_name} {self.last_name}"
        # )
        if self.half_courses[1] is not None:
            logging.error(
                f"Error: {self.first_name} {self.last_name} already has an afternoon course: {self.half_courses[1]}"
            )
            return False
        if course.is_full_day():
            logging.error(
                f"Error: {self.first_name} {self.last_name} cannot take a full course in a half day class"
            )
            return False
        self._half_courses[1] = course
        return True

    def remove_courses(self) -> None:
        if self.full_course is not None:
            if self.full_course.remove_student(self):
                self._full_course = None
        for i in range(2):
            if self.half_courses[i] is not None:
                if self.half_courses[i].remove_student(self):
                    self._half_courses[i] = None

    def score(self) -> int:
        # score calculation is calculated based on how 'happy' this student will be based on the assigned courses
        # if half day is preferred: score = morning_prefs.find(course_a) + afternoon_prefs.find(course_b)
        # if full day is preferred: score = full_prefs.find(course_a)

        score = 0
        if self.full_course is not None:
            try:
                score += (
                    len(self.prefs)
                    - self.prefs[CourseType.FULL].index(self.full_course)
                    + 1
                )
            except ValueError:
                pass  # not found, score is 0
        if self.half_courses[0] is not None:
            try:
                score += (
                    len(self.prefs)
                    - self.prefs[CourseType.MORNING].index(self.half_courses[0])
                    + 1
                )
            except ValueError:
                pass
        if self.half_courses[1] is not None:
            try:
                score += (
                    len(self.prefs)
                    - self.prefs[CourseType.AFTERNOON].index(self.half_courses[1])
                    + 1
                )
            except ValueError:
                pass
        return score

    def position(self) -> int:
        position = 0
        if self.full_course is not None:
            return 5 - self.prefs[CourseType.FULL].index(self.full_course)
        a = 0
        if self.half_courses[0] is not None:
            a += 1
            position += 5 - self.prefs[CourseType.MORNING].index(self.half_courses[0])
        if self.half_courses[1] is not None:
            a += 1
            position += 5 - self.prefs[CourseType.AFTERNOON].index(self.half_courses[1])
        return position // a

    def __str__(self):
        #
        return (
            f"{self.first_name} {self.last_name}({self.grade})(pos {self.position()})"
        )

    def short_str(self):
        return f"{self.first_name}_{self.last_name}(pos {self.position()})"


if True:
    from scheduler.course import Course, CourseType
