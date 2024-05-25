from enum import Enum, auto
import sys
from microcode import microcode
import isa

def main(program_file: str, input_file: str) -> None:
    with open(program_file, "rb") as f:
        program = isa.read_program(f)

    with open(input_file, encoding="ascii") as f:
        text = f.read()
        input_buffer = [ord(c) for c in text]

    output = simulation(program, input_buffer)
    print(output, end="")


def simulation(program: isa.Program, input_buffer: list[int]) -> str:
    data_path = DataPath(program, input_buffer)
    control_unit = ControlUnit(microcode, data_path)
    try:
        while True:
            control_unit.execute_microinstruction()
    except StopIteration:
        pass

    return "".join([chr(c) for c in data_path.output_buffer])


class DataPath:
    memory: list[isa.MemoryWord]
    registers: list[isa.MemoryWord]
    carry: bool
    zero: bool
    input_buffer: list[int]
    output_buffer: list[int]

    def __init__(self, program: isa.Program, input_buffer: list[int]) -> None:
        self.memory = [0] * isa.ORIGIN + program.instructions + [0] * (isa.MEMORY_SIZE - len(program.instructions) - isa.ORIGIN)
        self.registers = [0] * isa.REG_N
        self.registers[isa.PC] = program.start
        self.carry = False
        self.zero = False
        self.input_buffer = input_buffer
        self.output_buffer = []

    def signal_write_register(self, x_sel: int, y_sel: int, alu_ctrl: isa.ALUControl, rwr_sel: int) -> isa.MemoryWord:
        x = self._get_reg(x_sel)
        y = self._get_reg(y_sel)
        (r, c) = alu_ctrl.call(x, y)
        self.zero = r == 0
        self.carry = c
        self._set_reg(rwr_sel, r)
        return r

    def signal_mem_wr(self) -> None:
        address = self.registers[isa.AR]
        data = self.registers[isa.DR]
        assert isinstance(address, int) and isinstance(data, int), "Expected data, but got instruction"
        if address == isa.OUTPUT_DEVICE_ADDR:
            self.output_buffer.append(data & 0xFF)
        self.memory[address] = data

    def signal_mem_rd(self) -> None:
        address = self.registers[isa.AR]
        assert isinstance(address, int), "Expected data, but got instruction"
        read = self.memory[address]
        if address == isa.INPUT_DEVICE_ADDR:
            popped = 0 if len(self.input_buffer) == 0 else self.input_buffer.pop(0)
            read = popped & 0xFF

        self.registers[isa.DR] = read

    def _get_reg(self, reg: int) -> isa.MemoryWord:
        if reg == isa.IND_AR:
            ar = self.registers[isa.AR]
            assert isinstance(ar, int), "Expected data, but got instruction"
            reg = ar & isa.IND_AR_MASK
        assert _valid_register(reg), f"Unexpected register '{reg}'"
        if reg == 0:
            return 0
        return self.registers[reg]

    def _set_reg(self, reg: int, val: isa.MemoryWord) -> None:
        if reg == isa.IND_AR:
            ar = self.registers[isa.AR]
            assert isinstance(ar, int), "Expected data, but got instruction"
            reg = ar & isa.IND_AR_MASK
        assert _valid_register(reg), f"Unexpected register '{reg}'"
        if reg != 0:
            self.registers[reg] = val
    

class ControlUnit:
    microcode: list[isa.MInstruction]
    mpc: int
    data_path: DataPath
    _tick: int

    def __init__(self, microcode: list[isa.MInstruction], data_path: DataPath) -> None:
        self.microcode = microcode
        self.mpc = 0
        self.data_path = data_path
        self._tick = 0

    def tick(self) -> None:
        self._tick += 1

    def signal_latch_mpc(self, mpc_sel: int) -> None:
        self.mpc = mpc_sel

    def execute_microinstruction(self) -> None:
        minstr = self.microcode[self.mpc]
        next_mpc = self.mpc + 1
        if isinstance(minstr, isa.MIJump):
            next_mpc = self._execute_jump_mi(minstr)
        else:
            self._execute_operation_mi(minstr)
        self.tick()
        self.signal_latch_mpc(next_mpc)

    def _execute_jump_mi(self, minstr: isa.MIJump) -> int:
        alu_result = self.data_path.signal_write_register(minstr.x_sel, minstr.y_sel, minstr.alu_ctrl, rwr_sel=0)
        if minstr.to != -1:
            return minstr.to
        if minstr.if_zero != -1 and self.data_path.zero:
            return minstr.if_zero
        if minstr.if_carry != -1 and self.data_path.carry:
            return minstr.if_carry
        if minstr.if_op[1] != -1:
            assert isinstance(alu_result, tuple), f"Expected instruction, got data: '{alu_result}'"
            if alu_result[0] == minstr.if_op[0]:
                return minstr.if_op[1]   
        return self.mpc + 1

    def _execute_operation_mi(self, minstr: isa.MIOperation) -> None:
        self.data_path.signal_write_register(minstr.x_sel, minstr.y_sel, minstr.alu_ctrl, minstr.rwr_sel)
        if minstr.mem_wr:
            self.data_path.signal_mem_wr()
        if minstr.mem_rd:
            self.data_path.signal_mem_rd()
        if minstr.halt:
            raise StopIteration("Got halt signal")

def _valid_register(reg: int) -> bool:
    return 0 <= reg and reg < isa.REG_N

if __name__ == "__main__":
    assert len(sys.argv) == 3
    main(sys.argv[1], sys.argv[2])