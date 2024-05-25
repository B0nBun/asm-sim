from __future__ import annotations
from typing import Generator, Optional
import lexer as lex
import isa
import math
import sys


def main(source: str, out_target: str) -> None:
    with open(source, "r") as f:
        input = f.read()
    program = translate(input)
    with open(out_target, "wb") as f:
        isa.write_program(program, f)

def translate(input: str) -> isa.Program:
    l = lex.Lexer.new(input)
    tokens = l.run()
    for token in tokens:
        assert token.type != lex.TokenType.ERROR, f"Lexer error: {token.literal}"
    labels = labels_from_tokens(tokens)
    assert "start" in labels, "No 'start' label in the program"
    instructions = instructions_from_tokens(tokens, labels)
    return isa.Program(start=labels["start"], instructions=instructions)


def labels_from_tokens(tokens: list[lex.Token]) -> dict[str, int]:
    labels = isa.PREDEFINED_LABELS.copy()
    for pc, token in tokens_with_pc(tokens):
        if token.type == lex.TokenType.LABEL:
            labels[token.literal] = pc
    return labels


def instructions_from_tokens(
    tokens: list[lex.Token], labels: dict[str, int]
) -> list[isa.MemoryWord]:
    program: list[isa.MemoryWord] = []
    while len(tokens) > 0:
        token = tokens.pop(0)
        if token.type in [lex.TokenType.LABEL, lex.TokenType.EOF]:
            continue
        if token.type == lex.TokenType.STR:
            words = string_token_to_words(token)
            program.extend(words)
            continue
        if token.type == lex.TokenType.OP:
            op = op_from_token(token)
            assert op is not None, f"Unknown op '{token.literal}'"
            args, tokens = arguments_from_tokens(tokens, labels)
            instruction = isa.instruction_from_args(op, args)
            program.append(instruction)
            continue
        assert False, f"Expected label, string, op or EOF, but got {token}"
    return program


def tokens_with_pc(
    tokens: list[lex.Token],
) -> Generator[tuple[int, lex.Token], None, None]:
    pc = isa.ORIGIN
    for token in tokens:
        yield (pc, token)
        if token.type == lex.TokenType.OP:
            pc += 1
        if token.type == lex.TokenType.STR:
            pc += len(string_token_to_words(token))


def string_token_to_words(token: lex.Token) -> list[isa.MemoryWord]:
    assert token.type == lex.TokenType.STR
    words: list[isa.MemoryWord] = []
    escaped = token.literal[1:-1].encode("raw_unicode_escape").decode("unicode_escape")
    for i in range(0, len(escaped)):
        ascii = ord(escaped[i])
        assert ascii <= 255, "Only ASCII characters in string literals"
        words.append(ascii)
    return words


def arguments_from_tokens(
    tokens: list[lex.Token], labels: dict[str, int]
) -> tuple[list[isa.ImmArg | isa.RegArg], list[lex.Token]]:
    args: list[isa.ImmArg | isa.RegArg] = []
    for token in tokens:
        if token.type == lex.TokenType.ARG_LABEL:
            assert token.literal in labels, f"Label '{token.literal}' is used, but not declared"
            addr = labels[token.literal]
            args.append(isa.ImmArg(addr))
        elif token.type == lex.TokenType.ARG_REG:
            idx = int(token.literal[1:])
            assert 0 <= idx and idx < isa.GEN_REG_N, f"Undefined register ${idx} used"
            args.append(isa.RegArg(idx))
        elif token.type == lex.TokenType.ARG_UINT:
            num = int(token.literal)
            assert num < 2**32, f"Immediate values can be up to 2^32 ({2**32}), but {num} was used"
            args.append(isa.ImmArg(num))
        else:
            break
    return (args, tokens[len(args) :])


def op_from_token(token: lex.Token) -> Optional[isa.Op]:
    assert token.type == lex.TokenType.OP
    return next((op for op in isa.Op if op.name.lower() == token.literal), None)


if __name__ == "__main__":
    assert len(sys.argv) == 3
    main(sys.argv[1], sys.argv[2])
