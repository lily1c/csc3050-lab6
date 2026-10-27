# CSC3050 Lab 6 microinstruction testing

Shared working environment for Lab 6, starting from the verified Lab 5 MOVE
and HALT implementation. Automated checks run on every push and pull request.
No manual simulator-output comparison is required.

## Current implementation status

`lab6-specs.dat` initially contains the exact, tested Lab 5 code. It implements
MOVE and HALT only. ADD, AND, OR, EXG, INC, and DEC still need implementation.
The Lab 6 CI job is deliberately a **required-to-pass behavioral test**, not an
expected-failure or skipped test. It will be red until the implementation meets
the new requirements. A green Lab 5 job alone does not mean Lab 6 is complete.

Initial verification with the unchanged starter: **28/28 Lab 5 cases pass**;
**49/303 Lab 6 cases pass**, with the remaining cases failing because the six new
instructions are not yet implemented. All 7 checker/oracle tests pass. The runner
automatically batches large suites to respect the simulator's 61-case limit.

`baseline/lab5-specs.dat` preserves the original working implementation.
Edit `lab6-specs.dat` for Lab 6; do not change the baseline to hide regressions.

## Automatic testing on GitHub

1. Create your own branch and edit `lab6-specs.dat`.
2. Commit and push the changes, then open a pull request.
3. Open **Actions → Microcode checks**, or the pull request's checks.
4. Review the three checks: the checker/oracle tests, Lab 5 regression, and Lab 6.
5. For a failure, download that job's `lab5-results` or `lab6-results` artifact.
   `results.json` names the failing case and first difference; `simulator.log`
   includes compilation and execution messages. `details.*` shows the state trace.

Both simulator jobs must pass before treating changes as ready to combine.
The workflow does not itself configure branch protection or prevent merging.
There is no deployment step: this project needs CI, not CD.

## What is checked

- Compilation and input-file errors, including simulator errors that still
  return a zero process exit code.
- Successful HALT, missing outputs, timeouts, and test-count mismatches.
- AC, X, SP, PC, and all CVZN bits after each instruction.
- Every reported memory write, including value, address, order, and extra writes.
- For generated Lab 6 cases, register values and flags at HALT as well.
- Register pairs, PC source/destination behavior, and self-copies.
- Applicable source modes 0–6 and destination modes 0–5. EXG excludes immediate
  sources because they cannot be written back; single-operand immediate mode is
  also excluded. Cases follow the one-register-or-immediate-source restriction.
- Negative index offsets, extension-word consumption, and automatic pointer updates.
- Zero, negative, carry, signed-overflow, and wraparound arithmetic results.
- All 16 incoming CVZN combinations for EXG, which must preserve the flags.
- The Lab 6 provided INC example and a mixed-instruction program.

The 28 Lab 5 cases and expected results come from the provided instructor
regression suite, independently verified against the simulator. They contain
66 instruction result records and 24 memory writes. `tests/lab5/expected.json`
stores those reference records, not results produced by the current microcode.

New Lab 6 expectations are calculated by `tools/reference.py`, an independent
instruction-level model. It does not execute or inspect microcode. Its tests
verify all 28 Lab 5 reference cases and explicit arithmetic flag boundaries.
This gives broad regression coverage, not a proof that every possible program
is correct or a substitute for the instructor's hidden tests.

## One command in Ubuntu

Requires x86-64 Linux and Python 3, as supplied by the class Ubuntu VM.
From the repository root:

```bash
python3 tools/check.py
```

This runs both suites against `lab6-specs.dat` and exits with status 1 if any
check fails. Outputs are written under `outputs/` in fresh run directories so
old simulator results cannot accidentally pass a new run.

To run just one suite:

```bash
python3 tools/check.py --suite lab5
python3 tools/check.py --suite lab6
```

To verify the untouched baseline:

```bash
python3 tools/check.py --suite lab5 --specs baseline/lab5-specs.dat
```

To test the checker and reference model without running the simulator:

```bash
python3 -m unittest discover -s tools -p 'test_*.py' -v
```

## Optional Docker environment on a Mac

The included `simrun` is the supplied Linux x86-64 executable. It does not run
directly in macOS Terminal. GitHub Actions handles the Linux environment for you.
If you already have Docker installed, you can also run locally:

```bash
docker build --platform linux/amd64 -t csc3050-lab6 .
docker run --rm --platform linux/amd64 csc3050-lab6
```

Rebuild after edits. The default Docker command runs all checks. Use your Ubuntu
VM or GitHub Actions if you do not want to install Docker.

## Working as a pair

Agree first on the temporary-register roles, source/destination effective-address
storage, state-number ranges, and shared writeback interfaces. The Lab 5 code
reuses MAR for source and destination accesses and keeps the source value in T2;
Lab 6 operations need additional retained operands, and EXG needs both writeback
locations. Establish that interface before implementing separate instructions.

Each person uses their own branch and pushes changes for review. Run the checks
on the combined code before submission. Put both actual contributors' names in
the microcode comments and report cover, and describe their actual work in the
report's Contributions to the Group section.

## Files

| Path | Purpose |
| --- | --- |
| `lab6-specs.dat` | Working microcode to implement and eventually submit |
| `baseline/lab5-specs.dat` | Verified MOVE/HALT starting point |
| `tools/simrun` | Supplied Linux x86-64 processor simulator |
| `tools/check.py` | Simulator runner and result comparator |
| `tools/reference.py` | Independent instruction semantics and CVZN oracle |
| `tools/cases.py` | Lab 6 behavioral test generation |
| `tools/test_checks.py` | Tests for the checker, oracle, and coverage |
| `tests/lab5/` | Instructor regression input and expected events |
| `.github/workflows/test.yml` | Automatic GitHub Actions checks |

The code initially retains Assol Abasova's name from the verified Lab 5 file.
The repository excludes VM images, login keys, reports, and student IDs.

## Flag conventions

All values are 16-bit; all register and memory values are hexadecimal.
Condition codes are written in binary **C V Z N** order.

- MOVE, AND, OR: update N/Z and clear C/V.
- ADD: update all four flags from the sum.
- EXG: preserve all four flags.
- INC: add one and update all four flags.
- DEC: calculate old + FFFF and use the adder carry-out; do not use SUB's borrow
  convention. For example, DEC 0000 → FFFF gives CVZN 0001, while DEC 8000 →
  7FFF gives CVZN 1100.
- HALT: preserve the flags. The fetch cycle has already advanced PC.

## Submission

The Lab 6 submission is `lab6-specs.dat` plus the required Word report.
Include your own test cases, actual results, and explanations in the report.
Do not submit generated `summary.*`, `details.*`, or other test outputs separately.
