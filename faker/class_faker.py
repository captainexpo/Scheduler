from faker import Faker
import sys
import random
import csv

fake = Faker()

TYPES = ["Morning", "Afternoon", "Full"]

# A slightly more realistic course catalog: broad academic subjects, some electives,
# and a few career-oriented options. The weights make common offerings appear more often.
COURSE_CATALOG = [
    ("Math", 12),
    ("English", 11),
    ("Science", 11),
    ("History", 10),
    ("Computer Science", 10),
    ("Biology", 9),
    ("Chemistry", 9),
    ("Physics", 9),
    ("Art", 8),
    ("Music", 8),
    ("Psychology", 8),
    ("Economics", 8),
    ("Statistics", 7),
    ("Geography", 7),
    ("Sociology", 7),
    ("Political Science", 7),
    ("Business Studies", 7),
    ("French", 6),
    ("Philosophy", 6),
    ("Drama", 6),
    ("Environmental Science", 6),
    ("Engineering", 5),
    ("Graphic Design", 5),
    ("Law", 5),
    ("Medicine", 5),
    ("Anthropology", 5),
    ("Linguistics", 5),
    ("Architecture", 4),
    ("Robotics", 4),
    ("Data Science", 4),
    ("Creative Writing", 4),
    ("Journalism", 4),
    ("Marketing", 4),
    ("Sports Science", 4),
    ("Astronomy", 3),
]

TYPE_WEIGHTS = {"Morning": 0.34, "Afternoon": 0.32, "Full": 0.34}

TYPE_CAPACITY_RANGES = {
    "Morning": (18, 28),
    "Afternoon": (18, 28),
    "Full": (20, 32),
}


def generate_courses(num_courses: int):
    courses = []
    used_names = set()

    for _ in range(num_courses):
        name = random.choices(
            [item[0] for item in COURSE_CATALOG],
            weights=[item[1] for item in COURSE_CATALOG],
            k=1,
        )[0]
        f_num = 1
        while f"{name}_{f_num}" in used_names:
            f_num += 1
        name = f"{name}_{f_num}"
        used_names.add(name)

        teacher = fake.name()
        course_type = random.choices(
            TYPES,
            weights=[TYPE_WEIGHTS[t] for t in TYPES],
            k=1,
        )[0]
        capacity = random.randint(*TYPE_CAPACITY_RANGES[course_type])

        courses.append(
            {
                "Name": name,
                "Teacher": teacher,
                "Capacity": capacity,
                "Type": course_type,
            }
        )

    return courses


def write_courses_to_csv(filename="fake_courses.csv"):
    seed = None
    if len(sys.argv) > 2:
        if len(sys.argv) == 3 and sys.argv[2].isdigit():
            seed = int(sys.argv[2])
            filename = "fake_courses.csv"
        else:
            filename = sys.argv[2]
            if len(sys.argv) > 3 and sys.argv[3].isdigit():
                seed = int(sys.argv[3])
    if seed is not None:
        random.seed(seed)
        Faker.seed(seed)
    courses = generate_courses(int(sys.argv[1]))
    with open(filename, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Name", "Teacher", "Capacity", "Type"])
        writer.writeheader()
        writer.writerows(courses)


if __name__ == "__main__":
    write_courses_to_csv()
