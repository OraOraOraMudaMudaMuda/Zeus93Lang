#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Desktop GUI for converting text into ZeusLang source."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


PROGRAM_START = "안녕하세요"
PROGRAM_END = "아 재밌었다"
STMT_END = "발 존나 기네"
PRINT = "블블"
STRING_START = "점프를 하고싶으면"
STRING_END = "점프킹을 해!"
CHAR_SEP = "이런이런"
PREVIOUS_CHAR = "웨얼 이즈 롤백 넷코드?"
PLUS = "모리"
MINUS = "후추"
BIT_ONE = "아잇"
BIT_ZERO = "시발!"


def to_zeus_binary(value: int) -> str:
    bits = bin(value)[2:]
    return "".join(BIT_ONE if bit == "1" else BIT_ZERO for bit in bits)


def encode(text: str) -> str:
    """Return a complete ZeusLang program that prints *text*."""
    characters: list[str] = []
    previous_codepoint: int | None = None

    for character in text:
        codepoint = ord(character)

        if previous_codepoint is None:
            # 문자열의 첫 글자는 이전 글자가 없으므로 절대 코드값을 사용한다.
            expression = to_zeus_binary(codepoint)
        else:
            # 이후 글자는 항상 이전 글자의 코드값을 기준으로 표현한다.
            difference = codepoint - previous_codepoint
            if difference == 0:
                expression = PREVIOUS_CHAR
            else:
                operator = PLUS if difference > 0 else MINUS
                expression = (
                    f"{PREVIOUS_CHAR} {operator} "
                    f"{to_zeus_binary(abs(difference))}"
                )

        characters.append(expression)
        previous_codepoint = codepoint

    string_body = f" {CHAR_SEP}\n".join(characters)
    if string_body:
        string_body = f"\n{string_body}\n"

    return (
        f"{PROGRAM_START}\n"
        f"{PRINT} {STRING_START}{string_body}{STRING_END} {STMT_END}\n"
        f"{PROGRAM_END}\n"
    )


class ZeusLangConverterApp(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=16)
        self.master = master
        self.status = tk.StringVar(value="입력한 문자열을 ZeusLang 코드로 변환합니다.")
        self.create_widgets()

    def create_widgets(self) -> None:
        self.grid(sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(4, weight=1)

        ttk.Label(self, text="입력 문자열").grid(row=0, column=0, sticky="w")
        self.input_text = tk.Text(self, height=8, wrap="word", undo=True)
        self.input_text.grid(row=1, column=0, sticky="nsew", pady=(4, 12))

        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, sticky="ew", pady=(0, 12))
        ttk.Button(button_frame, text="ZeusLang으로 변환", command=self.convert).pack(
            side="left"
        )
        ttk.Button(button_frame, text="결과 복사", command=self.copy_output).pack(
            side="left", padx=8
        )
        ttk.Button(button_frame, text="모두 지우기", command=self.clear).pack(side="left")

        ttk.Label(self, text="ZeusLang 출력").grid(row=3, column=0, sticky="w")
        self.output_text = tk.Text(self, height=16, wrap="word", undo=True)
        self.output_text.grid(row=4, column=0, sticky="nsew", pady=(4, 8))

        ttk.Label(self, textvariable=self.status).grid(row=5, column=0, sticky="w")

        self.input_text.bind("<Control-Return>", self.convert)
        self.input_text.focus_set()

    def convert(self, _event: tk.Event[tk.Misc] | None = None) -> str:
        text = self.input_text.get("1.0", "end-1c")
        program = encode(text)

        self.output_text.delete("1.0", "end")
        self.output_text.insert("1.0", program)
        self.status.set(f"{len(text)}개 문자를 ZeusLang 소스로 변환했습니다.")
        return "break"

    def copy_output(self) -> None:
        output = self.output_text.get("1.0", "end-1c")
        self.master.clipboard_clear()
        self.master.clipboard_append(output)
        self.master.update()
        self.status.set("ZeusLang 소스를 클립보드에 복사했습니다.")

    def clear(self) -> None:
        self.input_text.delete("1.0", "end")
        self.output_text.delete("1.0", "end")
        self.status.set("입력과 출력을 지웠습니다.")
        self.input_text.focus_set()


def main() -> None:
    root = tk.Tk()
    root.title("ZeusLang 문자열 변환기")
    root.minsize(640, 560)
    root.geometry("760x680")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    ZeusLangConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
