from faker import Faker
import pandas as pd
import sys
import random
from collections import defaultdict

# Initialize Faker
fake = Faker()

def build_course_pools(class_file: pd.DataFrame):
    morning_courses = []
    afternoon_courses = []
    full_courses = []
    courses_by_subject = defaultdict(lambda: {"Morning": [], "Afternoon": [], "Full": []})
    course_rows = []

    for _, row in class_file.iterrows():
        name = row["Name"]
        teacher = row["Teacher"]
        capacity = row["Capacity"]
        course_type = row["Type"]

        base_subject = name.rsplit("_", 1)[0]
        course_rows.append((name, teacher, capacity, course_type, base_subject))

        if course_type == "Morning":
            morning_courses.append(name)
        elif course_type == "Afternoon":
            afternoon_courses.append(name)
        elif course_type == "Full":
            full_courses.append(name)

        courses_by_subject[base_subject][course_type].append(name)

    return morning_courses, afternoon_courses, full_courses, courses_by_subject, course_rows

class_file = pd.read_csv(sys.argv[3])
morning_courses, afternoon_courses, full_courses, courses_by_subject, course_rows = build_course_pools(class_file)

subjects = sorted({subject for subject in courses_by_subject.keys()})


def preferred_course_list(pool: list[str], count: int) -> list[str]:
    if not pool:
        return ["" for _ in range(count)]
    if len(pool) >= count:
        return random.sample(pool, count)
    chosen = list(pool)
    while len(chosen) < count:
        chosen.append(random.choice(pool))
    return chosen


def pick_weighted(pool: list[str], emphasis: list[str], count: int) -> list[str]:
    if not pool:
        return ["" for _ in range(count)]
    weighted = list(pool)
    if emphasis:
        weighted.extend(emphasis * 3)
    chosen = []
    seen = set()
    attempts = 0
    while len(chosen) < count and attempts < count * 12:
        attempts += 1
        candidate = random.choice(weighted)
        if candidate in seen:
            continue
        seen.add(candidate)
        chosen.append(candidate)
    while len(chosen) < count:
        candidate = random.choice(pool)
        if candidate in seen:
            continue
        seen.add(candidate)
        chosen.append(candidate)

    while len(chosen) < count:
        chosen.append(random.choice(pool))
    return chosen


# Define function to create a fake student
def create_fake_student():
    first_name = fake.first_name()
    last_name = fake.last_name()
    grade = random.randint(9, 12)

    # Availability in the current loader means:
    # - Morning -> afternoon-only
    # - Afternoon -> morning-only
    # - None -> both slots available
    cte_or_btc = random.choices(
        ["Morning", "Afternoon", "None"],
        weights=[0.16, 0.16, 0.68],
        k=1,
    )[0]
    pref_class_type = random.choices(["Half", "Full"], weights=[0.62, 0.38], k=1)[0]

    # Give students a small thematic cluster so preferences look human rather than uniform.
    focus_subjects = random.sample(subjects, k=min(2, len(subjects))) if subjects else []
    focus_courses = []
    for subject in focus_subjects:
        focus_courses.extend(courses_by_subject[subject]["Morning"])
        focus_courses.extend(courses_by_subject[subject]["Afternoon"])
        focus_courses.extend(courses_by_subject[subject]["Full"])

    morning_pool = morning_courses
    afternoon_pool = afternoon_courses
    full_pool = full_courses

    morning_prefs = pick_weighted(morning_pool, focus_courses, 5)
    afternoon_prefs = pick_weighted(afternoon_pool, focus_courses, 5)
    full_prefs = pick_weighted(full_pool, focus_courses, 5)

    # Occasionally create a more one-sided preference profile for realism.
    if random.random() < 0.18:
        morning_prefs = preferred_course_list(morning_pool, 5)
    if random.random() < 0.18:
        afternoon_prefs = preferred_course_list(afternoon_pool, 5)
    if random.random() < 0.12:
        full_prefs = preferred_course_list(full_pool, 5)

    return {
        "First Name": first_name,
        "Last Name": last_name,
        "Grade": grade,
        "Pref Class Type": pref_class_type,
        "CTE or BTC": cte_or_btc,
        "Morning Pref 1": morning_prefs[0],
        "Morning Pref 2": morning_prefs[1],
        "Morning Pref 3": morning_prefs[2],
        "Morning Pref 4": morning_prefs[3],
        "Morning Pref 5": morning_prefs[4],
        "Afternoon Pref 1": afternoon_prefs[0],
        "Afternoon Pref 2": afternoon_prefs[1],
        "Afternoon Pref 3": afternoon_prefs[2],
        "Afternoon Pref 4": afternoon_prefs[3],
        "Afternoon Pref 5": afternoon_prefs[4],
        "Full Pref 1": full_prefs[0],
        "Full Pref 2": full_prefs[1],
        "Full Pref 3": full_prefs[2],
        "Full Pref 4": full_prefs[3],
        "Full Pref 5": full_prefs[4],
    }


seed = int(sys.argv[4]) if len(sys.argv) > 4 else None
if seed is not None:
    random.seed(seed)
    Faker.seed(seed)

# Generate a list of fake students
fake_students = [create_fake_student() for _ in range(int(sys.argv[1]))]

# Create DataFrame
fake_students_df = pd.DataFrame(fake_students)

# Save to CSV
fake_students_df.to_csv(sys.argv[2], index=False)
