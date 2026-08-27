#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ZeusLang v0.2 Interpreter

현재 문법
=========
안녕하세요                    : 프로그램 시작
아 재밌었다                   : 프로그램 종료
발 존나 기네                  : 일반 문장 종료

애송이가? <이진수>            : 변수 참조 / 대입문의 변수 번호
제하하핳                       : 대입 (=)

아잇                          : 이진수 비트 1
시발!                         : 이진수 비트 0

모리                          : +
후추                          : -
후쿠하라                      : *
이시와타리                    : /

블블                          : 출력
점프를 하고싶으면             : 문자열 시작
점프킹을 해!                  : 문자열 끝
이런이런                      : 문자열의 다음 문자
웨얼 이즈 롤백 넷코드?        : 문자열에서 직전 문자 코드값

왓 디스 이즈 갈비지 게임?    : if
어메이징시발롬                : while
무능한남                      : 블록 시작 {
도태딜러                      : 블록 끝 }

댄서 <비교코드>               : 비교 연산자
    댄서 시발!                : ==
    댄서 아잇                 : !=
    댄서 아잇시발!            : >
    댄서 아잇아잇             : <
    댄서 아잇시발!시발!       : >=
    댄서 아잇시발!아잇        : <=

중요
====
이진수는 공백 없이 붙여 써야 하나의 숫자로 인식됩니다.

예:
    아잇시발!아잇   -> 101(2) -> 5

    아잇 시발! 아잇
은 서로 다른 숫자 1, 0, 1로 인식됩니다.

실행:
    python rollback_lang_interpreter.py program.rbk
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Optional


# ============================================================
# 오류
# ============================================================

class ZeusError(Exception):
    pass


# ============================================================
# 토큰
# ============================================================

@dataclass
class Token:
    type: str
    text: str
    pos: int
    value: Optional[int] = None


FIXED_KEYWORDS = [
    ("PROGRAM_START", "안녕하세요"),
    ("PROGRAM_END", "아 재밌었다"),
    ("STMT_END", "발 존나 기네"),

    ("VAR", "애송이가?"),
    ("ASSIGN", "제하하핳"),

    ("PRINT", "블블"),
    ("STRING_START", "점프를 하고싶으면"),
    ("STRING_END", "점프킹을 해!"),
    ("CHAR_SEP", "이런이런"),
    ("PREV_CHAR", "웨얼 이즈 롤백 넷코드?"),

    ("IF", "왓 디스 이즈 갈비지 게임?"),
    ("WHILE", "어메이징시발롬"),
    ("BLOCK_START", "무능한남"),
    ("BLOCK_END", "도태딜러"),

    ("COMPARE", "댄서"),

    ("PLUS", "모리"),
    ("MINUS", "후추"),
    ("MUL", "후쿠하라"),
    ("DIV", "이시와타리"),
]

# 겹치는 문구가 생겨도 긴 토큰부터 우선 인식
FIXED_KEYWORDS.sort(key=lambda item: len(item[1]), reverse=True)

BIT_ONE = "아잇"
BIT_ZERO = "시발!"


def tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0

    while i < len(source):
        # 공백/줄바꿈은 문법적으로 의미 없음
        if source[i].isspace():
            i += 1
            continue

        # 1) 고정 키워드를 먼저 검사
        matched = False
        for token_type, token_text in FIXED_KEYWORDS:
            if source.startswith(token_text, i):
                tokens.append(Token(token_type, token_text, i))
                i += len(token_text)
                matched = True
                break

        if matched:
            continue

        # 2) 아잇/시발!이 연속해서 붙어 있으면 하나의 이진수 리터럴
        if source.startswith(BIT_ONE, i) or source.startswith(BIT_ZERO, i):
            start = i
            bits: list[str] = []

            while i < len(source):
                if source.startswith(BIT_ONE, i):
                    bits.append("1")
                    i += len(BIT_ONE)
                elif source.startswith(BIT_ZERO, i):
                    bits.append("0")
                    i += len(BIT_ZERO)
                else:
                    break

            bit_string = "".join(bits)
            tokens.append(
                Token(
                    "NUMBER",
                    source[start:i],
                    start,
                    int(bit_string, 2),
                )
            )
            continue

        snippet = source[i:i + 30].replace("\n", "\\n")
        raise ZeusError(
            f"알 수 없는 문법입니다.\n"
            f"위치: {i}\n"
            f"근처 내용: {snippet}"
        )

    tokens.append(Token("EOF", "", len(source)))
    return tokens


# ============================================================
# AST - 표현식
# ============================================================

class Expr:
    pass


@dataclass
class NumberExpr(Expr):
    value: int


@dataclass
class VarExpr(Expr):
    var_id: int


@dataclass
class PreviousCharExpr(Expr):
    pass


@dataclass
class BinaryExpr(Expr):
    left: Expr
    op: str
    right: Expr


# ============================================================
# AST - 조건
# ============================================================

@dataclass
class CompareExpr:
    left: Expr
    op: str
    right: Expr


# ============================================================
# AST - 문장
# ============================================================

class Stmt:
    pass


@dataclass
class AssignStmt(Stmt):
    var_id: int
    value: Expr


@dataclass
class PrintNumberStmt(Stmt):
    value: Expr


@dataclass
class StringExpr:
    chars: list[Expr]


@dataclass
class PrintStringStmt(Stmt):
    value: StringExpr


@dataclass
class IfStmt(Stmt):
    condition: CompareExpr
    body: list[Stmt]


@dataclass
class WhileStmt(Stmt):
    condition: CompareExpr
    body: list[Stmt]


# ============================================================
# Parser
# ============================================================

COMPARE_CODES = {
    0: "==",
    1: "!=",
    2: ">",
    3: "<",
    4: ">=",
    5: "<=",
}


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def check(self, token_type: str) -> bool:
        return self.peek().type == token_type

    def advance(self) -> Token:
        token = self.peek()
        if token.type != "EOF":
            self.current += 1
        return token

    def match(self, *token_types: str) -> bool:
        if self.peek().type in token_types:
            self.advance()
            return True
        return False

    def expect(self, token_type: str, message: str) -> Token:
        if not self.check(token_type):
            token = self.peek()
            raise ZeusError(
                f"{message}\n"
                f"현재 토큰: {token.text or token.type}\n"
                f"위치: {token.pos}"
            )
        return self.advance()

    def parse(self) -> list[Stmt]:
        self.expect(
            "PROGRAM_START",
            "프로그램은 '안녕하세요'로 시작해야 합니다.",
        )

        statements: list[Stmt] = []

        while not self.check("PROGRAM_END"):
            if self.check("EOF"):
                raise ZeusError(
                    "프로그램 마지막에 '아 재밌었다'가 필요합니다."
                )
            statements.append(self.parse_statement())

        self.expect("PROGRAM_END", "'아 재밌었다'가 필요합니다.")

        if not self.check("EOF"):
            token = self.peek()
            raise ZeusError(
                "'아 재밌었다' 뒤에는 코드를 작성할 수 없습니다.\n"
                f"위치: {token.pos}"
            )

        return statements

    def parse_statement(self) -> Stmt:
        if self.check("VAR"):
            stmt = self.parse_assignment()
            self.expect(
                "STMT_END",
                "대입문은 '발 존나 기네'로 끝나야 합니다.",
            )
            return stmt

        if self.check("PRINT"):
            stmt = self.parse_print()
            self.expect(
                "STMT_END",
                "출력문은 '발 존나 기네'로 끝나야 합니다.",
            )
            return stmt

        if self.check("IF"):
            stmt = self.parse_if()
            # 블록 자체는 도태딜러로 끝남.
            # 원하면 뒤에 '발 존나 기네'를 붙여도 허용.
            self.match("STMT_END")
            return stmt

        if self.check("WHILE"):
            stmt = self.parse_while()
            self.match("STMT_END")
            return stmt

        token = self.peek()
        raise ZeusError(
            f"문장을 시작할 수 없습니다.\n"
            f"현재 토큰: {token.text or token.type}\n"
            f"위치: {token.pos}"
        )

    # --------------------------------------------------------
    # 변수 대입
    #
    # 애송이가? 시발! 제하하핳 아잇시발!아잇 발 존나 기네
    # var0 = 5;
    # --------------------------------------------------------

    def parse_assignment(self) -> AssignStmt:
        self.expect("VAR", "'애송이가?'가 필요합니다.")
        var_id = self.expect_number("변수 번호가 필요합니다.")

        self.expect(
            "ASSIGN",
            "변수 대입에는 '제하하핳'이 필요합니다.",
        )

        value = self.parse_expression()
        return AssignStmt(var_id, value)

    # --------------------------------------------------------
    # 출력
    # --------------------------------------------------------

    def parse_print(self) -> Stmt:
        self.expect("PRINT", "'블블'이 필요합니다.")

        if self.check("STRING_START"):
            return PrintStringStmt(self.parse_string())

        return PrintNumberStmt(self.parse_expression())

    # --------------------------------------------------------
    # 문자열
    #
    # 블블 점프를 하고싶으면
    #   <문자값>
    #   이런이런
    #   <다음 문자값>
    # 점프킹을 해! 발 존나 기네
    # --------------------------------------------------------

    def parse_string(self) -> StringExpr:
        self.expect(
            "STRING_START",
            "문자열은 '점프를 하고싶으면'으로 시작해야 합니다.",
        )

        chars: list[Expr] = []

        if self.check("STRING_END"):
            self.advance()
            return StringExpr(chars)

        chars.append(self.parse_expression())

        while self.match("CHAR_SEP"):
            chars.append(self.parse_expression())

        self.expect(
            "STRING_END",
            "문자열은 '점프킹을 해!'로 끝나야 합니다.",
        )

        return StringExpr(chars)

    # --------------------------------------------------------
    # if
    #
    # 왓 디스 이즈 갈비지 게임?
    # <왼쪽값> 댄서 <비교코드> <오른쪽값>
    # 무능한남
    #   ...
    # 도태딜러
    # --------------------------------------------------------

    def parse_if(self) -> IfStmt:
        self.expect("IF", "'왓 디스 이즈 갈비지 게임?'이 필요합니다.")
        condition = self.parse_condition()
        body = self.parse_block()
        return IfStmt(condition, body)

    # --------------------------------------------------------
    # while
    # --------------------------------------------------------

    def parse_while(self) -> WhileStmt:
        self.expect("WHILE", "'어메이징시발롬'이 필요합니다.")
        condition = self.parse_condition()
        body = self.parse_block()
        return WhileStmt(condition, body)

    # --------------------------------------------------------
    # 조건식
    #
    # <표현식> 댄서 <비교코드> <표현식>
    # --------------------------------------------------------

    def parse_condition(self) -> CompareExpr:
        left = self.parse_expression()

        self.expect(
            "COMPARE",
            "조건식에는 비교 연산자 접두어 '댄서'가 필요합니다.",
        )

        code = self.expect_number(
            "'댄서' 뒤에는 비교 연산 코드가 필요합니다."
        )

        if code not in COMPARE_CODES:
            raise ZeusError(
                f"알 수 없는 비교 연산 코드입니다: {code}\n"
                f"사용 가능 코드: 0~5"
            )

        right = self.parse_expression()
        return CompareExpr(left, COMPARE_CODES[code], right)

    # --------------------------------------------------------
    # 블록
    # --------------------------------------------------------

    def parse_block(self) -> list[Stmt]:
        self.expect(
            "BLOCK_START",
            "블록은 '무능한남'으로 시작해야 합니다.",
        )

        body: list[Stmt] = []

        while not self.check("BLOCK_END"):
            if self.check("EOF") or self.check("PROGRAM_END"):
                raise ZeusError(
                    "블록 마지막에 '도태딜러'가 필요합니다."
                )
            body.append(self.parse_statement())

        self.expect(
            "BLOCK_END",
            "블록은 '도태딜러'로 끝나야 합니다.",
        )

        return body

    # ========================================================
    # 표현식
    #
    # 일반적인 우선순위:
    # * / 먼저
    # + - 나중
    # ========================================================

    def parse_expression(self) -> Expr:
        expr = self.parse_term()

        while self.match("PLUS", "MINUS"):
            op = self.previous().type
            right = self.parse_term()
            expr = BinaryExpr(expr, op, right)

        return expr

    def parse_term(self) -> Expr:
        expr = self.parse_factor()

        while self.match("MUL", "DIV"):
            op = self.previous().type
            right = self.parse_factor()
            expr = BinaryExpr(expr, op, right)

        return expr

    def parse_factor(self) -> Expr:
        if self.check("NUMBER"):
            token = self.advance()
            return NumberExpr(token.value)

        if self.check("VAR"):
            self.advance()
            var_id = self.expect_number(
                "'애송이가?' 뒤에는 변수 번호가 필요합니다."
            )
            return VarExpr(var_id)

        if self.match("PREV_CHAR"):
            return PreviousCharExpr()

        token = self.peek()
        raise ZeusError(
            f"숫자, 변수 또는 직전 문자값이 필요합니다.\n"
            f"현재 토큰: {token.text or token.type}\n"
            f"위치: {token.pos}"
        )

    def expect_number(self, message: str) -> int:
        token = self.expect("NUMBER", message)
        assert token.value is not None
        return token.value


# ============================================================
# 실행기
# ============================================================

class Interpreter:
    # while 무한루프 실수 방지용.
    # 필요하면 값을 늘리거나 None 방식으로 바꿔도 됨.
    MAX_WHILE_ITERATIONS = 1_000_000

    def __init__(self):
        self.variables: dict[int, float | int] = {}

    def run(self, statements: list[Stmt]) -> None:
        self.execute_block(statements)

    def execute_block(self, statements: list[Stmt]) -> None:
        for stmt in statements:
            self.execute(stmt)

    def execute(self, stmt: Stmt) -> None:
        if isinstance(stmt, AssignStmt):
            value = self.eval_expr(stmt.value)
            self.variables[stmt.var_id] = value
            return

        if isinstance(stmt, PrintNumberStmt):
            value = self.eval_expr(stmt.value)
            print(self.pretty_number(value))
            return

        if isinstance(stmt, PrintStringStmt):
            print(self.eval_string(stmt.value))
            return

        if isinstance(stmt, IfStmt):
            if self.eval_condition(stmt.condition):
                self.execute_block(stmt.body)
            return

        if isinstance(stmt, WhileStmt):
            count = 0

            while self.eval_condition(stmt.condition):
                self.execute_block(stmt.body)
                count += 1

                if count > self.MAX_WHILE_ITERATIONS:
                    raise ZeusError(
                        "while 반복 횟수가 안전 제한을 초과했습니다.\n"
                        "무한루프인지 확인해 주세요."
                    )
            return

        raise ZeusError(
            f"지원하지 않는 문장 타입입니다: {type(stmt).__name__}"
        )

    # --------------------------------------------------------
    # 표현식 계산
    # --------------------------------------------------------

    def eval_expr(
        self,
        expr: Expr,
        previous_char: Optional[int] = None,
    ) -> float | int:
        if isinstance(expr, NumberExpr):
            return expr.value

        if isinstance(expr, VarExpr):
            if expr.var_id not in self.variables:
                raise ZeusError(
                    f"{expr.var_id}번 변수는 아직 선언되지 않았습니다."
                )
            return self.variables[expr.var_id]

        if isinstance(expr, PreviousCharExpr):
            if previous_char is None:
                raise ZeusError(
                    "'웨얼 이즈 롤백 넷코드?'는 "
                    "문자열에서 이전 문자가 있을 때만 사용할 수 있습니다."
                )
            return previous_char

        if isinstance(expr, BinaryExpr):
            left = self.eval_expr(expr.left, previous_char)
            right = self.eval_expr(expr.right, previous_char)

            if expr.op == "PLUS":
                return left + right
            if expr.op == "MINUS":
                return left - right
            if expr.op == "MUL":
                return left * right
            if expr.op == "DIV":
                if right == 0:
                    raise ZeusError("0으로 나눌 수 없습니다.")
                return left / right

        raise ZeusError(
            f"지원하지 않는 표현식 타입입니다: {type(expr).__name__}"
        )

    # --------------------------------------------------------
    # 문자열 계산
    # --------------------------------------------------------

    def eval_string(self, string_expr: StringExpr) -> str:
        result: list[str] = []
        previous_char: Optional[int] = None

        for char_expr in string_expr.chars:
            value = self.eval_expr(char_expr, previous_char)

            if isinstance(value, float):
                if not value.is_integer():
                    raise ZeusError(
                        f"문자 코드값은 정수여야 합니다. 현재 값: {value}"
                    )
                value = int(value)

            codepoint = int(value)

            if not 0 <= codepoint <= 0x10FFFF:
                raise ZeusError(
                    f"유효하지 않은 Unicode 코드값입니다: {codepoint}"
                )

            result.append(chr(codepoint))
            previous_char = codepoint

        return "".join(result)

    # --------------------------------------------------------
    # 조건 계산
    # --------------------------------------------------------

    def eval_condition(self, condition: CompareExpr) -> bool:
        left = self.eval_expr(condition.left)
        right = self.eval_expr(condition.right)

        if condition.op == "==":
            return left == right
        if condition.op == "!=":
            return left != right
        if condition.op == ">":
            return left > right
        if condition.op == "<":
            return left < right
        if condition.op == ">=":
            return left >= right
        if condition.op == "<=":
            return left <= right

        raise ZeusError(
            f"지원하지 않는 비교 연산자입니다: {condition.op}"
        )

    @staticmethod
    def pretty_number(value: float | int) -> float | int:
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return value


# ============================================================
# 실행 진입점
# ============================================================

def main() -> None:
    if len(sys.argv) != 2:
        print("사용법: python zeus_lang_interpreter.py <프로그램파일>")
        print("예:     python zeus_lang_interpreter.py hello.rbk")
        return

    filename = sys.argv[1]

    try:
        with open(filename, "r", encoding="utf-8") as file:
            source = file.read()

        tokens = tokenize(source)
        statements = Parser(tokens).parse()

        interpreter = Interpreter()
        interpreter.run(statements)

    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {filename}")

    except ZeusError as error:
        print(f"[ZeusLang 오류]\n{error}")

    except UnicodeDecodeError:
        print("소스 파일은 UTF-8로 저장해 주세요.")


if __name__ == "__main__":
    main()
