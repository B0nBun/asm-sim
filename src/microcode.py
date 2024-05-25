from __future__ import annotations

from typing import Callable, Final, TypeAlias

import isa
from isa import MIJump, MIOperation, Op

_load_0rr: Final[list[isa.MInstruction]] = [
    MIOperation(x_sel=isa.DR, alu_ctrl=isa.ALUControl.mask_snd_r, rwr_sel=isa.AR),
    MIOperation(x_sel=isa.IND_AR, rwr_sel=isa.OR2),
    MIOperation(x_sel=isa.DR, alu_ctrl=isa.ALUControl.mask_thrd_r, rwr_sel=isa.AR),
    MIOperation(x_sel=isa.IND_AR, rwr_sel=isa.OR3),
]

_load_rri: Final[list[isa.MInstruction]] = [
    MIOperation(x_sel=isa.DR, alu_ctrl=isa.ALUControl.mask_fst_r, rwr_sel=isa.AR),
    MIOperation(x_sel=isa.IND_AR, rwr_sel=isa.OR1),
    MIOperation(x_sel=isa.DR, alu_ctrl=isa.ALUControl.mask_snd_r, rwr_sel=isa.AR),
    MIOperation(x_sel=isa.IND_AR, rwr_sel=isa.OR2),
    MIOperation(x_sel=isa.DR, alu_ctrl=isa.ALUControl.mask_imm, rwr_sel=isa.OR3),
]

_load_0ri: Final[list[isa.MInstruction]] = [
    MIOperation(x_sel=isa.DR, alu_ctrl=isa.ALUControl.mask_snd_r, rwr_sel=isa.AR),
    MIOperation(x_sel=isa.IND_AR, rwr_sel=isa.OR2),
    MIOperation(x_sel=isa.DR, alu_ctrl=isa.ALUControl.mask_imm, rwr_sel=isa.OR3),
]

LabelFunc: TypeAlias = Callable[[str], int]


def _with_labels(get_microcode: Callable[[LabelFunc], list[isa.MInstruction | str]]) -> list[isa.MInstruction]:
    mc_with_stubs = get_microcode(lambda _: 0)
    labels: dict[str, int] = {}
    labels_encountered = 0
    for idx, mi in enumerate(mc_with_stubs):
        if isinstance(mi, str):
            label = mi
            labels[label] = idx - labels_encountered
            labels_encountered += 1
    return [mi for mi in get_microcode(lambda label: labels[label]) if not isinstance(mi, str)]


microcode: Final[list[isa.MInstruction]] = _with_labels(
    lambda label: [
        "instruction_fetch",
        MIOperation(x_sel=isa.PC, rwr_sel=isa.AR, mem_rd=True),
        MIJump(x_sel=isa.DR, if_op=(Op.LW, label("LW"))),
        MIJump(x_sel=isa.DR, if_op=(Op.SW, label("SW"))),
        MIJump(x_sel=isa.DR, if_op=(Op.BEQ, label("BEQ"))),
        MIJump(x_sel=isa.DR, if_op=(Op.BLEQ, label("BLEQ"))),
        MIJump(x_sel=isa.DR, if_op=(Op.ADDI, label("ADDI"))),
        MIJump(x_sel=isa.DR, if_op=(Op.ANDI, label("ANDI"))),
        MIJump(x_sel=isa.DR, if_op=(Op.SHR, label("SHR"))),
        MIJump(x_sel=isa.DR, if_op=(Op.ADD, label("ADD"))),
        MIJump(x_sel=isa.DR, if_op=(Op.HALT, label("HALT"))),
        "LW",
        *_load_0ri,
        MIOperation(x_sel=isa.DR, alu_ctrl=isa.ALUControl.mask_fst_r, rwr_sel=isa.OR1),
        MIOperation(x_sel=isa.OR2, y_sel=isa.OR3, alu_ctrl=isa.ALUControl.add, rwr_sel=isa.AR),
        MIOperation(mem_rd=True),
        MIOperation(x_sel=isa.OR1, rwr_sel=isa.AR),
        MIOperation(x_sel=isa.DR, rwr_sel=isa.IND_AR),
        MIJump(to=label("increment_pc")),
        "SW",
        *_load_rri,
        MIOperation(x_sel=isa.OR2, y_sel=isa.OR3, alu_ctrl=isa.ALUControl.add, rwr_sel=isa.AR),
        MIOperation(x_sel=isa.OR1, rwr_sel=isa.DR, mem_wr=True),
        MIJump(to=label("increment_pc")),
        "BEQ",
        *_load_rri,
        MIJump(x_sel=isa.OR1, y_sel=isa.OR2, alu_ctrl=isa.ALUControl.sub, if_zero=label("BEQ_jmp")),
        MIJump(to=label("increment_pc")),
        "BEQ_jmp",
        MIOperation(x_sel=isa.OR3, rwr_sel=isa.PC),
        MIJump(to=label("instruction_fetch")),
        "BLEQ",
        *_load_rri,
        MIJump(
            x_sel=isa.OR1,
            y_sel=isa.OR2,
            alu_ctrl=isa.ALUControl.sub,
            if_carry=label("BLEQ_jmp"),
            if_zero=label("BLEQ_jmp"),
        ),
        MIJump(to=label("increment_pc")),
        "BLEQ_jmp",
        MIOperation(x_sel=isa.OR3, rwr_sel=isa.PC),
        MIJump(to=label("instruction_fetch")),
        "ADDI",
        *_load_0ri,
        MIOperation(x_sel=isa.DR, alu_ctrl=isa.ALUControl.mask_fst_r, rwr_sel=isa.AR),
        MIOperation(x_sel=isa.OR2, y_sel=isa.OR3, alu_ctrl=isa.ALUControl.add, rwr_sel=isa.IND_AR),
        MIJump(to=label("increment_pc")),
        "ANDI",
        *_load_0ri,
        MIOperation(x_sel=isa.DR, alu_ctrl=isa.ALUControl.mask_fst_r, rwr_sel=isa.AR),
        MIOperation(x_sel=isa.OR2, y_sel=isa.OR3, alu_ctrl=isa.ALUControl.band, rwr_sel=isa.IND_AR),
        MIJump(to=label("increment_pc")),
        "SHR",
        *_load_0ri,
        MIOperation(x_sel=isa.DR, alu_ctrl=isa.ALUControl.mask_fst_r, rwr_sel=isa.AR),
        MIOperation(x_sel=isa.OR2, y_sel=isa.OR3, alu_ctrl=isa.ALUControl.shr, rwr_sel=isa.IND_AR),
        MIJump(to=label("increment_pc")),
        "ADD",
        *_load_0rr,
        MIOperation(x_sel=isa.DR, alu_ctrl=isa.ALUControl.mask_fst_r, rwr_sel=isa.AR),
        MIOperation(x_sel=isa.OR2, y_sel=isa.OR3, alu_ctrl=isa.ALUControl.add, rwr_sel=isa.IND_AR),
        MIJump(to=label("increment_pc")),
        "HALT",
        MIOperation(halt=True),
        "increment_pc",
        MIOperation(x_sel=isa.PC, alu_ctrl=isa.ALUControl.inc, rwr_sel=isa.PC),
        MIJump(to=label("instruction_fetch")),
    ]
)
