"""Reproduce collision EDA after checking the preparation validation receipt."""
import argparse
import hashlib
import json
from pathlib import Path

# Dictionary-validated domain codes & standard sentinels for NCDB microdata
DICTIONARY_DOMAINS: dict[str, set[str]] = {
    "C_SEV": {"1", "2", "01", "02", "U", "X"},
    "C_MNTH": {str(i) for i in range(1, 13)} | {f"{i:02d}" for i in range(1, 13)} | {"UU", "XX", "U", "X"},
    "C_WDAY": {str(i) for i in range(1, 8)} | {f"{i:02d}" for i in range(1, 8)} | {"U", "X"},
    "C_HOUR": {str(i) for i in range(24)} | {f"{i:02d}" for i in range(24)} | {"UU", "XX", "U", "X"},
    "C_RCFG": {str(i) for i in range(1, 13)} | {f"{i:02d}" for i in range(1, 13)} | {"QQ", "UU", "XX", "Q", "U", "X"},
    "C_WTHR": {str(i) for i in range(1, 8)} | {f"{i:02d}" for i in range(1, 8)} | {"Q", "U", "X", "QQ", "UU", "XX"},
    "C_RSUR": {str(i) for i in range(1, 10)} | {f"{i:02d}" for i in range(1, 10)} | {"Q", "U", "X", "QQ", "UU", "XX"},
    "C_RALN": {str(i) for i in range(1, 7)} | {f"{i:02d}" for i in range(1, 7)} | {"Q", "U", "X", "QQ", "UU", "XX"},
    "C_TRAF": {str(i) for i in range(1, 19)} | {f"{i:02d}" for i in range(1, 19)} | {"QQ", "UU", "XX", "Q", "U", "X"},
    "C_CONF": {
        "1", "2", "3", "4", "5", "6", "21", "22", "23", "24", "25", "31", "32", "33", "34", "35", "36", "41",
        "01", "02", "03", "04", "05", "06", "QQ", "UU", "XX", "Q", "U", "X",
    },
    "C_VEHS": {str(i) for i in range(1, 100)} | {f"{i:02d}" for i in range(1, 100)} | {"UU", "XX", "U", "X"},
    "V_ID": {str(i) for i in range(1, 100)} | {f"{i:02d}" for i in range(1, 100)} | {"UU", "XX", "NN", "U", "X", "N", "99"},
    "V_TYPE": {
        "1", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "16", "17", "18", "19", "20", "21", "22", "23",
        "01", "05", "06", "07", "08", "09", "NN", "N", "UU", "U", "XX", "X", "QQ", "Q",
    },
    "P_ID": {str(i) for i in range(1, 100)} | {f"{i:02d}" for i in range(1, 100)} | {"UU", "XX", "NN", "U", "X", "N", "99"},
    "P_USER": {"1", "2", "3", "4", "5", "01", "02", "03", "04", "05", "U", "UU", "X", "XX", "Q", "QQ", "N", "NN"},
}



def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_inputs(root):
    receipt_path = root / 'data/derived/prepared_validation.json'
    receipt = json.loads(receipt_path.read_text())
    if receipt['status'] != 'passed' or receipt['failures']:
        raise ValueError('Collision preparation has not passed validation')
    for relative, expected in receipt['input_fingerprints'].items():
        if sha256(root / relative) != expected:
            raise ValueError(f'Stale preparation validation: {relative}')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.root.resolve()
    verify_inputs(root)
    from . import analyze_temporal, analyze_conditions, analyze_stability
    for analysis in (analyze_temporal, analyze_conditions, analyze_stability):
        analysis.run(root)
    from .validate_exploration import validate
    result = validate(root)
    print(json.dumps(result, indent=2))
    if result['status'] != 'passed':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
