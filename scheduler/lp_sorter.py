import pulp
from scheduler.course import CourseType
from scheduler.course import Course
from scheduler.data import RawData
from scheduler.student import Student


class LPSorter:
    def __init__(self):
        self.raw_data: RawData | None = None
        self.meta: dict[str, object] = {}

    def sort(self, raw_data: RawData):
        self.raw_data = raw_data
        self.optimize_class_assignments()

    def optimize_class_assignments(self):
        if self.raw_data is None:
            raise ValueError("No data loaded. Call sort() first.")

        for course in self.raw_data.courses:
            course.students = set()

        for student in self.raw_data.students:
            student._full_course = None
            student._half_courses = [None, None]

        full_students = [
            student
            for student in self.raw_data.students
            if student.course_type_pref == CourseType.FULL
        ]
        half_students = [
            student
            for student in self.raw_data.students
            if student.course_type_pref == CourseType.HALF
        ]

        full_courses = [
            course for course in self.raw_data.courses if course.type == CourseType.FULL
        ]
        morning_courses = [
            course
            for course in self.raw_data.courses
            if course.type == CourseType.MORNING
        ]
        afternoon_courses = [
            course
            for course in self.raw_data.courses
            if course.type == CourseType.AFTERNOON
        ]

        def weight_for(prefs: list[Course], course: Course) -> int:
            return len(prefs) - prefs.index(course)

        full_vars: dict[tuple[Student, Course], pulp.LpVariable] = {
            (student, course): pulp.LpVariable(
                f"full_s{student_index}_c{course_index}", cat="Binary"
            )
            for student_index, student in enumerate(full_students)
            for course_index, course in enumerate(
                student.prefs.get(CourseType.FULL, [])
            )
            if course.type == CourseType.FULL
        }

        morning_vars: dict[tuple[Student, Course], pulp.LpVariable] = {
            (student, course): pulp.LpVariable(
                f"morning_s{student_index}_c{course_index}", cat="Binary"
            )
            for student_index, student in enumerate(half_students)
            if student.available_times[0]
            for course_index, course in enumerate(
                student.prefs.get(CourseType.MORNING, [])
            )
            if course.type == CourseType.MORNING
        }

        afternoon_vars: dict[tuple[Student, Course], pulp.LpVariable] = {
            (student, course): pulp.LpVariable(
                f"afternoon_s{student_index}_c{course_index}", cat="Binary"
            )
            for student_index, student in enumerate(half_students)
            if student.available_times[1]
            for course_index, course in enumerate(
                student.prefs.get(CourseType.AFTERNOON, [])
            )
            if course.type == CourseType.AFTERNOON
        }

        full_unsorted: dict[Student, pulp.LpVariable] = {
            student: pulp.LpVariable(f"full_unsorted_s{student_index}", cat="Binary")
            for student_index, student in enumerate(full_students)
        }
        morning_unsorted: dict[Student, pulp.LpVariable] = {
            student: pulp.LpVariable(f"morning_unsorted_s{student_index}", cat="Binary")
            for student_index, student in enumerate(half_students)
            if student.available_times[0]
        }
        afternoon_unsorted: dict[Student, pulp.LpVariable] = {
            student: pulp.LpVariable(
                f"afternoon_unsorted_s{student_index}", cat="Binary"
            )
            for student_index, student in enumerate(half_students)
            if student.available_times[1]
        }

        def build_model() -> pulp.LpProblem:
            model = pulp.LpProblem("Student_Class_Mixed_Scheduling", pulp.LpMaximize)

            for student in full_students:
                model += (
                    pulp.lpSum(
                        var
                        for (candidate_student, _), var in full_vars.items()
                        if candidate_student is student
                    )
                    + full_unsorted[student]
                    == 1
                )

            for student in half_students:
                if student.available_times[0]:
                    model += (
                        pulp.lpSum(
                            var
                            for (candidate_student, _), var in morning_vars.items()
                            if candidate_student is student
                        )
                        + morning_unsorted[student]
                        == 1
                    )

                if student.available_times[1]:
                    model += (
                        pulp.lpSum(
                            var
                            for (candidate_student, _), var in afternoon_vars.items()
                            if candidate_student is student
                        )
                        + afternoon_unsorted[student]
                        == 1
                    )

            for course in full_courses:
                model += (
                    pulp.lpSum(
                        var
                        for (student, candidate_course), var in full_vars.items()
                        if candidate_course is course
                    )
                    <= course.capacity
                )

            for course in morning_courses:
                model += (
                    pulp.lpSum(
                        var
                        for (student, candidate_course), var in morning_vars.items()
                        if candidate_course is course
                    )
                    <= course.capacity
                )

            for course in afternoon_courses:
                model += (
                    pulp.lpSum(
                        var
                        for (student, candidate_course), var in afternoon_vars.items()
                        if candidate_course is course
                    )
                    <= course.capacity
                )

            return model

        def preference_objective() -> pulp.LpAffineExpression:
            return (
                pulp.lpSum(
                    weight_for(student.prefs.get(CourseType.FULL, []), course) * var
                    for (student, course), var in full_vars.items()
                )
                + pulp.lpSum(
                    weight_for(student.prefs.get(CourseType.MORNING, []), course) * var
                    for (student, course), var in morning_vars.items()
                )
                + pulp.lpSum(
                    weight_for(student.prefs.get(CourseType.AFTERNOON, []), course)
                    * var
                    for (student, course), var in afternoon_vars.items()
                )
            )

        def unsorted_objective() -> pulp.LpAffineExpression:
            return (
                pulp.lpSum(full_unsorted.values())
                + pulp.lpSum(morning_unsorted.values())
                + pulp.lpSum(afternoon_unsorted.values())
            )

        # Stage 1: minimize the number of unsorted full students and unsorted half-day slots.
        stage1 = build_model()
        stage1.sense = pulp.LpMinimize
        stage1.setObjective(unsorted_objective())
        stage1.solve(pulp.PULP_CBC_CMD(msg=True))
        full_unsorted_count = 0
        half_unsorted_count = 0

        for (student, course), var in full_vars.items():
            if pulp.value(var) == 1:
                student.add_course_full(course)

        for student, var in full_unsorted.items():
            if pulp.value(var) == 1:
                full_unsorted_count += 1

        for (student, course), var in morning_vars.items():
            if pulp.value(var) == 1:
                student.add_course_morning(course)

        for student, var in morning_unsorted.items():
            if pulp.value(var) == 1:
                half_unsorted_count += 1

        for (student, course), var in afternoon_vars.items():
            if pulp.value(var) == 1:
                student.add_course_afternoon(course)

        for student, var in afternoon_unsorted.items():
            if pulp.value(var) == 1:
                half_unsorted_count += 1
        self._build_meta(full_unsorted_count, half_unsorted_count)

        print(self.raw_data.meta)

        best_unsorted_value = pulp.value(unsorted_objective())
        best_unsorted = 0
        if isinstance(best_unsorted_value, (int, float)):
            best_unsorted = int(round(best_unsorted_value))

        # Stage 2: maximize preference quality while keeping the best unsorted count.
        model = build_model()
        model += unsorted_objective() == best_unsorted
        model += preference_objective()
        model.solve(pulp.PULP_CBC_CMD(msg=True))

        full_unsorted_count = 0
        half_unsorted_count = 0

        for (student, course), var in full_vars.items():
            if pulp.value(var) == 1:
                student.add_course_full(course)

        for student, var in full_unsorted.items():
            if pulp.value(var) == 1:
                full_unsorted_count += 1

        for (student, course), var in morning_vars.items():
            if pulp.value(var) == 1:
                student.add_course_morning(course)

        for student, var in morning_unsorted.items():
            if pulp.value(var) == 1:
                half_unsorted_count += 1

        for (student, course), var in afternoon_vars.items():
            if pulp.value(var) == 1:
                student.add_course_afternoon(course)

        for student, var in afternoon_unsorted.items():
            if pulp.value(var) == 1:
                half_unsorted_count += 1

        self._build_meta(full_unsorted_count, half_unsorted_count)

    def get_raw_data(self) -> RawData:
        if self.raw_data is None:
            raise ValueError("No data loaded. Call sort() first.")
        result = RawData(self.raw_data.students, self.raw_data.courses)
        result.meta = dict(self.raw_data.meta)
        return result

    def _build_meta(self, full_unsorted_count: int, half_unsorted_count: int) -> None:
        if self.raw_data is None:
            return

        scores = [student.score() for student in self.raw_data.students]
        total_score = sum(scores)
        avg_score = total_score / len(scores) if scores else 0
        unsorted_students = sum(
            1
            for student in self.raw_data.students
            if (
                student.course_type_pref == CourseType.FULL
                and student.full_course is None
            )
            or (
                student.course_type_pref == CourseType.HALF
                and (
                    (student.available_times[0] and student.half_courses[0] is None)
                    or (student.available_times[1] and student.half_courses[1] is None)
                )
            )
        )

        c_dist = [0,0,0,0,0,0]
        top_3 = 0
        for student in self.raw_data.students:
            if student.course_type_pref == CourseType.HALF:
                c = student.half_courses
                i0 = 6
                i1 = 6
                if student.half_courses[0] is not None:
                    i0 = student.prefs[CourseType.MORNING].index(c[0])
                    c_dist[i0] += 0.5
                    if i0 <= 2:
                        top_3 += 1
                else:
                    c_dist[-1] += 0.5
                if student.half_courses[1] is not None:
                    i1 = student.prefs[CourseType.AFTERNOON].index(c[1])
                    c_dist[i1] += 0.5
                    if i1 <= 2 and i0 > 2:
                        top_3 += 1
                else:
                    c_dist[-1] += 0.5
            if student.course_type_pref == CourseType.FULL:
                if student.full_course is not None:
                    i = student.prefs[CourseType.FULL].index(student.full_course)
                    c_dist[i] += 1
                    if i <= 2:
                        top_3 += 1
                else:
                    c_dist[-1] += 1


        self.raw_data.meta = {
            "algorithm": "lp",
            "total_score": total_score,
            "avg_score": round(avg_score, 2),
            "students": len(self.raw_data.students),
            "courses": len(self.raw_data.courses),
            "unsorted": unsorted_students,
            "unsorted_full_students": full_unsorted_count,
            "unsorted_half_slots": half_unsorted_count,
            "score_dist": c_dist,
            "top_3": top_3,
        }
