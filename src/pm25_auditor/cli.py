from pathlib import Path

from .pipeline import run_auditor


def main() -> None:
    run_auditor(Path(__file__).resolve().parents[2])


if __name__ == "__main__":
    main()

