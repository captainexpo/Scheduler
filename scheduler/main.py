import argparse
from pathlib import Path

import scheduler.dataloader as dataloader
import scheduler.data as data

def run_scheduler(
    student_csv: str,
    classes_csv: str,
    algorithm: str = "lp",
) -> tuple[data.RawData, str]:
    raw_data: data.RawData = dataloader.load_data(student_csv, classes_csv)

    if algorithm == "lp":
        from scheduler.lp_sorter import LPSorter
        sorter = LPSorter()
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    sorter.sort(raw_data)
    solved_data = sorter.get_raw_data()
    return solved_data, solved_data.as_text_output(format="csv")


def main(
    student_csv: str,
    classes_csv: str,
    output_file: str,
    algorithm: str = "lp",
):
    solved_data, csv_output = run_scheduler(student_csv, classes_csv, algorithm=algorithm)
    print(solved_data.meta)
    Path(output_file).write_text(csv_output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YES class scheduler.")
    parser.add_argument("classes", type=str, help="Path to the Class CSV file")
    parser.add_argument("students", type=str, help="Path to the Student CSV file")
    parser.add_argument(
        "--output", default="out.txt", type=str, help="Path to the output file"
    )
    parser.add_argument(
        "--algorithm",
        choices=["lp"],
        default="lp",
        help="Scheduling algorithm to use",
    )
    args = parser.parse_args()

    main(
        args.students,
        args.classes,
        args.output,
        algorithm=args.algorithm,
    )
