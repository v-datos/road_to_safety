"""Reproduce collision EDA after checking the preparation validation receipt."""
import argparse
import hashlib
import json
from pathlib import Path


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
