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

## Using simrun directly in the terminal

If you prefer running the simulator yourself, open a terminal in your Ubuntu
VM and clone the repository:

```bash
git clone https://github.com/lily1c/csc3050-lab6.git
cd csc3050-lab6
chmod +x tools/simrun
```

If you already cloned it, go into that folder instead. Run commands from the
repository root so the paths below point to the right files.

To run the provided Lab 5 tests against the current code:

```bash
./tools/simrun -debug lab6-specs.dat tests/lab5/tests.dat
```

Put your own Lab 6 test cases in `tests6.dat` in the repository folder.
It starts empty, so add a test before running it:

```bash
./tools/simrun -debug lab6-specs.dat tests6.dat
```

For example, this small test copies AC into X and then halts:

```text
0005 AC
0000 X
0010 SP
0000 PC
0000 CVZN
3001
0000
```

After MOVE, expect AC = 0005, X = 0005, SP = 0010, PC = 0001, and CVZN = 0000.
The following HALT fetch advances PC to 0002 in the detailed trace.

The simulator writes its output into the folder where you ran the command.
For the first test, read the register summary or the full state trace with:

```bash
cat summary.1
less details.1
```

Press `q` to exit `less`. Multiple tests produce additional files such as
`summary.2` and `details.2`. Another run in the same folder can overwrite these
files, so copy any results you want to keep before running again.

Direct `simrun` execution shows what happened; it does not compare the output
with expected results. Use `python3 tools/check.py` or GitHub Actions for the
automatic comparisons. `./tools/simrun` must be run in Linux x86-64, not directly
in your Mac terminal.

## Working together

Use separate branches and agree on temporary registers and state numbers before
editing shared routines. Review each other's changes in a pull request and check
the test results before combining them.

### Saving and sharing changes to the specs file

Both partners need their own GitHub account. The repository owner needs to add
the other partner under **Settings → Collaborators**, and the partner needs to
accept the invitation before they can push a branch.

From your cloned repository, first check whether you have unsaved Git changes:

```bash
git status
```

If the working tree is clean, start your work from the latest main branch:

```bash
git switch main
git pull --ff-only origin main
git switch -c add-instruction
```

Use a branch name that describes your work, such as `add-instruction` or
`logic-instructions`. Each partner should use a different branch. If `git status`
shows existing changes, commit them on their current work branch first rather
than switching away and risking mixing unrelated work.

Edit the working specs file, not the copy under `baseline/`:

```bash
nano lab6-specs.dat
```

In nano, press **Ctrl+O**, then **Enter** to save, and **Ctrl+X** to exit.
Keep the leading spaces on executable microinstruction lines: the simulator
treats a line starting with a nonblank character as a comment.

Review exactly what you changed:

```bash
git diff -- lab6-specs.dat
git status
```

Then save the change in Git and send your branch to GitHub:

```bash
git add lab6-specs.dat
git commit -m "Implement register ADD"
git push -u origin add-instruction
```

Replace the commit message with a short description of what you actually changed,
and use your own branch name in the push command. `git add` selects the file,
`git commit` records the change locally, and `git push` uploads those commits.
For later changes on that same branch, repeat add and commit, then use `git push`.

If Git asks for your identity, configure your own name and GitHub email:

```bash
git config user.name "Your Name"
git config user.email "YOUR_GITHUB_EMAIL"
```

If HTTPS authentication is not set up, use GitHub CLI in Ubuntu:

```bash
sudo apt install gh
gh auth login
```

Choose GitHub.com, HTTPS, and browser login. Agree to authenticate Git when
prompted. Sign in with your own account; do not share passwords or tokens.

After pushing, open the repository on GitHub and select **Compare & pull request**.
Choose `main` as the base and your work branch as the comparison branch. Describe
the change and ask your partner to review it. GitHub Actions runs automatically.
Check the results before merging; unrelated Lab 6 tests will still fail while
their instructions are unfinished, so review the individual failures as well.

After the pull request is merged and your working tree is clean, get the combined
version before starting another branch:

```bash
git switch main
git pull --ff-only origin main
```

If Git reports a conflict or rejects a push, keep your work and inspect the
message with your partner. Do not use a force push to overwrite their changes.

## Main files

| File | Purpose |
| --- | --- |
| `lab6-specs.dat` | Working Lab 6 microcode |
| `tests6.dat` | Empty file for our own Lab 6 test cases |
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
