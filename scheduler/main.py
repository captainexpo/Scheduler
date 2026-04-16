import argparse
import scheduler.dataloader as dataloader
import scheduler.data as data

def main(
    student_csv: str,
    classes_csv: str,
    output_file: str,
    algorithm: str = "greedy",
    ga_population: int = 60,
    ga_generations: int = 60,
    ga_mutation: float = 0.08,
    ga_seed: int | None = None,
):
    raw_data: data.RawData = dataloader.load_data(student_csv, classes_csv)

    if algorithm == "ga":
        import scheduler.ga_sorter as ga_sorter
        s = ga_sorter.GASorter(
            population_size=ga_population,
            generations=ga_generations,
            mutation_rate=ga_mutation,
            seed=ga_seed,
        )
    elif algorithm == "lp":
        from scheduler.lp_sorter import LPSorter
        s = LPSorter()
    else:
        import scheduler.sorter as sorter
        s = sorter.Sorter()

    s.sort(raw_data)
    raw_data = s.get_raw_data()
    print(raw_data.meta)
    with open(output_file, "w") as f:
        f.write(str(raw_data))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YES class scheduler.")
    parser.add_argument("classes", type=str, help="Path to the Class CSV file")
    parser.add_argument("students", type=str, help="Path to the Student CSV file")
    parser.add_argument(
        "--output", default="out.txt", type=str, help="Path to the output file"
    )
    parser.add_argument(
        "--algorithm",
        choices=["greedy", "ga", "lp"],
        default="greedy",
        help="Scheduling algorithm to use",
    )
    parser.add_argument(
        "--ga-population",
        default=60,
        type=int,
        help="GA population size (only used with --algorithm ga)",
    )
    parser.add_argument(
        "--ga-generations",
        default=60,
        type=int,
        help="GA generation count (only used with --algorithm ga)",
    )
    parser.add_argument(
        "--ga-mutation",
        default=0.08,
        type=float,
        help="GA mutation rate in [0, 1] (only used with --algorithm ga)",
    )
    parser.add_argument(
        "--ga-seed",
        default=None,
        type=int,
        help="Random seed for GA reproducibility (only used with --algorithm ga)",
    )
    args = parser.parse_args()

    main(
        args.students,
        args.classes,
        args.output,
        algorithm=args.algorithm,
        ga_population=args.ga_population,
        ga_generations=args.ga_generations,
        ga_mutation=args.ga_mutation,
        ga_seed=args.ga_seed,
    )
