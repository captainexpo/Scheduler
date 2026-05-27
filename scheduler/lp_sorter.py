import pulp
from scheduler.course import CourseType
from scheduler.course import Course
from scheduler.data import RawData
from scheduler.student import Student


class LPSorter:
    opts: dict[str, object]

    def __init__(self, opts: dict[str, object] | None = None):
        self.raw_data: RawData | None = None
        self.meta: dict[str, object] = {}
        self.opts = opts or {}

    def sort(self, raw_data: RawData):
        self.raw_data = raw_data
        self.optimize_class_assignments()

    def optimize_class_assignments(self):
        if self.raw_data is None:
            raise ValueError("No data loaded. Call sort() first.")
        raw_data = self.raw_data
        preference_weight_value = self.opts.get("preference_weight", 1.0)
        if isinstance(preference_weight_value, (int, float)):
            preference_weight = float(preference_weight_value)
        else:
            preference_weight = 1.0

        grade_mixing_weight_value = self.opts.get("grade_mixing_weight", 0.0)
        if isinstance(grade_mixing_weight_value, (int, float)):
            grade_mixing_weight = float(grade_mixing_weight_value)
        else:
            grade_mixing_weight = 0.0

        student_grades: dict[Student, int] = {}
        grade_mixing_enabled = grade_mixing_weight != 0.0
        if grade_mixing_enabled:
            for student in raw_data.students:
                try:
                    student_grades[student] = int(student.grade)
                except ValueError:
                    grade_mixing_enabled = False
                    student_grades = {}
                    break

        grade_values = sorted(set(student_grades.values())) if grade_mixing_enabled else []

        def reset_assignment_state() -> None:
            for course in raw_data.courses:
                course.students = set()
            for student in raw_data.students:
                student._full_course = None
                student._half_courses = [None, None]

        def build_assignment_vars(
            students: list[Student],
            pref_type: CourseType,
            required_course_type: CourseType,
            var_prefix: str,
            availability_index: int | None = None,
        ) -> dict[tuple[Student, Course], pulp.LpVariable]:
            return {
                (student, course): pulp.LpVariable(
                    f"{var_prefix}_s{student_index}_c{course_index}", cat="Binary"
                )
                for student_index, student in enumerate(students)
                if availability_index is None
                or student.available_times[availability_index]
                for course_index, course in enumerate(student.prefs.get(pref_type, []))
                if course.type == required_course_type
            }

        def build_unsorted_vars(
            students: list[Student],
            var_prefix: str,
            availability_index: int | None = None,
        ) -> dict[Student, pulp.LpVariable]:
            return {
                student: pulp.LpVariable(f"{var_prefix}_s{student_index}", cat="Binary")
                for student_index, student in enumerate(students)
                if availability_index is None
                or student.available_times[availability_index]
            }

        def vars_by_student(
            vars_map: dict[tuple[Student, Course], pulp.LpVariable],
        ) -> dict[Student, list[pulp.LpVariable]]:
            grouped: dict[Student, list[pulp.LpVariable]] = {}
            for (student, _), var in vars_map.items():
                grouped.setdefault(student, []).append(var)
            return grouped

        def assignment_items_by_student(
            vars_map: dict[tuple[Student, Course], pulp.LpVariable],
        ) -> dict[Student, list[tuple[Course, pulp.LpVariable]]]:
            grouped: dict[Student, list[tuple[Course, pulp.LpVariable]]] = {}
            for (student, course), var in vars_map.items():
                grouped.setdefault(student, []).append((course, var))
            return grouped

        def vars_by_course(
            vars_map: dict[tuple[Student, Course], pulp.LpVariable],
        ) -> dict[Course, list[pulp.LpVariable]]:
            grouped: dict[Course, list[pulp.LpVariable]] = {}
            for (_, course), var in vars_map.items():
                grouped.setdefault(course, []).append(var)
            return grouped

        def sum_for_student(
            grouped: dict[Student, list[pulp.LpVariable]], student: Student
        ) -> pulp.LpAffineExpression:
            return pulp.lpSum(grouped.get(student, []))

        def sum_for_course(
            grouped: dict[Course, list[pulp.LpVariable]], course: Course
        ) -> pulp.LpAffineExpression:
            return pulp.lpSum(grouped.get(course, []))

        reset_assignment_state()

        full_students = [
            student
            for student in raw_data.students
            if student.course_type_pref == CourseType.FULL
        ]
        half_students = [
            student
            for student in raw_data.students
            if student.course_type_pref == CourseType.HALF
        ]
        flex_students = [
            student
            for student in raw_data.students
            if student.course_type_pref == CourseType.NO_PREFERENCE
        ]

        full_courses = [
            course for course in raw_data.courses if course.type == CourseType.FULL
        ]
        morning_courses = [
            course for course in raw_data.courses if course.type == CourseType.MORNING
        ]
        afternoon_courses = [
            course for course in raw_data.courses if course.type == CourseType.AFTERNOON
        ]

        # this function assigns higher weights to higher-ranked preferences, can be changed in the future
        def weight_for(prefs: list[Course], course: Course) -> int:
            return (len(prefs) - prefs.index(course)) ** 2

        full_vars = build_assignment_vars(
            full_students, CourseType.FULL, CourseType.FULL, "full"
        )

        morning_vars = build_assignment_vars(
            half_students,
            CourseType.MORNING,
            CourseType.MORNING,
            "morning",
            availability_index=0,
        )

        afternoon_vars = build_assignment_vars(
            half_students,
            CourseType.AFTERNOON,
            CourseType.AFTERNOON,
            "afternoon",
            availability_index=1,
        )

        full_unsorted = build_unsorted_vars(full_students, "full_unsorted")
        morning_unsorted = build_unsorted_vars(
            half_students, "morning_unsorted", availability_index=0
        )
        afternoon_unsorted = build_unsorted_vars(
            half_students, "afternoon_unsorted", availability_index=1
        )

        flex_full_mode: dict[Student, pulp.LpVariable] = {
            student: pulp.LpVariable(f"flex_full_mode_s{student_index}", cat="Binary")
            for student_index, student in enumerate(flex_students)
        }
        flex_full_vars = build_assignment_vars(
            flex_students, CourseType.FULL, CourseType.FULL, "flex_full"
        )
        flex_morning_vars = build_assignment_vars(
            flex_students,
            CourseType.MORNING,
            CourseType.MORNING,
            "flex_morning",
            availability_index=0,
        )
        flex_afternoon_vars = build_assignment_vars(
            flex_students,
            CourseType.AFTERNOON,
            CourseType.AFTERNOON,
            "flex_afternoon",
            availability_index=1,
        )
        flex_full_unsorted = build_unsorted_vars(flex_students, "flex_full_unsorted")
        flex_morning_unsorted = build_unsorted_vars(
            flex_students, "flex_morning_unsorted", availability_index=0
        )
        flex_afternoon_unsorted = build_unsorted_vars(
            flex_students, "flex_afternoon_unsorted", availability_index=1
        )

        full_vars_by_student = vars_by_student(full_vars)
        morning_vars_by_student = vars_by_student(morning_vars)
        afternoon_vars_by_student = vars_by_student(afternoon_vars)
        flex_full_vars_by_student = vars_by_student(flex_full_vars)
        flex_morning_vars_by_student = vars_by_student(flex_morning_vars)
        flex_afternoon_vars_by_student = vars_by_student(flex_afternoon_vars)

        full_assignments_by_student = assignment_items_by_student(full_vars)
        morning_assignments_by_student = assignment_items_by_student(morning_vars)
        afternoon_assignments_by_student = assignment_items_by_student(afternoon_vars)
        flex_full_assignments_by_student = assignment_items_by_student(flex_full_vars)
        flex_morning_assignments_by_student = assignment_items_by_student(
            flex_morning_vars
        )
        flex_afternoon_assignments_by_student = assignment_items_by_student(
            flex_afternoon_vars
        )

        full_vars_by_course = vars_by_course(full_vars)
        morning_vars_by_course = vars_by_course(morning_vars)
        afternoon_vars_by_course = vars_by_course(afternoon_vars)
        flex_full_vars_by_course = vars_by_course(flex_full_vars)
        flex_morning_vars_by_course = vars_by_course(flex_morning_vars)
        flex_afternoon_vars_by_course = vars_by_course(flex_afternoon_vars)

        def assign_solution() -> tuple[int, int]:
            reset_assignment_state()

            full_unsorted_count = 0
            half_unsorted_count = 0

            for student, assignments in full_assignments_by_student.items():
                for course, var in assignments:
                    if pulp.value(var) == 1:
                        student.add_course_full(course)

            for student, var in full_unsorted.items():
                if pulp.value(var) == 1:
                    full_unsorted_count += 1

            for student, assignments in morning_assignments_by_student.items():
                for course, var in assignments:
                    if pulp.value(var) == 1:
                        student.add_course_morning(course)

            for student, var in morning_unsorted.items():
                if pulp.value(var) == 1:
                    half_unsorted_count += 1

            for student, assignments in afternoon_assignments_by_student.items():
                for course, var in assignments:
                    if pulp.value(var) == 1:
                        student.add_course_afternoon(course)

            for student, var in afternoon_unsorted.items():
                if pulp.value(var) == 1:
                    half_unsorted_count += 1

            for student, var in flex_full_mode.items():
                if pulp.value(var) == 1:
                    assigned = False
                    for course, candidate_var in flex_full_assignments_by_student.get(
                        student, []
                    ):
                        if pulp.value(candidate_var) == 1:
                            student.add_course_full(course)
                            assigned = True
                    if not assigned:
                        full_unsorted_count += 1
                else:
                    morning_assigned = False
                    afternoon_assigned = False
                    for (
                        course,
                        candidate_var,
                    ) in flex_morning_assignments_by_student.get(student, []):
                        if pulp.value(candidate_var) == 1:
                            student.add_course_morning(course)
                            morning_assigned = True
                    for (
                        course,
                        candidate_var,
                    ) in flex_afternoon_assignments_by_student.get(student, []):
                        if pulp.value(candidate_var) == 1:
                            student.add_course_afternoon(course)
                            afternoon_assigned = True

                    if student.available_times[0] and not morning_assigned:
                        half_unsorted_count += 1
                    if student.available_times[1] and not afternoon_assigned:
                        half_unsorted_count += 1

            return full_unsorted_count, half_unsorted_count

        def build_model() -> pulp.LpProblem:
            model = pulp.LpProblem("Student_Class_Mixed_Scheduling", pulp.LpMaximize)

            for student in full_students:
                model += (
                    sum_for_student(full_vars_by_student, student)
                    + full_unsorted[student]
                    == 1
                )

            for student in half_students:
                if student.available_times[0]:
                    model += (
                        sum_for_student(morning_vars_by_student, student)
                        + morning_unsorted[student]
                        == 1
                    )

                if student.available_times[1]:
                    model += (
                        sum_for_student(afternoon_vars_by_student, student)
                        + afternoon_unsorted[student]
                        == 1
                    )

            for student in flex_students:
                mode_full = flex_full_mode[student]
                model += (
                    sum_for_student(flex_full_vars_by_student, student)
                    + flex_full_unsorted[student]
                    == mode_full
                )

                if student.available_times[0]:
                    model += (
                        sum_for_student(flex_morning_vars_by_student, student)
                        + flex_morning_unsorted[student]
                        == 1 - mode_full
                    )

                if student.available_times[1]:
                    model += (
                        sum_for_student(flex_afternoon_vars_by_student, student)
                        + flex_afternoon_unsorted[student]
                        == 1 - mode_full
                    )

                if not student.available_times[0] or not student.available_times[1]:
                    model += mode_full == 1

            for course in full_courses:
                model += (
                    sum_for_course(full_vars_by_course, course)
                    + sum_for_course(flex_full_vars_by_course, course)
                    <= course.capacity
                )

            for course in morning_courses:
                model += (
                    sum_for_course(morning_vars_by_course, course)
                    + sum_for_course(flex_morning_vars_by_course, course)
                    <= course.capacity
                )

            for course in afternoon_courses:
                model += (
                    sum_for_course(afternoon_vars_by_course, course)
                    + sum_for_course(flex_afternoon_vars_by_course, course)
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
                + pulp.lpSum(
                    weight_for(student.prefs.get(CourseType.FULL, []), course) * var
                    for (student, course), var in flex_full_vars.items()
                )
                + pulp.lpSum(
                    weight_for(student.prefs.get(CourseType.MORNING, []), course) * var
                    for (student, course), var in flex_morning_vars.items()
                )
                + pulp.lpSum(
                    weight_for(student.prefs.get(CourseType.AFTERNOON, []), course)
                    * var
                    for (student, course), var in flex_afternoon_vars.items()
                )
            )

        def flex_preference_objective() -> pulp.LpAffineExpression:
            return pulp.lpSum(
                (
                    flex_full_mode[student]
                    if student.flex_pref == CourseType.FULL
                    else 1 - flex_full_mode[student]
                    if student.flex_pref == CourseType.HALF
                    else 0
                )
                for student in flex_students
            )

        def unsorted_objective() -> pulp.LpAffineExpression:
            return (
                pulp.lpSum(full_unsorted.values())
                + pulp.lpSum(morning_unsorted.values())
                + pulp.lpSum(afternoon_unsorted.values())
                + pulp.lpSum(flex_full_unsorted.values())
                + pulp.lpSum(flex_morning_unsorted.values())
                + pulp.lpSum(flex_afternoon_unsorted.values())
            )

        def grade_mixing_objective(model: pulp.LpProblem) -> pulp.LpAffineExpression:
            if not grade_mixing_enabled:
                return pulp.lpSum([])

            assignment_maps = (
                full_vars,
                morning_vars,
                afternoon_vars,
                flex_full_vars,
                flex_morning_vars,
                flex_afternoon_vars,
            )
            assignments_by_course_grade: dict[tuple[Course, int], list[pulp.LpVariable]] = {}
            for vars_map in assignment_maps:
                for (student, course), var in vars_map.items():
                    grade = student_grades[student]
                    assignments_by_course_grade.setdefault((course, grade), []).append(var)

            course_penalties = []
            for course_index, course in enumerate(raw_data.courses):
                for grade in grade_values:
                    assigned_vars = assignments_by_course_grade.get((course, grade), [])
                    if not assigned_vars:
                        continue

                    count_choices = [
                        pulp.LpVariable(
                            f"grade_mix_c{course_index}_g{grade}_k{count}", cat="Binary"
                        )
                        for count in range(course.capacity + 1)
                    ]

                    model += pulp.lpSum(count_choices) == 1
                    model += pulp.lpSum(assigned_vars) == pulp.lpSum(
                        count * choice
                        for count, choice in enumerate(count_choices)
                    )
                    course_penalties.append(
                        pulp.lpSum(
                            (count * (count - 1) / 2) * choice
                            for count, choice in enumerate(count_choices)
                        )
                    )

            return -pulp.lpSum(course_penalties)

        # Stage 1: minimize the number of unsorted full students and unsorted half-day slots.
        stage1 = build_model()
        stage1.sense = pulp.LpMinimize
        stage1.setObjective(unsorted_objective())
        stage1.solve(pulp.PULP_CBC_CMD(msg=True))
        full_unsorted_count, half_unsorted_count = assign_solution()
        self._build_meta(full_unsorted_count, half_unsorted_count)

        print(self.raw_data.meta)

        reset_assignment_state()

        best_unsorted_value = pulp.value(unsorted_objective())
        best_unsorted = 0
        if isinstance(best_unsorted_value, (int, float)):
            best_unsorted = int(round(best_unsorted_value))

        # Stage 2: maximize preference quality while keeping the best unsorted count.
        model = build_model()
        model += unsorted_objective() == best_unsorted
        print("Best unsorted count from stage 1:", best_unsorted)
        print("Preference objective weight:", preference_weight)
        print("Grade mixing objective weight:", grade_mixing_weight)
        grade_mixing_term = grade_mixing_objective(model)
        model += preference_objective() * preference_weight + grade_mixing_term * grade_mixing_weight

        model.solve(pulp.PULP_CBC_CMD(msg=True))

        best_combined_value = pulp.value(
            preference_objective() * preference_weight
            + grade_mixing_term * grade_mixing_weight
        )
        best_combined = 0
        if isinstance(best_combined_value, (int, float)):
            best_combined = int(round(best_combined_value))

        # Stage 3: keep the best preference score and use flex preference as a tie-breaker.
        model = build_model()
        model += unsorted_objective() == best_unsorted
        grade_mixing_term = grade_mixing_objective(model)
        model += (
            preference_objective() * preference_weight
            + grade_mixing_term * grade_mixing_weight
            == best_combined
        )
        model += flex_preference_objective()
        model.solve(pulp.PULP_CBC_CMD(msg=True))

        full_unsorted_count, half_unsorted_count = assign_solution()

        self._build_meta(full_unsorted_count, half_unsorted_count)

    def get_raw_data(self) -> RawData:
        if self.raw_data is None:
            raise ValueError("No data loaded. Call sort() first.")
        result = RawData(self.raw_data.students, self.raw_data.courses)
        result.meta = dict(self.raw_data.meta)
        return result

    def _grade_mixing_metrics(self) -> dict[str, object]:
        if self.raw_data is None:
            return {
                "grade_variance": 0.0,
                "grade_mixing_ratio": 0.0,
                "grade_mixing_threshold": 0.5,
                "sufficiently_mixed": False,
            }

        threshold_value = self.opts.get("grade_mixing_threshold", 0.5)
        if isinstance(threshold_value, (int, float)):
            grade_mixing_threshold = float(threshold_value)
        else:
            grade_mixing_threshold = 0.5

        course_variances: list[float] = []
        assigned_grades: list[int] = []

        for course in self.raw_data.courses:
            grades = []
            for student in course.students:
                try:
                    grade = int(student.grade)
                except ValueError:
                    continue
                grades.append(grade)
                assigned_grades.append(grade)

            if not grades:
                continue

            avg_grade = sum(grades) / len(grades)
            variance = sum((grade - avg_grade) ** 2 for grade in grades) / len(grades)
            course_variances.append(variance)

        grade_variance = sum(course_variances) / len(course_variances) if course_variances else 0.0
        if assigned_grades:
            grade_range = max(assigned_grades) - min(assigned_grades)
            max_possible_variance = (grade_range**2) / 4 if grade_range else 0.0
            if max_possible_variance:
                grade_mixing_ratio = min(1.0, grade_variance / max_possible_variance)
            else:
                grade_mixing_ratio = 1.0
        else:
            grade_mixing_ratio = 0.0

        return {
            "grade_variance": round(grade_variance, 4),
            "grade_mixing_ratio": round(grade_mixing_ratio, 4),
            "grade_mixing_threshold": grade_mixing_threshold,
            "sufficiently_mixed": grade_mixing_ratio >= grade_mixing_threshold,
        }

    def _build_meta(self, full_unsorted_count: int, half_unsorted_count: int) -> None:
        if self.raw_data is None:
            return

        scores = [student.score() for student in self.raw_data.students]
        total_score = sum(scores)
        avg_score = total_score / len(scores) if scores else 0
        unsorted_students = 0
        for student in self.raw_data.students:
            if student.course_type_pref == CourseType.FULL:
                if student.full_course is None:
                    unsorted_students += 1
            elif student.course_type_pref == CourseType.HALF:
                if (student.available_times[0] and student.half_courses[0] is None) or (
                    student.available_times[1] and student.half_courses[1] is None
                ):
                    unsorted_students += 1
            else:
                if student.full_course is not None:
                    continue
                if (student.available_times[0] and student.half_courses[0] is None) or (
                    student.available_times[1] and student.half_courses[1] is None
                ):
                    unsorted_students += 1

        c_dist: list[float] = [0, 0, 0, 0, 0, 0]
        top_3 = 0
        for student in self.raw_data.students:
            if student.full_course is not None:
                i = student.prefs[CourseType.FULL].index(student.full_course)
                c_dist[i] += 1
                if i <= 2:
                    top_3 += 1
            elif student.course_type_pref in (
                CourseType.HALF,
                CourseType.NO_PREFERENCE,
            ):
                c = student.half_courses
                i0 = 6
                i1 = 6
                if student.half_courses[0] is not None:
                    i0 = student.prefs[CourseType.MORNING].index(c[0])
                    c_dist[i0] += 0.5
                    if i0 <= 2:
                        top_3 += 1
                elif student.available_times[0]:
                    c_dist[-1] += 0.5
                if student.half_courses[1] is not None:
                    i1 = student.prefs[CourseType.AFTERNOON].index(c[1])
                    c_dist[i1] += 0.5
                    if i1 <= 2 and i0 > 2:
                        top_3 += 1
                elif student.available_times[1]:
                    c_dist[-1] += 0.5
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
            **self._grade_mixing_metrics(),
        }
