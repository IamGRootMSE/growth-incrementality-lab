"""Compare regenerated JSON with a committed snapshot, tolerating only roundoff."""
import argparse
import json
import math
from pathlib import Path


def compare(expected, actual, path='$'):
    # Booleans are not numbers for schema purposes; counts remain exact integers.
    if type(expected) is not type(actual):
        raise AssertionError(f'{path}: type changed')
    if isinstance(expected, dict):
        if expected.keys() != actual.keys():
            raise AssertionError(f'{path}: keys changed')
        for key in expected:
            compare(expected[key], actual[key], f'{path}.{key}')
    elif isinstance(expected, list):
        if len(expected) != len(actual):
            raise AssertionError(f'{path}: length changed')
        for i, (a, b) in enumerate(zip(expected, actual)):
            compare(a, b, f'{path}[{i}]')
    elif isinstance(expected, float):
        if not (math.isfinite(expected) and math.isfinite(actual)
                and math.isclose(expected, actual, rel_tol=1e-12, abs_tol=1e-12)):
            raise AssertionError(f'{path}: numeric drift: {expected} != {actual}')
    elif expected != actual:
        raise AssertionError(f'{path}: value changed: {expected!r} != {actual!r}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('expected', type=Path)
    parser.add_argument('actual', type=Path)
    args = parser.parse_args()
    compare(json.loads(args.expected.read_text(encoding='utf-8')),
            json.loads(args.actual.read_text(encoding='utf-8')))
    print('Snapshot matches: exact schema, strings, counts and hashes; floats within 1e-12 relative/absolute tolerance')


if __name__ == '__main__':
    main()
