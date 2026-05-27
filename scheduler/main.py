import argparse
from pathlib import Path

import scheduler.dataloader as dataloader
import scheduler.data as data
import json


def run_scheduler(
    student_csv: str,
    classes_csv: str,
    algorithm: str = "lp",
    lp_opts: dict[str, object] | None = None,
) -> tuple[data.RawData, str]:
    raw_data: data.RawData = dataloader.load_data(student_csv, classes_csv)

    if algorithm == "lp":
        from scheduler.lp_sorter import LPSorter

        sorter = LPSorter(lp_opts)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    sorter.sort(raw_data)
    solved_data = sorter.get_raw_data()
    return solved_data, solved_data.as_text_output(format="csv")


def main(
    student_csv: str,
    classes_csv: str,
    output_file: str,
    lp_opts: dict[str, object] | None = None,
    output_json: bool = False,
    algorithm: str = "lp",
):
    solved_data, csv_output = run_scheduler(
        student_csv, classes_csv, algorithm=algorithm, lp_opts=lp_opts
    )
    print(solved_data.meta)
    Path(output_file).write_text(csv_output)

    if output_json:
        json_output = solved_data.as_json()
        json_output_file = output_file.rsplit(".", 1)[0] + ".json"
        Path(json_output_file).write_text(json.dumps(json_output, indent=4))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YES class scheduler.")
    parser.add_argument("classes", type=str, help="Path to the Class CSV file")
    parser.add_argument("students", type=str, help="Path to the Student CSV file")
    parser.add_argument(
        "--output", default="out.csv", type=str, help="Path to the output file"
    )
    parser.add_argument(
        "--algorithm",
        choices=["lp"],
        default="lp",
        help="Scheduling algorithm to use",
    )
    parser.add_argument(
        "--preference-objective-weight",
        type=float,
        default=1.0,
        help="Weight for the preference objective in the optimization",
    )
    parser.add_argument(
        "--grade-balance-objective-weight",
        type=float,
        default=0.0,
        help="Weight for the grade balance objective in the optimization",
    )
    parser.add_argument(
        "--output-json",
        action="store_true",
        help="Whether to output the solved data as JSON in addition to csv",
    )
    args = parser.parse_args()

    lp_opts = {
        "preference_weight": args.preference_objective_weight,
        "grade_mixing_weight": args.grade_balance_objective_weight,
    }
    print(f"Running with LP options: {lp_opts}")
    main(
        args.students,
        args.classes,
        args.output,
        lp_opts,
        output_json=args.output_json,
        algorithm=args.algorithm,
    )
