"""Finish the versioned experiment and build the portfolio in delivery order."""
import fcntl
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN = ROOT / "data/derived/tree_comparison_v1"
TABLES = ROOT / "reports/tables/tree_comparison_v1"


def command(name, environment):
    subprocess.run([sys.executable, str(HERE / name)], cwd=ROOT, env=environment, check=True)


def main():
    RUN.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="8", PYTHONDONTWRITEBYTECODE="1")
    environment.setdefault("MPLCONFIGDIR", str(RUN / "matplotlib"))
    with (RUN / "portfolio.lock").open("a") as finish_lock:
        fcntl.flock(finish_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        # A live trainer owns this lock. Wait for its checkpoints before checking the run.
        with (RUN / "run.lock").open("a") as training_lock:
            fcntl.flock(training_lock, fcntl.LOCK_EX)
        outputs = [TABLES / f"{name}.csv" for name in
                   ("development_grid", "development_metrics", "stress_metrics",
                    "stress_calibration", "permutation_importance")]
        if not all(path.is_file() for path in outputs):
            command("run.py", environment)
        command("validate.py", environment)
        command("portfolio.py", environment)
        command("build_brief.py", environment)
        command("build_story.py", environment)


if __name__ == "__main__":
    main()
