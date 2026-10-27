#!/usr/bin/env python3
"""Compile, execute, and compare simulator output; nonzero exit on failure."""
import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from cases import lab6_cases, serialize

ROOT = Path(__file__).resolve().parents[1]

def events(text):
    pattern = (r'At\s+end\s+of\s+instruction\s+(\d+)\s+ac\s+x\s+sp\s+pc\s+cvzn\s+'
               r'([0-9A-F]+)\s+([0-9A-F]+)\s+([0-9A-F]+)\s+([0-9A-F]+)\s+([01]{4})'
               r'|memory\s+write::\s*([0-9A-F]+)\s*->M\(\s*([0-9A-F]+)\s*\)')
    result = []
    for m in re.finditer(pattern, text, re.I):
        if m[1]:
            result.append(['state', int(m[1]), *[int(m[k], 16) for k in range(2, 6)], m[6]])
        else:
            result.append(['write', int(m[7], 16), int(m[8], 16)])
    return result

def final_state(text):
    rows = re.findall(r'^10\s+([0-9A-F]+)\s+([0-9A-F]+)\s+([0-9A-F]+)\s+([0-9A-F]+)'
                      r'\s+(?:[0-9A-F]+\s+){9}([01])\s+([01])\s+([01])\s+([01])\s*$', text, re.M | re.I)
    if not rows:
        raise ValueError('No HALT state found in detailed trace')
    pc, ac, x, sp, *flags = rows[-1]
    return [*[int(v, 16) for v in (ac, x, sp, pc)], ''.join(flags)]

def compare(expected, actual):
    for i, (a, b) in enumerate(zip(expected, actual)):
        if a != b:
            return f'event {i + 1}: expected {a}, got {b}'
    if len(expected) != len(actual):
        return f'expected {len(expected)} events, got {len(actual)}'
    return None

def run_suite(name, specs, simulator, output):
    target = output / name
    target.mkdir(parents=True, exist_ok=True)
    if name == 'lab5':
        expected = json.loads((ROOT / 'tests/lab5/expected.json').read_text())
        cases = [{'name': 'Lab5-reference-' + key, 'expected': value} for key, value in expected.items()]
        test_path = ROOT / 'tests/lab5/tests.dat'
    else:
        cases = lab6_cases()
    results = []
    # The supplied simulator supports at most 61 tests in one invocation.
    # Batch below that limit, then aggregate all cases without silent truncation.
    batches = [cases[i:i + 50] for i in range(0, len(cases), 50)]
    for index, batch in enumerate(batches, 1):
        directory = target / f'batch-{index:02d}'
        directory.mkdir(exist_ok=True)
        if name == 'lab6':
            test_path = directory / 'tests.dat'
            test_path.write_text(serialize(batch))
        results.extend(run_batch(name, batch, specs, simulator, directory, test_path))
    (target / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    failures = [r for r in results if not r['passed']]
    print(f'{name}: {len(results) - len(failures)}/{len(results)} passed')
    for row in failures[:12]:
        print(f'  FAIL {row["name"]}: {row["error"]}')
    if len(failures) > 12:
        print(f'  ... {len(failures) - 12} more; see the saved {name}/results.json')
    import os
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
            summary.write(f'## {name}: {len(results) - len(failures)}/{len(results)} passed\n\n')
            summary.write('All tests must pass before treating this suite as complete.\n\n')
            for row in failures[:12]:
                summary.write(f'- **{row["name"]}**: {row["error"]}\n')
    return not failures

def run_batch(name, cases, specs, simulator, target, test_path):
    try:
        proc = subprocess.run([str(simulator), '-debug', str(specs), str(test_path)],
                              cwd=target, text=True, capture_output=True, timeout=90)
    except subprocess.TimeoutExpired:
        raise ValueError(f'{name}: simulator exceeded 90 seconds')
    log = proc.stdout + proc.stderr
    (target / 'simulator.log').write_text(log)
    if proc.returncode or re.search(r'\b[1-9]\d* error\(s\)|cannot|failed to|fatal|test sets ignored', log, re.I):
        raise ValueError(f'{name}: simulator failed; see {target / "simulator.log"}\n{log[:2000]}')
    runs = re.findall(r'Test ([^:]+): (.*?) -> (summary\.\S+), (details\.\S+)', log)
    if len(runs) != len(cases):
        raise ValueError(f'{name}: expected {len(cases)} test results, got {len(runs)}')
    results = []
    for case, (label, status, summary, details) in zip(cases, runs):
        error = None
        if 'OK (halted)' not in status:
            error = 'Test did not halt successfully: ' + status
        summary_path, details_path = target / summary, target / details
        if not summary_path.exists() or not details_path.exists():
            error = 'Missing simulator output file'
        else:
            actual = events(summary_path.read_text())
            error = error or compare(case['expected'], actual)
            if name == 'lab6' and error is None:
                try:
                    actual_final = final_state(details_path.read_text())
                    if actual_final != case['final']:
                        error = f'final HALT state: expected {case["final"]}, got {actual_final}'
                except ValueError as exc:
                    error = str(exc)
        results.append({'name': case['name'], 'passed': error is None, 'error': error})
    (target / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suite', choices=['lab5', 'lab6', 'all'], default='all')
    parser.add_argument('--specs', type=Path, default=ROOT / 'lab6-specs.dat')
    parser.add_argument('--simulator', type=Path, default=ROOT / 'tools/simrun')
    parser.add_argument('--output', type=Path, default=ROOT / 'outputs')
    args = parser.parse_args()
    if platform.system() != 'Linux' or platform.machine() not in ('x86_64', 'amd64'):
        parser.error('Run in Ubuntu x86-64, the supplied Docker environment, or GitHub Actions.')
    specs, simulator = args.specs.resolve(), args.simulator.resolve()
    if not specs.is_file() or not simulator.is_file():
        parser.error('The specs file and simulator must exist.')
    print('Specs SHA256:', hashlib.sha256(specs.read_bytes()).hexdigest())
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    # Each run gets a fresh directory, preventing stale outputs from passing tests.
    with tempfile.TemporaryDirectory(prefix='.run-', dir=output) as directory:
        fresh = Path(directory)
        suites = ['lab5', 'lab6'] if args.suite == 'all' else [args.suite]
        passed = True
        try:
            for name in suites:
                passed = run_suite(name, specs, simulator, fresh) and passed
        except (ValueError, OSError) as exc:
            print(str(exc), file=sys.stderr)
            passed = False
        import shutil
        for item in fresh.iterdir():
            dest = output / item.name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
    return 0 if passed else 1

if __name__ == '__main__':
    sys.exit(main())
