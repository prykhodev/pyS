#!/usr/bin/env python3
import sys
from types import ModuleType
from typing import Iterator, Mapping, SupportsIndex, TypeVar, Any


class NoArgumentException(Exception):
    def __init__(self, argname: str) -> None:
        super().__init__(f"no value for argument {argname}")


class RandomAccessList(list):
    T = TypeVar("T", SupportsIndex, slice, tuple)

    def __getitem__(self, key: T) -> Any:
        if isinstance(key, tuple):
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


def parse_args(line: str) -> list[str]:
    return RandomAccessList(line.strip().split(" "))


def main():
    imported_modules = {}
    no_pipe = False
    sep = None
    for arg in (it := iter(sys.argv[:-1])):
        match arg:
            case "-i" | "--import":
                try:
                    argval = next(it)
                    imported_modules[argval] = __import__(argval)
                except StopIteration:
                    raise NoArgumentException(arg)
            case "-n" | "--no-pipe":
                no_pipe = True
            case "-s" | "--sep":
                try:
                    sep = next(it)
                    if sep == "\\n":
                        sep = "\n"
                except StopIteration:
                    raise NoArgumentException(arg)

    def run(args=None) -> None:
        code = sys.argv[-1]
        has_star = code[0] == "*"
        code = code if not has_star else code[1:]
        evaluated = eval(
            code,
            None,
            LocalArgs(args if args is not None else [], imported_modules),
        )
        if has_star:
            print(*evaluated, sep=sep)
        else:
            print(evaluated, sep=sep)

    if not no_pipe:
        for line in sys.stdin.readlines():
            run(parse_args(line))
    else:
        run()


if __name__ == "__main__":
    main()
