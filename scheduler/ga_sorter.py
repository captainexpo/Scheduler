from __future__ import annotations

from collections import defaultdict
import random
import statistics
import sys
from typing import Union

from scheduler.course import Course, CourseType
from scheduler.data import RawData
from scheduler.sorter import Sorter
from scheduler.student import Student


Assignment = Union[Course, tuple[Course | None, Course | None], None]
Genome = dict[Student, Assignment]
EvalMetrics = tuple[int, int, float, int]


class GASorter(Sorter):
    def __init__(
        self,
        population_size: int = 60,
        generations: int = 60,
        mutation_rate: float = 0.08,
        elite_fraction: float = 0.15,
        seed: int | None = None,
    ) -> None:
        super().__init__()
        self.population_size = max(10, population_size)
        self.generations = max(1, generations)
        self.mutation_rate = max(0.0, min(1.0, mutation_rate))
        self.elite_fraction = max(0.0, min(0.5, elite_fraction))
        self.seed = seed
        self.feasibility_unsorted_slack = 10
        self.feasibility_overflow_slack = 20

    def _print_generation_progress(
        self,
        generation_index: int,
        completed: int,
        total: int,
        best_unsorted: int,
        best_overflow: int,
    ) -> None:
        if total <= 0:
            total = 1
        width = 28
        fraction = min(max(completed / total, 0.0), 1.0)
        filled = int(width * fraction)
        bar = "#" * filled + "-" * (width - filled)
        pct = int(fraction * 100)

        line = (
            f"\rGen {generation_index + 1}/{self.generations} "
            f"[{bar}] {completed}/{total} {pct:>3}% "
            f"best_u={best_unsorted} best_o={best_overflow}"
        )
        sys.stdout.write(line)
        sys.stdout.flush()

    def _is_valid_course_for_student_slot(
        self,
        student: Student,
        course: Course | None,
        slot: int | None,
    ) -> bool:
        if course is None:
            return False

        if student.course_type_pref == CourseType.FULL:
            return slot is None and course.type == CourseType.FULL

        if slot == 0:
            return student.available_times[0] and course.type == CourseType.MORNING
        if slot == 1:
            return student.available_times[1] and course.type == CourseType.AFTERNOON
        return False

    def _safe_pref_index(self, prefs: list[Course], course: Course | None) -> int:
        if course is None:
            return 6
        try:
            return prefs.index(course)
        except ValueError:
            return 6

    def _random_full_assignment(self, student: Student, rng: random.Random) -> Course | None:
        prefs = student.prefs.get(CourseType.FULL, [])
        if not prefs:
            return None

        rank = min(int(rng.expovariate(1.0)), len(prefs) - 1)
        return prefs[rank]

    def _random_half_assignment(
        self, student: Student, rng: random.Random
    ) -> tuple[Course | None, Course | None]:
        morning: Course | None = None
        afternoon: Course | None = None

        if student.available_times[0]:
            prefs = student.prefs.get(CourseType.MORNING, [])
            if prefs:
                rank = min(int(rng.expovariate(1.0)), len(prefs) - 1)
                morning = prefs[rank]

        if student.available_times[1]:
            prefs = student.prefs.get(CourseType.AFTERNOON, [])
            if prefs:
                rank = min(int(rng.expovariate(1.0)), len(prefs) - 1)
                afternoon = prefs[rank]

        return (morning, afternoon)

    def _random_assignment(self, student: Student, rng: random.Random) -> Assignment:
        if student.course_type_pref == CourseType.FULL:
            return self._random_full_assignment(student, rng)
        return self._random_half_assignment(student, rng)

    def _first_choice_genome(self) -> Genome:
        genome: Genome = {}
        for student in self.students:
            if student.course_type_pref == CourseType.FULL:
                prefs = student.prefs.get(CourseType.FULL, [])
                genome[student] = prefs[0] if prefs else None
            else:
                morning = None
                afternoon = None
                if student.available_times[0]:
                    prefs = student.prefs.get(CourseType.MORNING, [])
                    morning = prefs[0] if prefs else None
                if student.available_times[1]:
                    prefs = student.prefs.get(CourseType.AFTERNOON, [])
                    afternoon = prefs[0] if prefs else None
                genome[student] = (morning, afternoon)
        return genome

    def _current_assignment_genome(self) -> Genome:
        genome: Genome = {}
        for student in self.students:
            if student.course_type_pref == CourseType.FULL:
                genome[student] = student.full_course
            else:
                genome[student] = (student.half_courses[0], student.half_courses[1])
        return genome

    def _perturb_genome(self, base: Genome, rng: random.Random, ratio: float) -> Genome:
        mutated = dict(base)
        count = max(1, int(len(self.students) * ratio))
        for student in rng.sample(self.students, min(count, len(self.students))):
            mutated[student] = self._random_assignment(student, rng)
        return mutated

    def _initial_population(
        self, rng: random.Random, greedy_seed: Genome | None = None
    ) -> list[Genome]:
        population: list[Genome] = []

        # Keep deterministic greedy-derived seeds at the front of the population.
        population.append(self._first_choice_genome())
        if greedy_seed is not None:
            population.append(dict(greedy_seed))
            population.append(self._perturb_genome(greedy_seed, rng, 0.03))
            population.append(self._perturb_genome(greedy_seed, rng, 0.07))
            population.append(self._perturb_genome(greedy_seed, rng, 0.12))

        while len(population) < self.population_size:
            genome: Genome = {}
            for student in self.students:
                genome[student] = self._random_assignment(student, rng)
            population.append(genome)

        return population

    def _set_half_slot(
        self,
        genome: Genome,
        student: Student,
        slot: int,
        value: Course | None,
    ) -> None:
        current = genome.get(student)
        if isinstance(current, tuple):
            morning, afternoon = current
        else:
            morning, afternoon = (None, None)

        if slot == 0:
            genome[student] = (value, afternoon)
        else:
            genome[student] = (morning, value)

    def _compatible_courses(self, student: Student, slot: int | None) -> list[Course]:
        if student.course_type_pref == CourseType.FULL:
            return [course for course in self.courses if course.type == CourseType.FULL]
        if slot == 0:
            return [course for course in self.courses if course.type == CourseType.MORNING]
        if slot == 1:
            return [course for course in self.courses if course.type == CourseType.AFTERNOON]
        return []

    def _least_loaded_course(
        self, candidates: list[Course], loads: dict[Course, int]
    ) -> Course | None:
        if not candidates:
            return None
        return min(candidates, key=lambda course: loads.get(course, 0))

    def _force_place_slot(
        self,
        genome: Genome,
        student: Student,
        slot: int | None,
        loads: dict[Course, int],
    ) -> bool:
        if student.course_type_pref == CourseType.FULL:
            prefs = student.prefs.get(CourseType.FULL, [])
            target = self._least_loaded_course(prefs, loads)
            if target is None:
                target = self._least_loaded_course(
                    self._compatible_courses(student, None), loads
                )
            if target is None:
                genome[student] = None
                return False
            genome[student] = target
            loads[target] += 1
            return True

        if slot == 0:
            if not student.available_times[0]:
                self._set_half_slot(genome, student, 0, None)
                return False
            prefs = student.prefs.get(CourseType.MORNING, [])
        elif slot == 1:
            if not student.available_times[1]:
                self._set_half_slot(genome, student, 1, None)
                return False
            prefs = student.prefs.get(CourseType.AFTERNOON, [])
        else:
            return False

        target = self._least_loaded_course(prefs, loads)
        if target is None:
            target = self._least_loaded_course(
                self._compatible_courses(student, slot), loads
            )

        if target is None:
            self._set_half_slot(genome, student, slot, None)
            return False

        self._set_half_slot(genome, student, slot, target)
        loads[target] += 1
        return True

    def _compute_course_loads(self, genome: Genome) -> dict[Course, int]:
        loads: dict[Course, int] = defaultdict(int)
        for student in self.students:
            assignment = genome.get(student)
            if student.course_type_pref == CourseType.FULL:
                if isinstance(assignment, Course) and assignment.type == CourseType.FULL:
                    loads[assignment] += 1
                continue

            if not isinstance(assignment, tuple):
                continue
            morning, afternoon = assignment
            if isinstance(morning, Course) and morning.type == CourseType.MORNING:
                loads[morning] += 1
            if isinstance(afternoon, Course) and afternoon.type == CourseType.AFTERNOON:
                loads[afternoon] += 1
        return loads

    def _try_place_slot(
        self,
        genome: Genome,
        student: Student,
        slot: int | None,
        loads: dict[Course, int],
    ) -> bool:
        if student.course_type_pref == CourseType.FULL:
            prefs = student.prefs.get(CourseType.FULL, [])
            for course in prefs:
                if loads[course] < course.capacity:
                    genome[student] = course
                    loads[course] += 1
                    return True
            genome[student] = None
            return False

        if slot == 0:
            if not student.available_times[0]:
                self._set_half_slot(genome, student, 0, None)
                return False
            prefs = student.prefs.get(CourseType.MORNING, [])
        elif slot == 1:
            if not student.available_times[1]:
                self._set_half_slot(genome, student, 1, None)
                return False
            prefs = student.prefs.get(CourseType.AFTERNOON, [])
        else:
            return False

        for course in prefs:
            if loads[course] < course.capacity:
                self._set_half_slot(genome, student, slot, course)
                loads[course] += 1
                return True

        self._set_half_slot(genome, student, slot, None)
        return False

    def _find_occupants(
        self, genome: Genome, target: Course, slot: int | None, limit: int = 16
    ) -> list[Student]:
        occupants: list[Student] = []
        for student in self.students:
            assignment = genome.get(student)
            if slot is None:
                if student.course_type_pref == CourseType.FULL and assignment is target:
                    occupants.append(student)
                    if len(occupants) >= limit:
                        break
                continue

            if student.course_type_pref == CourseType.FULL or not isinstance(assignment, tuple):
                continue
            course = assignment[slot]
            if course is target:
                occupants.append(student)
                if len(occupants) >= limit:
                    break
        return occupants

    def _swap_rescue(
        self,
        genome: Genome,
        student: Student,
        slot: int | None,
        loads: dict[Course, int],
    ) -> bool:
        if student.course_type_pref == CourseType.FULL:
            prefs = student.prefs.get(CourseType.FULL, [])
        elif slot == 0:
            prefs = student.prefs.get(CourseType.MORNING, [])
        elif slot == 1:
            prefs = student.prefs.get(CourseType.AFTERNOON, [])
        else:
            return False

        for desired in prefs[:4]:
            if loads[desired] < desired.capacity:
                continue

            desired_rank = self._safe_pref_index(prefs, desired)
            occupants = self._find_occupants(genome, desired, slot)
            if not occupants:
                continue

            # Try to displace a worse-ranked occupant into alternate capacity.
            occupants.sort(
                key=lambda occ: (
                    self._safe_pref_index(
                        occ.prefs.get(CourseType.FULL, [])
                        if occ.course_type_pref == CourseType.FULL
                        else occ.prefs.get(
                            CourseType.MORNING if slot == 0 else CourseType.AFTERNOON,
                            [],
                        ),
                        desired,
                    )
                ),
                reverse=True,
            )

            for occupant in occupants:
                if occupant is student:
                    continue

                occupant_prefs = (
                    occupant.prefs.get(CourseType.FULL, [])
                    if occupant.course_type_pref == CourseType.FULL
                    else occupant.prefs.get(
                        CourseType.MORNING if slot == 0 else CourseType.AFTERNOON,
                        [],
                    )
                )
                occupant_rank = self._safe_pref_index(occupant_prefs, desired)
                if occupant_rank <= desired_rank:
                    continue

                relocated = False
                for alt in occupant_prefs:
                    if alt is desired:
                        continue
                    if loads[alt] < alt.capacity:
                        if occupant.course_type_pref == CourseType.FULL:
                            genome[occupant] = alt
                        else:
                            self._set_half_slot(genome, occupant, slot if slot is not None else 0, alt)
                        loads[alt] += 1
                        loads[desired] -= 1
                        relocated = True
                        break

                if not relocated:
                    continue

                if student.course_type_pref == CourseType.FULL:
                    genome[student] = desired
                else:
                    self._set_half_slot(genome, student, slot if slot is not None else 0, desired)
                loads[desired] += 1
                return True

        return False

    def _repair_genome(self, genome: Genome) -> None:
        course_assignments: dict[Course, list[tuple[Student, int | None]]] = defaultdict(list)

        for student in self.students:
            assignment = genome.get(student)
            if student.course_type_pref == CourseType.FULL:
                if isinstance(assignment, Course) and assignment.type == CourseType.FULL:
                    course_assignments[assignment].append((student, None))
                continue

            if not isinstance(assignment, tuple):
                continue

            morning, afternoon = assignment
            if (
                student.available_times[0]
                and isinstance(morning, Course)
                and morning.type == CourseType.MORNING
            ):
                course_assignments[morning].append((student, 0))
            if (
                student.available_times[1]
                and isinstance(afternoon, Course)
                and afternoon.type == CourseType.AFTERNOON
            ):
                course_assignments[afternoon].append((student, 1))

        for course, assigned in course_assignments.items():
            overflow = len(assigned) - course.capacity
            if overflow <= 0:
                continue

            def rank_for(student: Student, slot: int | None) -> int:
                if student.course_type_pref == CourseType.FULL:
                    return self._safe_pref_index(
                        student.prefs.get(CourseType.FULL, []), course
                    )
                if slot == 0:
                    return self._safe_pref_index(
                        student.prefs.get(CourseType.MORNING, []), course
                    )
                return self._safe_pref_index(
                    student.prefs.get(CourseType.AFTERNOON, []), course
                )

            # Remove the worst-ranked occupants first.
            assigned.sort(key=lambda pair: rank_for(pair[0], pair[1]), reverse=True)
            for student, slot in assigned[:overflow]:
                if slot is None:
                    genome[student] = None
                else:
                    self._set_half_slot(genome, student, slot, None)

        # Multi-pass refill with swap rescue for harder placements.
        for pass_idx in range(3):
            loads = self._compute_course_loads(genome)
            changed = False

            for student in self.students:
                assignment = genome.get(student)
                if student.course_type_pref == CourseType.FULL:
                    if not (
                        isinstance(assignment, Course)
                        and assignment.type == CourseType.FULL
                    ):
                        if self._try_place_slot(genome, student, None, loads):
                            changed = True
                        elif pass_idx == 2 and self._swap_rescue(genome, student, None, loads):
                            changed = True
                    continue

                morning, afternoon = (
                    assignment if isinstance(assignment, tuple) else (None, None)
                )

                if student.available_times[0] and not (
                    isinstance(morning, Course) and morning.type == CourseType.MORNING
                ):
                    if self._try_place_slot(genome, student, 0, loads):
                        changed = True
                    elif pass_idx == 2 and self._swap_rescue(genome, student, 0, loads):
                        changed = True

                if student.available_times[1] and not (
                    isinstance(afternoon, Course)
                    and afternoon.type == CourseType.AFTERNOON
                ):
                    if self._try_place_slot(genome, student, 1, loads):
                        changed = True
                    elif pass_idx == 2 and self._swap_rescue(genome, student, 1, loads):
                        changed = True

            if not changed:
                break

        # Final force-fill: no voluntary unsorted state in GA mode.
        loads = self._compute_course_loads(genome)
        for student in self.students:
            assignment = genome.get(student)
            if student.course_type_pref == CourseType.FULL:
                if not (
                    isinstance(assignment, Course)
                    and assignment.type == CourseType.FULL
                ):
                    self._force_place_slot(genome, student, None, loads)
                continue

            morning, afternoon = (
                assignment if isinstance(assignment, tuple) else (None, None)
            )
            if student.available_times[0] and not (
                isinstance(morning, Course) and morning.type == CourseType.MORNING
            ):
                self._force_place_slot(genome, student, 0, loads)

            if student.available_times[1] and not (
                isinstance(afternoon, Course)
                and afternoon.type == CourseType.AFTERNOON
            ):
                self._force_place_slot(genome, student, 1, loads)

    def _evaluate_components(self, genome: Genome) -> EvalMetrics:
        course_loads: dict[Course, int] = defaultdict(int)
        unsorted_students = 0
        total_score = 0.0
        scored_students = 0
        worst_score_students = 0

        for student in self.students:
            assignment = genome.get(student)

            if student.course_type_pref == CourseType.FULL:
                if isinstance(assignment, Course) and assignment.type == CourseType.FULL:
                    course_loads[assignment] += 1
                    score = self._safe_pref_index(
                        student.prefs.get(CourseType.FULL, []), assignment
                    )
                    total_score += score
                    scored_students += 1
                    if score >= 6:
                        worst_score_students += 1
                else:
                    unsorted_students += 1
                continue

            morning, afternoon = (
                assignment if isinstance(assignment, tuple) else (None, None)
            )
            slot_scores: list[float] = []
            assigned_any = False

            if student.available_times[0]:
                if isinstance(morning, Course) and morning.type == CourseType.MORNING:
                    course_loads[morning] += 1
                    score = self._safe_pref_index(
                        student.prefs.get(CourseType.MORNING, []), morning
                    )
                    slot_scores.append(score)
                    assigned_any = True
                else:
                    slot_scores.append(6)

            if student.available_times[1]:
                if (
                    isinstance(afternoon, Course)
                    and afternoon.type == CourseType.AFTERNOON
                ):
                    course_loads[afternoon] += 1
                    score = self._safe_pref_index(
                        student.prefs.get(CourseType.AFTERNOON, []), afternoon
                    )
                    slot_scores.append(score)
                    assigned_any = True
                else:
                    slot_scores.append(6)

            if assigned_any and slot_scores:
                student_score = sum(slot_scores) / len(slot_scores)
                total_score += student_score
                scored_students += 1
                if student_score >= 6:
                    worst_score_students += 1
            else:
                unsorted_students += 1

        overflow = 0
        for course in self.courses:
            overflow += max(0, course_loads.get(course, 0) - course.capacity)

        avg_score = total_score / scored_students if scored_students else 6
        return (unsorted_students, overflow, avg_score, worst_score_students)

    def _evaluate_genome(self, genome: Genome) -> float:
        unsorted_students, overflow, avg_score, worst_score_students = (
            self._evaluate_components(genome)
        )

        # Fitness is retained for debugging/inspection; selection uses lexicographic ranking.
        penalty = (
            100000 * unsorted_students
            + 10000 * overflow
            + 100 * avg_score
            + 50 * worst_score_students
        )
        return -penalty

    def _sort_key(self, metrics: EvalMetrics) -> tuple[int, int, float, int]:
        # Lexicographic objective: unsorted first, then overflow, then average score, then tail.
        return metrics

    def _tournament_select(
        self, ranked_population: list[tuple[EvalMetrics, Genome]], rng: random.Random
    ) -> Genome:
        k = min(5, len(ranked_population))
        sample = rng.sample(ranked_population, k)
        sample.sort(key=lambda pair: self._sort_key(pair[0]))
        return sample[0][1]

    def _crossover(self, parent_a: Genome, parent_b: Genome, rng: random.Random) -> Genome:
        child: Genome = {}
        for student in self.students:
            child[student] = (
                parent_a[student] if rng.random() < 0.5 else parent_b[student]
            )
        return child

    def _mutate(self, genome: Genome, rng: random.Random) -> None:
        for student in self.students:
            if rng.random() < self.mutation_rate:
                genome[student] = self._random_assignment(student, rng)

    def _apply_genome(self, genome: Genome) -> None:
        self._reset_assignment_state()
        loads: dict[Course, int] = defaultdict(int)

        for student in self.students:
            assignment = genome.get(student)

            if student.course_type_pref == CourseType.FULL:
                target = assignment if isinstance(assignment, Course) else None
                if not self._is_valid_course_for_student_slot(student, target, None):
                    target = self._least_loaded_course(
                        student.prefs.get(CourseType.FULL, []), loads
                    )
                if target is None:
                    target = self._least_loaded_course(
                        self._compatible_courses(student, None), loads
                    )
                if target is not None:
                    student.add_course_full(target)
                    loads[target] += 1
                continue

            morning, afternoon = (
                assignment if isinstance(assignment, tuple) else (None, None)
            )

            if student.available_times[0]:
                morning_target = morning if isinstance(morning, Course) else None
                if not self._is_valid_course_for_student_slot(student, morning_target, 0):
                    morning_target = self._least_loaded_course(
                        student.prefs.get(CourseType.MORNING, []), loads
                    )
                if morning_target is None:
                    morning_target = self._least_loaded_course(
                        self._compatible_courses(student, 0), loads
                    )
                if morning_target is not None:
                    student.add_course_morning(morning_target)
                    loads[morning_target] += 1

            if student.available_times[1]:
                afternoon_target = afternoon if isinstance(afternoon, Course) else None
                if not self._is_valid_course_for_student_slot(student, afternoon_target, 1):
                    afternoon_target = self._least_loaded_course(
                        student.prefs.get(CourseType.AFTERNOON, []), loads
                    )
                if afternoon_target is None:
                    afternoon_target = self._least_loaded_course(
                        self._compatible_courses(student, 1), loads
                    )
                if afternoon_target is not None:
                    student.add_course_afternoon(afternoon_target)
                    loads[afternoon_target] += 1

    def _build_meta(self) -> None:
        def course_is_overpopulated(course: Course) -> bool:
            return course.is_over_capacity() and course.num_students() > 0

        scored_students = list(self.students)
        scores = [student.score() for student in scored_students]
        total_score: float = sum(scores)
        avg_score: float = total_score / len(scores) if scores else 0

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
            "algorithm": "ga",
            "population_size": self.population_size,
            "generations": self.generations,
            "mutation_rate": self.mutation_rate,
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

    def sort(self, raw_data: RawData) -> None:
        self.students = raw_data.students
        self.courses = raw_data.courses

        rng = random.Random(self.seed)
        # Build a greedy-derived seed genome before GA initialization.
        greedy_solver = Sorter()
        greedy_solver.sort(raw_data)
        greedy_seed = self._current_assignment_genome()
        self._reset_assignment_state()

        population = self._initial_population(rng, greedy_seed=greedy_seed)
        elite_count = max(1, int(self.population_size * self.elite_fraction))
        generation_best: list[dict[str, float | int]] = []

        for i in range(self.generations):
            ranked = [
                (self._evaluate_components(genome), genome)
                for genome in population
            ]
            ranked.sort(key=lambda pair: self._sort_key(pair[0]))

            best_unsorted, best_overflow, best_avg, best_worst = ranked[0][0]
            generation_best.append(
                {
                    "unsorted": best_unsorted,
                    "overflow": best_overflow,
                    "avg_score": round(best_avg, 3),
                    "worst_score_students": best_worst,
                }
            )

            next_population: list[Genome] = [
                dict(ranked[i][1]) for i in range(min(elite_count, len(ranked)))
            ]

            self._print_generation_progress(
                i,
                len(next_population),
                self.population_size,
                best_unsorted,
                best_overflow,
            )

            current_best_unsorted = ranked[0][0][0]
            current_best_overflow = ranked[0][0][1]
            unsorted_threshold = current_best_unsorted + self.feasibility_unsorted_slack
            overflow_threshold = current_best_overflow + self.feasibility_overflow_slack

            while len(next_population) < self.population_size:
                accepted = False
                fallback_child: Genome | None = None
                best_child_metrics: EvalMetrics | None = None

                for _ in range(6):
                    parent_a = self._tournament_select(ranked, rng)
                    parent_b = self._tournament_select(ranked, rng)
                    child = self._crossover(parent_a, parent_b, rng)
                    self._mutate(child, rng)
                    self._repair_genome(child)

                    metrics = self._evaluate_components(child)
                    if best_child_metrics is None or self._sort_key(metrics) < self._sort_key(best_child_metrics):
                        fallback_child = child
                        best_child_metrics = metrics

                    if metrics[0] <= unsorted_threshold and metrics[1] <= overflow_threshold:
                        next_population.append(child)
                        accepted = True
                        break

                if not accepted and fallback_child is not None:
                    next_population.append(fallback_child)

                self._print_generation_progress(
                    i,
                    len(next_population),
                    self.population_size,
                    best_unsorted,
                    best_overflow,
                )

            population = next_population
            sys.stdout.write("\n")

        ranked = [(self._evaluate_components(genome), genome) for genome in population]
        ranked.sort(key=lambda pair: self._sort_key(pair[0]))
        best_genome = ranked[0][1]

        self._repair_genome(best_genome)
        self._apply_genome(best_genome)
        self._build_meta()
        self.meta["ga_generation_best"] = generation_best[-1]

    def get_raw_data(self) -> RawData:
        d = RawData(self.students, self.courses + [self.unsorted_class])
        d.meta = self.meta
        return d
