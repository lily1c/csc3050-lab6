"""Independent instruction-level oracle. Does not interpret microinstructions."""
from dataclasses import dataclass, field

MASK = 0xFFFF
OPCODES = {'ADD': 1, 'MOVE': 3, 'EXG': 4, 'OR': 5, 'AND': 6}

def double(op, sm=0, sr=0, dm=0, dr=1):
    return OPCODES[op] << 12 | sm << 8 | dm << 4 | sr << 2 | dr

def single(op, mode=0, reg=0):
    return {'INC': 2, 'DEC': 3}[op] << 8 | mode << 4 | reg

@dataclass
class Machine:
    regs: list
    memory: dict = field(default_factory=dict)
    flags: str = '0000'
    events: list = field(default_factory=list)
    halted: bool = False

    def read(self, address):
        if not 0 <= address < 4096:
            raise ValueError(f'Out-of-range memory address {address:04X}')
        return self.memory.get(address, 0)

    def fetch(self):
        value = self.read(self.regs[3])
        self.regs[3] = (self.regs[3] + 1) & MASK
        return value

    def operand(self, mode, reg):
        if mode == 0:
            return ('reg', reg), self.regs[reg]
        if mode == 1:
            address = self.regs[reg]
        elif mode == 2:
            address = self.regs[reg]
            self.regs[reg] = (address + 1) & MASK
        elif mode == 3:
            self.regs[reg] = (self.regs[reg] - 1) & MASK
            address = self.regs[reg]
        elif mode == 4:
            offset = self.fetch()
            address = (self.regs[reg] + offset) & MASK
        elif mode == 5:
            address = self.fetch()
        elif mode == 6:
            return ('imm', None), self.fetch()
        else:
            raise ValueError('Invalid addressing mode')
        return ('mem', address), self.read(address)

    def store(self, target, value):
        kind, index = target
        value &= MASK
        if kind == 'reg':
            self.regs[index] = value
        elif kind == 'mem':
            self.read(index)
            self.memory[index] = value
            self.events.append(['write', value, index])
        else:
            raise ValueError('Immediate destination is invalid')

    def set_flags(self, value, carry=0, overflow=0):
        self.flags = f'{int(carry)}{int(overflow)}{int(value == 0)}{int(bool(value & 0x8000))}'

    def run(self, limit=100):
        for count in range(1, limit + 1):
            word = self.fetch()
            if word == 0:
                self.halted = True
                return self.events
            opcode = word >> 12
            if opcode:
                if opcode not in OPCODES.values():
                    raise ValueError(f'Unsupported opcode {word:04X}')
                src, a = self.operand((word >> 8) & 15, (word >> 2) & 3)
                dst, b = self.operand((word >> 4) & 15, word & 3)
                if opcode == 4:
                    self.store(src, b)
                    self.store(dst, a)
                else:
                    if opcode == 1:
                        total = a + b
                        value = total & MASK
                        self.set_flags(value, total > MASK, bool((~(a ^ b) & (b ^ value)) & 0x8000))
                    else:
                        value = {3: lambda: a, 5: lambda: a | b, 6: lambda: a & b}[opcode]()
                        self.set_flags(value)
                    self.store(dst, value)
            else:
                op = (word >> 8) & 15
                if op not in (2, 3):
                    raise ValueError(f'Unsupported single opcode {word:04X}')
                dst, old = self.operand((word >> 4) & 15, word & 3)
                if dst[0] == 'imm':
                    raise ValueError('Single-operand immediate mode is invalid')
                if op == 2:
                    value = (old + 1) & MASK
                    self.set_flags(value, old == MASK, old == 0x7FFF)
                else:
                    value = (old - 1) & MASK
                    # DEC uses adder carry-out for old + FFFF, not SUB borrow.
                    self.set_flags(value, old != 0, old == 0x8000)
                self.store(dst, value)
            self.events.append(['state', count, *self.regs, self.flags])
        raise ValueError('Reference program did not halt within instruction limit')
