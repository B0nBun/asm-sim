from __future__ import annotations
from typing import NamedTuple, Optional, Sequence, Callable, Generator, Final, TypeAlias
from dataclasses import dataclass
import re
from enum import Enum
import sys


def main(source: str) -> None:
    input = ""
    with open(source, "r") as f:
        input = f.read()
    lexer = Lexer.new(input)
    tokens = lexer.run()
    for token in tokens:
        if token.type == TokenType.ERROR:
            print("error:", token.literal)
            return
        print(token)


class TokenType(Enum):
    LABEL = "label"
    OP = "op"
    ARG_REG = "argument_register"
    ARG_UINT = "argument_uint"
    ARG_LABEL = "argument_label"
    STR = "string"
    ERROR = "error"
    EOF = "eof"


class Token(NamedTuple):
    type: TokenType
    literal: str

    def __repr__(self) -> str:
        truncated = self.literal[:10] + ".." if len(self.literal) > 10 else self.literal
        return f"Token({self.type.name}, '{truncated}')"


StateFn: TypeAlias = Callable[["Lexer"], Optional["StateFn"]]


@dataclass
class Lexer:
    input: str
    start: int
    pos: int
    tokens: list[Token]

    EOF: Final[str] = "\0"

    @staticmethod
    def new(input: str) -> Lexer:
        without_comments = "\n".join(line.partition(";")[0] for line in input.splitlines())
        l = Lexer(input=without_comments, start=0, pos=0, tokens=[])
        return l

    @staticmethod
    def lex_label_or_op_or_str(l: Lexer) -> Optional[StateFn]:
        peek = l._peek()
        if peek == '"':
            return Lexer.lex_string
        if re.match(r"^[a-zA-Z_]+:", l.input[l.pos :]):
            return Lexer.lex_label
        if peek.isalpha():
            return Lexer.lex_op
        if peek == Lexer.EOF:
            l._emit(TokenType.EOF)
            return None
        return l._error("Expected label, string, op or EOF")

    @staticmethod
    def lex_string(l: Lexer) -> Optional[StateFn]:
        assert l._accept(lambda c: c == '"')
        l._accept_run(lambda c: c != '"' and c != "\n")
        assert l._accept(lambda c: c == '"')
        l._emit(TokenType.STR)
        l._skip_ws()
        return Lexer.lex_label_or_op_or_str

    @staticmethod
    def lex_label(l: Lexer) -> Optional[StateFn]:
        assert l._accept_run(lambda c: re.match(r"[a-zA-Z_]", c) is not None) > 0
        l._emit(TokenType.LABEL)
        assert l._skip(lambda c: c == ":")
        l._skip_ws()
        return Lexer.lex_label_or_op_or_str

    @staticmethod
    def lex_op(l: Lexer) -> Optional[StateFn]:
        assert l._accept_run(str.isalpha) > 0
        l._emit(TokenType.OP)
        if not (l._peek().isspace() or l._peek() == Lexer.EOF):
            return l._error("Expected whitespace or eof after op")
        l._skip_ws(skip_newline=False)
        return Lexer.lex_args

    @staticmethod
    def lex_args(l: Lexer) -> Optional[StateFn]:
        peek = l._peek()
        if peek == "\n" or peek == Lexer.EOF:
            l._skip(lambda c: c == "\n" or c == Lexer.EOF)
            l._skip_ws()
            return Lexer.lex_label_or_op_or_str
        if peek.isnumeric():
            return Lexer.lex_arg_uint
        if peek == "$":
            return Lexer.lex_arg_reg
        if peek.isalpha():
            return Lexer.lex_arg_label
        return l._error("Expected register, uint or label argument")

    @staticmethod
    def lex_arg_uint(l: Lexer) -> Optional[StateFn]:
        assert l._accept_run(str.isnumeric) > 0
        l._emit(TokenType.ARG_UINT)
        l._skip_ws(skip_newline=False)
        l._skip(lambda c: c == ",")
        l._skip_ws(skip_newline=False)
        return Lexer.lex_args

    @staticmethod
    def lex_arg_reg(l: Lexer) -> Optional[StateFn]:
        assert l._accept(lambda c: c == "$")
        if l._accept_run(str.isnumeric) == 0:
            return l._error("Expected register index")
        l._emit(TokenType.ARG_REG)
        l._skip_ws(skip_newline=False)
        l._skip(lambda c: c == ",")
        l._skip_ws(skip_newline=False)
        return Lexer.lex_args

    @staticmethod
    def lex_arg_label(l: Lexer) -> Optional[StateFn]:
        assert l._accept_run(lambda c: re.match(r"[A-Za-z_]", c) is not None) > 0
        l._emit(TokenType.ARG_LABEL)
        l._skip_ws(skip_newline=False)
        l._skip(lambda c: c == ",")
        l._skip_ws(skip_newline=False)
        return Lexer.lex_args

    def run(self) -> list[Token]:
        self._skip_ws()
        state: Optional[StateFn] = Lexer.lex_label_or_op_or_str
        while state is not None:
            state = state(self)
        return self.tokens

    def _emit(self, ty: TokenType) -> None:
        self.tokens.append(Token(type=ty, literal=self.input[self.start : self.pos]))
        self.start = self.pos

    def _next(self) -> str:
        if self.pos >= len(self.input):
            self.pos = len(self.input) + 1
            return Lexer.EOF
        c = self.input[self.pos]
        self.pos += 1
        return c

    def _backup(self) -> None:
        self.pos = max(0, self.pos - 1)

    def _ignore(self) -> None:
        self.start = self.pos

    def _peek(self) -> str:
        c = self._next()
        self._backup()
        return c

    def _accept(self, valid: Callable[[str], bool]) -> bool:
        if valid(self._next()):
            return True
        self._backup()
        return False

    def _accept_run(self, valid: Callable[[str], bool]) -> int:
        len = 0
        while valid(self._next()):
            len += 1
        self._backup()
        return len

    def _skip(self, skip: Callable[[str], bool]) -> bool:
        skipped = self._accept(skip)
        self._ignore()
        return skipped

    def _skip_run(self, skip: Callable[[str], bool]) -> int:
        skipped = self._accept_run(skip)
        self._ignore()
        return skipped

    def _skip_ws(self, *, skip_newline: bool = True) -> int:
        return self._skip_run(lambda c: c.isspace() and (skip_newline or c != "\n"))

    def _error(self, msg: str) -> StateFn:
        def error_state_fn(l: Lexer) -> Optional[StateFn]:
            self.tokens.append(Token(type=TokenType.ERROR, literal=msg))
            return None

        return error_state_fn


if __name__ == "__main__":
    assert len(sys.argv) == 2
    main(sys.argv[1])
