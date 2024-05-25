from typing import NamedTuple, TypeAlias, Final, Generator, Optional, BinaryIO, Callable, NewType, Union
from enum import Enum
from utils import iota, iota_reset
import math
import pickle

GEN_REG_N: Final[int] = 6
AR = GEN_REG_N
DR = GEN_REG_N + iota()
PC = GEN_REG_N + iota()
OR1 = GEN_REG_N + iota()
OR2 = GEN_REG_N + iota()
OR3 = GEN_REG_N + iota()
REG_N = GEN_REG_N + iota_reset()
IND_AR = -1
IND_AR_MASK = pow(2, math.ceil(math.log(REG_N) / math.log(2))) - 1

ORIGIN: Final[int] = 0
MEMORY_SIZE = 0xFFFF
INPUT_DEVICE_ADDR = 0xFF00
OUTPUT_DEVICE_ADDR = 0xFF01
PREDEFINED_LABELS: Final[dict[str, int]] = {
    "input": INPUT_DEVICE_ADDR,
    "output": OUTPUT_DEVICE_ADDR,
}


class OpType(Enum):
    RRI = iota()
    RRR = iota()
    NOARG = iota_reset()


class Op(Enum):
    LW = iota(), OpType.RRI
    SW = iota(), OpType.RRI
    BEQ = iota(), OpType.RRI
    BLEQ = iota(), OpType.RRI
    ADDI = iota(), OpType.RRI
    ADD = iota(), OpType.RRR
    SHR = iota(), OpType.RRI
    HALT = iota_reset(), OpType.NOARG

    def code(self) -> int:
        return self.value[0]

    def type(self) -> OpType:
        return self.value[1]

    def __repr__(self) -> str:
        return self.name


class ImmArg(NamedTuple):
    val: int


class RegArg(NamedTuple):
    idx: int


Instruction: TypeAlias = Union[
    tuple[Op, RegArg, RegArg, ImmArg],
    tuple[Op, RegArg, RegArg, RegArg],
    tuple[Op],
]


def instruction_from_args(op: Op, args: list[ImmArg | RegArg]) -> Instruction:
    match op.type(), args:
        case OpType.RRR, [RegArg(_) as r1, RegArg(_) as r2, RegArg(_) as r3]:
            return (op, r1, r2, r3)
        case OpType.RRI, [RegArg(_) as r1, RegArg(_) as r2, ImmArg(_) as im]:
            return (op, r1, r2, im)
        case OpType.NOARG, []:
            return (op,)
    assert False, f"Got unexpected arguments for op {op} ({args})"


MemoryWord: TypeAlias = Instruction | int


class ALUControl(Enum):
    add = 0
    inc = iota()
    sub = iota()
    shr = iota()
    only_x = iota()
    mask_fst_r = iota()
    mask_snd_r = iota()
    mask_thrd_r = iota()
    mask_imm = iota_reset()

    def call(self, x: MemoryWord, y: MemoryWord) -> tuple[MemoryWord, bool]:
        match self, x, y:
            case ALUControl.add, int(x), int(y):
                return (x + y, x + y > 0xFFFFFFFF)
            case ALUControl.shr, int(x), int(y):
                return (x >> y, False)
            case ALUControl.inc, int(x), _:
                return (x + 1, x + 1 > 0xFFFFFFFF)
            case ALUControl.sub, int(x), int(y):
                return (x - y, x < y)
            case ALUControl.only_x, x, _:
                return (x, False)
            case ALUControl.mask_fst_r, (_, RegArg(r), _, _), _:
                return (r, False)
            case ALUControl.mask_snd_r, (_, _, RegArg(r), _), _:
                return (r, False)
            case ALUControl.mask_thrd_r, (_, _, _, RegArg(r)), _:
                return (r, False)
            case ALUControl.mask_imm, (_, _, _, ImmArg(n)), _:
                return (n, False)
        assert False, f"Unreachable: '{self}' '{x}' '{y}'"


class MIJump(NamedTuple):
    x_sel: int = 0
    y_sel: int = 0
    alu_ctrl: ALUControl = ALUControl.only_x

    if_zero: int = -1
    if_carry: int = -1
    if_op: tuple[Op, int] = (Op.HALT, -1)
    to: int = -1

    def __repr__(self) -> str:
        if self.to != -1:
            return f"jump {self.to}"
        res = f"jmp:{self.alu_ctrl.name}({self.x_sel}, {self.y_sel})"
        if self.if_zero != -1:
            res += f" Z -> {self.if_zero}"
        if self.if_carry != -1:
            res += f" C -> {self.if_carry}"
        if self.if_op[1] != -1:
            res += f" {self.if_op[0].name} -> {self.if_op[1]}"
        return res

class MIOperation(NamedTuple):
    x_sel: int = 0
    y_sel: int = 0
    alu_ctrl: ALUControl = ALUControl.only_x
    rwr_sel: int = 0
    mem_wr: bool = False
    mem_rd: bool = False
    halt: bool = False

    def __repr__(self) -> str:
        return (
            f"op:{self.alu_ctrl.name}(${self.x_sel}, ${self.y_sel}) -> ${self.rwr_sel}"
            f"{' WR' if self.mem_wr else ''}{' RD' if self.mem_rd else ''}{' STOP' if self.halt else ''}"
        )


MInstruction: TypeAlias = MIOperation | MIJump


class Program(NamedTuple):
    start: int
    instructions: list[MemoryWord]


def write_program(program: Program, out: BinaryIO) -> None:
    pickle.dump(program, out)


def read_program(src: BinaryIO) -> Program:
    loaded = pickle.load(src)
    assert isinstance(loaded, Program), f"Expected to read a program, but got {loaded.__class__}"
    return loaded
