from faker import Faker
import pandas as pd
import sys
import random

# Initialize Faker
fake = Faker()

# Define available preferences
morning_courses = [
    "Geography",
    "Psychology",
    "Physics",
    "Drama",
    "Math",
    "English",
    "German",
]
afternoon_courses = [
    "French",
    "Economics",
    "Physical Education",
    "Chemistry",
    "Science",
    "Art",
]
full_courses = [
    "History",
    "Biology",
    "Computer Science",
    "Music",
    "Philosophy",
    "Spanish",
]


# Define function to create a fake student
def create_fake_student():
    first_name = fake.first_name()
    last_name = fake.last_name()
    grade = random.randint(9, 12)
    cte_or_btc_weights = [
        0.1,
        0.1,
        0.8,
    ]  # Weights for "Morning", "Afternoon", "None", None
    cte_or_btc = random.choices(
        ["Morning", "Afternoon", "None"],
        weights=cte_or_btc_weights,
        k=1,
    )[0]
    pref_class_type = (
        random.choice(["Half", "Full"]) if cte_or_btc == "None" else "Half"
    )

    morning_prefs = random.sample(morning_courses, 5)
    afternoon_prefs = random.sample(afternoon_courses, 5)
    full_prefs = random.sample(full_courses, 5)

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


# Generate a list of 30 fake students
fake_students = [create_fake_student() for _ in range(int(sys.argv[1]))]

# Create DataFrame
fake_students_df = pd.DataFrame(fake_students)

# Save to CSV
fake_students_df.to_csv("data/faker/fake_students.csv", index=False)
