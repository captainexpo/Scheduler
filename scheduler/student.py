class Student:
    first_name: str
    last_name: str
    course_type_pref: "CourseType"
    prefs: dict["CourseType", "Course"]
    cur_pref: list[str]
    available_times: tuple[bool, bool]

    def __init__(
        self,
        first_name: str,
        last_name: str,
        grade: str,
        course_type_pref: "CourseType",
        available_times: tuple[bool, bool],  # (morning, afternoon) for BTC students
        prefs: dict["CourseType", "Course"],
    ) -> None:
        self.prefs = prefs
        self.first_name = first_name
        self.last_name = last_name
        self.grade = grade
        self.course_type_pref = course_type_pref
        self.cur_pref = []
        self.available_times = available_times

    def __str__(self):
        return f"{self.first_name} {self.last_name}({self.grade})"


from scheduler.course import Course, CourseType
