from scheduler.student import Student
from scheduler.course import Course, CourseType
from typing import Any
from scheduler.csvhelper import CSVWriter


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

    def _escape_csv(self, value: str) -> str:
        if "," in value or '"' in value:
            value = value.replace('"', '""')
            return f'"{value}"'
        return value

    def as_text_output(self, format: str = "txt") -> str:
        if format == "txt":
            return self.__str__()
        elif format == "csv":
            writer = CSVWriter()
            writer.write_header("First Name,Last Name,Grade,BTC/CTE,Course Type Preference,Full Course,Half Course 1,Half Course 2,Preference #")
            for student in sorted(self.students, key=lambda s: s.last_name):
                full_course = student.full_course.name if student.full_course else ""
                half_course_1 = student.half_courses[0].name if student.half_courses[0] else ""
                half_course_2 = student.half_courses[1].name if student.half_courses[1] else ""

                btc_cte_time = "None"
                if student.available_times[0] and not student.available_times[1]:
                    btc_cte_time = "Morning"
                elif student.available_times[1] and not student.available_times[0]:
                    btc_cte_time = "Afternoon"

                pref_num_str = ""
                if student.full_course:
                    pref_num_str = str(student.prefs[CourseType.FULL].index(student.full_course) + 1)
                else:
                    if student.half_courses[0]:
                        pref_num_str += str(student.prefs[CourseType.MORNING].index(student.half_courses[0]) + 1)
                    if student.half_courses[1]:
                        pref_num_str += str(student.prefs[CourseType.AFTERNOON].index(student.half_courses[1]) + 1)
                if pref_num_str == "":
                    pref_num_str = "N/A"
                writer.write(student.first_name)
                writer.write(student.last_name)
                writer.write(student.grade)
                writer.write(btc_cte_time)
                writer.write(student.course_type_pref.name)
                writer.write(full_course)
                writer.write(half_course_1)
                writer.write(half_course_2)
                writer.write(pref_num_str)
                writer.flush_line()

            print("Generated CSV output")
            print(len(self.students), "students written to CSV")
            return writer.get_raw_data()
        else:
            raise ValueError(f"Unknown format: {format}")

    def __repr__(self) -> str:
        return self.__str__()
