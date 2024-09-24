#!/usr/bin/env python3
import contextlib
import sys
from types import ModuleType
from typing import Iterable, Iterator, Mapping, SupportsIndex, TypeVar, Any
import importlib
import argparse

class Pys:
    import_targets: list[str]|None
    relative_import: bool
    print_sep: str
    no_pipe: bool
    no_split: bool
    sep: str
    code: str

    def __init__(self) -> None:
        parser = argparse.ArgumentParser(
            prog='pyS',
            description='awk inspired command line tool using Python'
        )

        parser.add_argument('code')
        parser.add_argument('-i', '--import', help='modules to be imported', action='extend', dest='import_targets')
        parser.add_argument('-n', '--no-pipe', action='store_true', help='don\'t read arguments from stdin')
        parser.add_argument('--relative-import', action='store_true',
                            help='sets import behavior to \'import [module]\', instead of \' from [module] import *\'')
        parser.add_argument('--no-split', action='store_true', help='treat input as single argument')
        parser.add_argument('-s', '--sep', help='input arguments separator')
        parser.add_argument('-p', '--print-sep', help='output arguments separator')
        parser.add_argument('-V', '--version', action='version', version='0.9 demo')

        parser.parse_args(namespace=self)

        self.has_star = self.code[0] == "*"
        self.code = self.code if not self.has_star else self.code[1:]

    def run(self, locals: Mapping[str, object]|None = None) -> None:
        evaluated = eval(
            self.code,
            None,
            locals
        )
        if self.has_star:
            print(*evaluated, sep=self.print_sep, file=sys.stdout)
        else:
            print(evaluated, sep=self.print_sep, file=sys.stdout)


class NoArgumentException(Exception):
    def __init__(self, argname: str) -> None:
        super().__init__(f"no value for argument {argname}")


class RandomAccessList(list[str]):
    T = TypeVar("T", SupportsIndex, slice, Iterable[Any])

    def __getitem__(self, key: T) -> Any:
        if isinstance(key, Iterable):
            return [self[i] for i in key]
        else:
            return super().__getitem__(key)

class LocalArgs(Mapping[str, object]):
    def __init__(self, args: list[str], imports: dict[str, ModuleType]) -> None:
        super(LocalArgs, self).__init__()
        self.args = args
        self.imports = imports

    def __iter__(self) -> Iterator[str]:
        yield "args"
        yield from [f"arg{i+1}" for i in range(len(self))]
        yield from self.imports

    def __len__(self) -> int:
        return len(self.args) + len(self.imports)

    def __getitem__(self, key: str) -> object:
        if key == "args":
            return self.args
        elif key[:-1] == "arg" and key[-1].isdigit():
            return self.args[int(key[-1]) - 1]
        else:
            return self.imports[key]


def parse_args(line: str, sep: str|None =" ") -> list[str]:
    return RandomAccessList(line.strip().split(sep))


def main():
    imports: dict[str, ModuleType] = {}
    pys = Pys()
    if pys.import_targets is not None:
        for import_target in pys.import_targets:
            if pys.relative_import:
                imports[import_target] = importlib.import_module(import_target)
            else:
                imports.update(importlib.import_module(import_target).__dict__)

    if pys.no_pipe:
        pys.run()
    elif pys.no_split:
        pys.run(LocalArgs(RandomAccessList((''.join(sys.stdin.readlines()), )), imports))
    else:
        for line in sys.stdin:
            pys.run(LocalArgs(parse_args(line, pys.sep), imports))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
