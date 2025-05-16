from faker import Faker
import random
import csv

fake = Faker()

TYPES = ["Morning", "Afternoon", "Full"]
COURSE_NAMES = [
    "Math",
    "English",
    "Physics",
    "Geography",
    "Psychology",
    "Science",
    "Art",
    "Chemistry",
    "Sociology",
    "French",
    "History",
    "Music",
    "Biology",
    "Philosophy",
    "Computer Science",
    "Economics",
    "Drama",
    "Statistics",
    "Astronomy",
    "Environmental Science",
    "Political Science",
    "Engineering",
    "Business Studies",
    "Graphic Design",
    "Law",
    "Medicine",
    "Anthropology",
    "Linguistics",
    "Architecture",
    "Robotics",
    "Data Science",
    "Creative Writing",
    "Journalism",
    "Marketing",
    "Sports Science",
]


def generate_courses():
    courses = []
    used_names = set()

    while len(used_names) < len(COURSE_NAMES):
        name = random.choice(COURSE_NAMES)
        if name in used_names:
            continue
        used_names.add(name)

        teacher = fake.name()
        capacity = random.randint(15, 30)
        course_type = random.choice(TYPES)

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
    courses = generate_courses()
    with open(filename, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Name", "Teacher", "Capacity", "Type"])
        writer.writeheader()
        writer.writerows(courses)


if __name__ == "__main__":
    write_courses_to_csv()
