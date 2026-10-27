import json
import re
import unittest
from pathlib import Path
from reference import Machine, double, single
from cases import lab6_cases
from check import events, compare, final_state

ROOT = Path(__file__).resolve().parents[1]

class OracleChecks(unittest.TestCase):
    def test_oracle_matches_all_instructor_lab5_results(self):
        text = (ROOT / 'tests/lab5/tests.dat').read_text()
        parts = re.split(r'\*+\s*test\s+([0-9A-S])\s*\n', text, flags=re.I)
        expected = json.loads((ROOT / 'tests/lab5/expected.json').read_text())
        for i in range(1, len(parts), 2):
            label, body = parts[i].upper(), parts[i + 1]
            lines = [line.split() for line in body.splitlines() if line.strip()]
            regs = [int(line[0], 16) for line in lines[:4]]
            flags = lines[4][0]
            memory = {i: int(line[0], 16) for i, line in enumerate(lines[5:])}
            with self.subTest(case=label):
                self.assertEqual(Machine(regs, memory, flags).run(), expected[label])

    def test_arithmetic_boundaries(self):
        for op, value, expected, flags in [
            ('INC', 0xFFFF, 0, '1010'), ('INC', 0x7FFF, 0x8000, '0101'),
            ('DEC', 0, 0xFFFF, '0001'), ('DEC', 0x8000, 0x7FFF, '1100')]:
            m = Machine([value, 0, 0, 0], {0: single(op), 1: 0})
            m.run()
            self.assertEqual((m.regs[0], m.flags), (expected, flags))
        for a, b, value, flags in [(0xFFFF, 1, 0, '1010'), (0x7FFF, 1, 0x8000, '0101')]:
            m = Machine([a, b, 0, 0], {0: double('ADD'), 1: 0})
            m.run()
            self.assertEqual((m.regs[1], m.flags), (value, flags))

    def test_exchange_preserves_flags(self):
        for flag in range(16):
            flags = f'{flag:04b}'
            m = Machine([0, 0x8000, 0, 0], {0: double('EXG'), 1: 0}, flags)
            m.run()
            self.assertEqual((m.regs[:2], m.flags), ([0x8000, 0], flags))

    def test_case_coverage_and_unique_names(self):
        cases = lab6_cases()
        names = [c['name'] for c in cases]
        self.assertEqual(len(names), len(set(names)))
        for op in ('MOVE', 'ADD', 'AND', 'OR', 'EXG'):
            for mode in range(1, 6 if op == 'EXG' else 7):
                self.assertIn(f'{op}-source-mode-{mode}', names)
            for mode in range(1, 6):
                self.assertIn(f'{op}-destination-mode-{mode}', names)
        for op in ('INC', 'DEC'):
            for mode in range(6):
                self.assertIn(f'{op}-mode-{mode}-value-0000', names)
        self.assertIn('HALT-preserves-registers-and-flags', names)

class CheckerChecks(unittest.TestCase):
    def test_comparison_rejects_missing_extra_and_wrong_results(self):
        expected = [['state', 1, 0, 0, 0, 1, '0010']]
        self.assertIsNone(compare(expected, expected))
        self.assertIsNotNone(compare(expected, []))
        self.assertIsNotNone(compare([], expected))
        self.assertIsNotNone(compare(expected, [['state', 1, 0, 0, 0, 1, '0000']]))

    def test_parser_tracks_write_order_and_flags(self):
        text = 'memory write:: F000->M( 5)\nAt end of instruction 1\nac x sp pc cvzn\n5 F000 5 1 0001\n'
        self.assertEqual(events(text), [['write', 0xF000, 5], ['state', 1, 5, 0xF000, 5, 1, '0001']])

    def test_missing_halt_trace_is_rejected(self):
        with self.assertRaises(ValueError):
            final_state('Processor halted.\n')

if __name__ == '__main__':
    unittest.main()
