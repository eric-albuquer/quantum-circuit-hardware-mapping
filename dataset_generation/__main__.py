import argparse
import logging

from dataset_generation.benchmarks import generate_benchmarks
from dataset_generation.random_circuits import generate_random_circuits
from dataset_generation.weighted_topologies import generate_weighted_topologies


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate quantum circuit and topology datasets.")
    parser.add_argument(
        "dataset",
        choices=("all", "algorithms", "random", "topologies"),
        nargs="?",
        default="all",
        help="Dataset category to generate (default: all).",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    generators = {
        "algorithms": generate_benchmarks,
        "random": generate_random_circuits,
        "topologies": generate_weighted_topologies,
    }
    selected = generators.values() if args.dataset == "all" else (generators[args.dataset],)
    for generate in selected:
        generate()


if __name__ == "__main__":
    main()
