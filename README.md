# CSC3050 Lab 6

This lab builds on our Lab 5 microcode. We're adding ADD, AND, OR, EXG, INC,
and DEC while keeping MOVE and HALT working. The instructions need to support
the applicable addressing modes and update the condition codes correctly.

## What we're working on

| Instruction | Operation |
| --- | --- |
| MOVE | Copy the source value into the destination |
| ADD | Add the source and destination and store the result in the destination |
| AND | Store the bitwise AND of the values in the destination |
| OR | Store the bitwise OR of the values in the destination |
| EXG | Exchange the source and destination values |
| INC | Increase the destination by one |
| DEC | Decrease the destination by one |
| HALT | Stop execution |

ADD, INC, and DEC update all four flags. MOVE, AND, and OR update N and Z
and clear C and V. EXG and HALT leave the flags unchanged.
The output lists the flags in **C V Z N** order.

## Addressing

The registers are AC, X, SP, and PC. Register and memory values are 16-bit
hexadecimal numbers.

| Mode | Name | Example |
| --- | --- | --- |
| 0 | Register | `X` |
| 1 | Register indirect | `(X)` |
| 2 | Autoincrement | `(X)+` |
| 3 | Autodecrement | `-(X)` |
| 4 | Indexed | `n(X)` |
| 5 | Absolute | `n` |
| 6 | Immediate | `#n` |

Immediate values can be sources, but cannot be destinations. INC and DEC use
modes 0–5. EXG needs both operands to be writable. For double-operand instructions,
one operand must use register addressing, or the source must be immediate,
following the machine's restriction from Lab 5.

The lab recommends sharing the operand-handling code. After fetching an
instruction, we get the operand values and save any effective addresses needed
later. Then we perform the operation and write the result to the correct location.

In Lab 5, T2 holds the source value and MAR is reused for memory accesses.
For Lab 6, we also need to keep the destination value. EXG needs both locations
available because it writes to both operands. PC advances as each instruction
word is read, and source addressing happens before destination addressing.

## Current code

`baseline/lab5-specs.dat` is the original Lab 5 code. It passed all 28 instructor
tests before we started this repository.

`lab6-specs.dat` is the file we're editing. It currently contains the same Lab 5
code, so MOVE and HALT work. The six new instructions still need to be added.

## Where the tests come from

- **Lab 5:** the 28 instructor tests and reference results provided for Lab 5.
  These check that changes haven't broken MOVE or HALT.
- **Lab 6:** 303 checks added for this repository. These are not the professor's
  test files. This set also includes the INC example from the Lab 6 handout.

The extra checks cover addressing modes, register pairs, memory writes, flags,
and values such as `0000`, `FFFF`, `7FFF`, and `8000`. Expected Lab 6 results
come from the separate instruction model in `tools/reference.py`, rather than
from running our microcode and assuming its output is correct.

With the starting code, **28/28 Lab 5 tests pass** and **49/303 Lab 6 checks
pass**. The remaining checks fail because the new instructions aren't implemented
yet. These are starting results; the Actions page shows the latest run.

We still need to understand and explain our own test cases in the lab report.

## Running the checks

GitHub Actions runs the tests whenever we push changes or open a pull request.
Open **Actions → Microcode checks** to see the results.

If a case fails, its name and first difference appear in the log. Download the
results to see `results.json`, `simulator.log`, and the detailed traces.

For example, `ADD-register-7FFF-0001` checks adding `7FFF` and `0001` using
register operands. `expected 1 events, got 0` means the checker expected one
completed instruction result but didn't find one in the summary. With the
starter code, ADD reaches HALT without being executed.

To run everything in the Ubuntu VM:

```bash
python3 tools/check.py
```

To run one set:

```bash
python3 tools/check.py --suite lab5
python3 tools/check.py --suite lab6
```

The simulator is a Linux x86-64 program. It doesn't run directly in macOS
Terminal; GitHub Actions runs it on Ubuntu. Docker is another option:

```bash
docker build --platform linux/amd64 -t csc3050-lab6 .
docker run --rm --platform linux/amd64 csc3050-lab6
```

## Working together

Use separate branches and agree on temporary registers and state numbers before
editing shared routines. Review each other's changes in a pull request and check
the test results before combining them.

## Main files

| File | Purpose |
| --- | --- |
| `lab6-specs.dat` | Working Lab 6 microcode |
| `baseline/lab5-specs.dat` | Original working Lab 5 code |
| `tests/lab5/` | Provided Lab 5 tests and expected results |
| `tools/cases.py` | Additional Lab 6 test cases |
| `tools/reference.py` | Expected instruction behavior and flags |
| `tools/check.py` | Runs the simulator and compares results |
| `tools/test_checks.py` | Checks the test runner and reference model |
| `tools/simrun` | Processor simulator |
| `.github/workflows/test.yml` | Automatic tests on GitHub |

The lab requirements come from **CSC-3050 Lab 6 Microinstruction Problem 3**.
Instruction encodings and flag behavior follow the **Computer Simulator Specification**.
