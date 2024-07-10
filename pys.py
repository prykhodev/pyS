#!/usr/bin/env python3
import sys
from types import ModuleType
from typing import Iterable, Iterator, Mapping, SupportsIndex, TypeVar, Any
import importlib


class NoArgumentException(Exception):
    def __init__(self, argname: str) -> None:
        super().__init__(f"no value for argument {argname}")


class RandomAccessList(list[str]):
    T = TypeVar("T", SupportsIndex, slice, Iterable)

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
    import_targets = []
    imports = {}
    no_pipe = False
    relative_import = False
    sep = None
    print_sep = None
    for arg in (it := iter(sys.argv[:-1])):
        match arg:
            case "-i" | "--import":
                try:
                    argval = next(it)
                    import_targets.append(argval)
                except StopIteration:
                    raise NoArgumentException(arg)
            case "-n" | "--no-pipe":
                no_pipe = True
            case "--relative-import":
                relative_import = True
            case "-s" | "--sep":
                try:
                    sep = next(it)
                except StopIteration:
                    raise NoArgumentException(arg)
            case "-p" | "--print-sep":
                try:
                    print_sep = next(it)
                    if print_sep == "\\n":
                        print_sep = "\n"
                except StopIteration:
                    raise NoArgumentException(arg)

    for import_target in import_targets:
        if relative_import:
            imports[import_target] = importlib.import_module(import_target)
        else:
            imports.update(importlib.import_module(import_target).__dict__)


    def run(args=None) -> None:
        code = sys.argv[-1]
        has_star = code[0] == "*"
        code = code if not has_star else code[1:]
        evaluated = eval(
            code,
            None,
            LocalArgs(args if args is not None else [], imports),
        )
        if has_star:
            print(*evaluated, sep=print_sep)
        else:
            print(evaluated, sep=print_sep)

    if not no_pipe:
        for line in sys.stdin.readlines():
            run(parse_args(line, sep))
    else:
        run()


if __name__ == "__main__":
    main()
