# CSC3050 Lab 6 Microinstruction Problem 3

This lab extends the processor microcode developed in Lab 5. Lab 5 implemented
MOVE across the addressing modes and supported HALT. Lab 6 adds four
double-operand instructions—ADD, AND, OR, and EXG—and two single-operand
instructions—INC and DEC. The finished microcode must run all eight instructions
with the applicable addressing modes and correct condition codes.

This repository contains the verified Lab 5 starting point, the working
`lab6-specs.dat`, and automated simulator checks for developing Lab 6 together.

## Assignment and deadlines

The requirements below summarize the course handout
**CSC-3050_Lab6_Microinstruction_Problem_3.pdf**, pages 1–3. Instruction encodings,
register interfaces, and flag semantics follow **Computer Simulator Specification**.
The handouts themselves are not stored in this repository.

| Milestone | Due as listed in the lab handout |
| --- | --- |
| Checkpoints 1 and 2 | November 3 at 1:40 PM |
| Code and report submission | November 6 at 11:59 PM |

You may work alone or in a group of two students. The handout requires each
group to do its own work and be able to explain its implementation and results.

## Instructions to implement

`src` and `dst` below mean the operand **values** after addressing-mode processing.
For memory operands, their effective addresses must also be retained for writeback.

| Instruction | Type | Operation | Condition codes |
| --- | --- | --- | --- |
| MOVE | Double operand | Copy src to dst | Update N/Z; clear C/V |
| ADD | Double operand | Store src + dst in dst | Update C/V/Z/N |
| AND | Double operand | Store src AND dst in dst | Update N/Z; clear C/V |
| OR | Double operand | Store src OR dst in dst | Update N/Z; clear C/V |
| EXG | Double operand | Exchange the source and destination values | Preserve C/V/Z/N |
| INC | Single operand | Add one to dst | Update C/V/Z/N |
| DEC | Single operand | Subtract one from dst | Update C/V/Z/N |
| HALT | Special | Stop execution | Preserve C/V/Z/N |

MOVE and HALT must continue to work after the new instructions are added.
The general fetch/decode structure mentioned in the handout is not a requirement
to implement every branch or special instruction in the machine specification.

## Addressing modes

All words and registers are 16 bits. The programmer-visible registers are AC,
X, SP, and PC. Memory and register values are written in hexadecimal; flags are
written in binary **C V Z N** order.

| Mode | Name | Example | How the operand is obtained |
| --- | --- | --- | --- |
| 0 | Register | `X` | Value already in X; no operand-memory access |
| 1 | Register indirect | `(X)` | Memory word at the address in X |
| 2 | Autoincrement | `(X)+` | Use the old address in X, then increment X by one |
| 3 | Autodecrement | `-(X)` | Decrement X by one, then use the new address |
| 4 | Indexed | `n(X)` | Memory word at X plus the extension-word offset n |
| 5 | Absolute | `n` | Memory word at the extension-word address n |
| 6 | Immediate | `#n` | The extension word n is the operand value itself |

Support every mode that is valid for the instruction. Immediate addressing
cannot be a destination, including the sole operand of INC or DEC. EXG needs
two writable operands, so its source cannot be immediate either. Follow the
machine's double-operand restriction carried forward from Lab 5: one operand
uses register addressing, or the source is immediate.

Indexed, absolute, and immediate modes consume an additional instruction word
for each operand using that mode. Update PC as soon as each instruction word
is read. Finish source addressing before destination addressing.

## Implementation approach from the lab handout

The handout recommends shared operand processing instead of repeating each
addressing routine for every opcode:

1. **Fetch and classify.** Fetch the instruction and determine whether it is
   special, single operand, or double operand. Distinguish INC and DEC from
   HALT even though their top opcode nibble is also zero.
2. **Prepare a single operand.** For INC or DEC, save the destination value in
   a temporary register. For a memory destination, also save its effective address.
3. **Prepare two operands.** For a double-operand instruction, save source and
   destination values and the memory addresses that may be needed for writeback.
4. **Execute the selected operation.** Use the saved values to perform MOVE,
   ADD, AND, OR, EXG, INC, or DEC and handle its condition-code rules.
5. **Write back.** Use the register interface for a register destination or the
   saved effective address for a memory destination. EXG also writes the old
   destination value back to the source location.

The Lab 5 code saves the source value in T2 and reuses MAR for successive memory
accesses. Lab 6 needs additional retained values and addresses. In particular,
do not lose an effective address when MAR is reused for an extension word or
another operand. Save the actual accessed address for autoincrement and
autodecrement; recomputing it from an already-updated pointer can be wrong.

The handout's OR hint uses the open-collector bus: with the values in T2 and T4,
`ot2 ot4 ib oadder` puts their bitwise OR in Q when the other adder controls are
inactive. AND can be constructed using De Morgan's law:

```text
A AND B = NOT ((NOT A) OR (NOT B))
```

Preserve operands and addresses while using scratch registers for these steps.
Arithmetic or pointer calculations used to locate an operand must not overwrite
the instruction's final condition codes.

## Required test evidence and checkpoints

| Requirement | What to demonstrate | Points |
| --- | --- | --- |
| Checkpoint 1 | Enough test cases to exercise all eight instructions | 1 |
| Checkpoint 2 | Match the provided INC example and demonstrate expected results for your own cases | 1 |
| Own test cases in the report | Include inputs, actual results, and appropriate explanations | 4 |
| Microcode discussion in the report | Explain how the implementation works | 4 |
| Submitted microcode | Pass the instructor's tests of `lab6-specs.dat` | 10 |

Initialize every register and memory location needed by a test. Design expected
results before comparing them with the simulator: destination changes, pointer
updates, PC, memory writes, and all four flags matter. The provided INC example
is checkpoint evidence; it does not replace the requirement to explain your
**own** test cases in the report.

The handout's example starts AC = 0008, X = 0008, SP = 000B, PC = 0000, and
CVZN = 0000. It executes these instructions and then HALT:

```text
INC (X)
INC (AC)+
INC -(SP)
INC 1(AC)
INC $000A
HALT
```

Its data words are FFFF at address 0008, 0003 at 0009, 8000 at 000A, and 0005
at 000B. The automated suite includes this program as
`Lab6-provided-INC-example`, in addition to the generated Lab 6 cases.

## Submission checklist

Upload these two files on Moodle:

1. **`lab6-specs.dat`** with your name, or both partners' names, in its opening comments.
2. **`csc3050_lab6_report_FirstName_LastName.docx`** using the course report template.

The report must discuss the microcode implementation and your own test cases
and results for all eight instructions. For a two-person group, put both names
on the cover and complete **Contributions to the Group**. Only one member needs
to upload the group's required files.

Do not submit `details.*`, `summary.*`, or other test outputs as separate files.
Keep a copy of the exact code submitted and double-check the uploaded files;
the handout says submissions cannot be replaced after the deadline.

## Automated testing in this repository

GitHub Actions runs the simulator and compares outputs on every push and pull
request. This supports the assignment; CI is not an additional course deliverable.
No manual simulator-output comparison is required to see which automated cases pass.

### Current implementation status

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

### Automatic testing on GitHub

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

### What is checked

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

### One command in Ubuntu

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

### Optional Docker environment on a Mac

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

## Flag details for testing

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

