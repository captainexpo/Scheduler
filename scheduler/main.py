import argparse
import scheduler.dataloader as dataloader
import scheduler.sorter as sorter
import scheduler.course as course
import scheduler.student as student
import scheduler.data as data


def main(student_csv: str, classes_csv: str, output_file: str):
    raw_data: data.RawData = dataloader.load_data(student_csv, classes_csv)
    with open(output_file, "w") as f:
        f.write(str(raw_data))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process two CSV input files.")
    parser.add_argument("classes", type=str, help="Path to the Class CSV file")
    parser.add_argument("students", type=str, help="Path to the Student CSV file")
    parser.add_argument(
        "--output", default="out.txt", type=str, help="Path to the output file"
    )
    args = parser.parse_args()

    main(args.students, args.classes, args.output)
