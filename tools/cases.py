"""Lab 6 behavioral cases, independent of the submitted microcode."""
from reference import Machine, double, single

def make_case(name, program, regs=None, data=None, flags='1111'):
    registers = list(regs or [0x0040, 0x00F0, 0x0080, 0])
    memory = dict(data or {})
    memory.update(enumerate(program))
    model = Machine(registers.copy(), memory.copy(), flags)
    expected = model.run()
    return {'name': name, 'program': program, 'regs': registers,
            'memory': dict(data or {}), 'flags': flags, 'expected': expected,
            'final': [*model.regs, model.flags]}

def lab6_cases():
    cases = []
    def add(*args, **kwargs):
        cases.append(make_case(*args, **kwargs))
    values = [(0, 0), (1, 2), (0xFFFF, 1), (0x7FFF, 1),
              (0x8000, 0x8000), (0xF0F0, 0x0FF0), (0xFFFF, 0xFFFF)]
    for op in ('MOVE', 'ADD', 'AND', 'OR', 'EXG'):
        for a, b in values:
            add(f'{op}-register-{a:04X}-{b:04X}', [double(op), 0], [a, b, 0x80, 0])
        # Every applicable source mode, with a register destination.
        for mode in range(1, 6 if op == 'EXG' else 7):
            base = 0x41 if mode == 3 else 0x40
            ext = [1] if mode == 4 else [0x40] if mode == 5 else [0x8000] if mode == 6 else []
            add(f'{op}-source-mode-{mode}', [double(op, mode, 0, 0, 1), *ext, 0],
                [base, 0x00F0, 0x80, 0], {0x40: 0x8000, 0x41: 0x8000})
        # Every memory destination mode with a register source.
        for mode in range(1, 6):
            base = 0x41 if mode == 3 else 0x40
            ext = [1] if mode == 4 else [0x40] if mode == 5 else []
            add(f'{op}-destination-mode-{mode}', [double(op, 0, 1, mode, 0), *ext, 0],
                [base, 0xF000, 0x80, 0], {0x40: 0x000F, 0x41: 0x000F})
        # Negative index offsets must wrap in 16-bit address arithmetic.
        add(f'{op}-negative-source-offset', [double(op, 4, 0, 0, 1), 0xFFFF, 0],
            [0x41, 1, 0x80, 0], {0x40: 0x8000})
        add(f'{op}-negative-destination-offset', [double(op, 0, 1, 4, 0), 0xFFFF, 0],
            [0x41, 0x8000, 0x80, 0], {0x40: 1})
    for op in ('MOVE', 'ADD', 'AND', 'OR'):
        for mode in range(1, 6):
            base = 0x41 if mode == 3 else 0x40
            ext = [1] if mode == 4 else [0x40] if mode == 5 else []
            add(f'{op}-zero-memory-result-mode-{mode}',
                [double(op, 0, 1, mode, 0), *ext, 0],
                [base, 0, 0x80, 0], {0x40: 0, 0x41: 0})
    # Immediate sources combined with all six destination modes.
    for op in ('MOVE', 'ADD', 'AND', 'OR'):
        for mode in range(6):
            base = 0x41 if mode == 3 else 0x40
            ext = [1] if mode == 4 else [0x40] if mode == 5 else []
            add(f'{op}-immediate-to-mode-{mode}', [double(op, 6, 0, mode, 0), 0x7FFF, *ext, 0],
                [base, 0, 0x80, 0], {0x40: 1, 0x41: 1})
    for op in ('INC', 'DEC'):
        for mode in range(6):
            for value in (0, 1, 0x7FFF, 0x8000, 0xFFFF):
                base = 0x41 if mode == 3 else 0x40
                regs = [value if mode == 0 else base, 0x1234, 0x80, 0]
                ext = [1] if mode == 4 else [0x40] if mode == 5 else []
                add(f'{op}-mode-{mode}-value-{value:04X}', [single(op, mode), *ext, 0],
                    regs, {0x40: value, 0x41: value})
    # EXG must preserve all 16 combinations of incoming condition codes.
    for flags in range(16):
        add(f'EXG-preserve-flags-{flags:04b}', [double('EXG'), 0],
            [0, 0x8000, 0x80, 0], flags=f'{flags:04b}')
    # All register pairs, including PC and self-copies. Zero-filled memory
    # provides HALT at any jump target used by these small register values.
    for op in ('MOVE', 'ADD', 'AND', 'OR', 'EXG'):
        for sr in range(4):
            for dr in range(4):
                regs = [1, 1, 1, 0] if op == 'AND' else [4, 5, 6, 0]
                add(f'{op}-register-pair-{sr}-{dr}', [double(op, 0, sr, 0, dr), 0], regs)
    add('HALT-preserves-registers-and-flags', [0], flags='1011')
    add('PC-source-before-destination-extension', [double('MOVE', 0, 3, 5, 0), 0x40, 0])
    add('Lab6-provided-INC-example',
        [0x0211, 0x0220, 0x0232, 0x0240, 1, 0x0250, 0x000A, 0],
        [8, 8, 0xB, 0], {8: 0xFFFF, 9: 3, 0xA: 0x8000, 0xB: 5}, '0000')
    # Cross-instruction sequencing catches shared-temporary/dispatch errors.
    add('mixed-arithmetic-logical-exchange',
        [double('MOVE', 6, 0, 0, 0), 0x7FFF,
         single('INC'), single('DEC'), double('ADD', 0, 0, 0, 1),
         double('AND', 6, 0, 0, 1), 0x00FF,
         double('OR', 6, 0, 0, 1), 0x8000,
         double('EXG'), 0], [0x40, 1, 0x80, 0])
    return cases

def serialize(cases):
    lines = []
    for index, case in enumerate(cases, 1):
        lines.append(f'******** test {index}: {case["name"]}')
        lines.extend(f'{value:04X} {name}' for name, value in zip(('AC', 'X', 'SP', 'PC'), case['regs']))
        lines.append(case['flags'] + ' CVZN')
        end = max(len(case['program']) - 1, max(case['memory'], default=0))
        memory = dict(case['memory'])
        memory.update(enumerate(case['program']))
        lines.extend(f'{memory.get(address, 0):04X}' for address in range(end + 1))
    return '\n'.join(lines) + '\n'
