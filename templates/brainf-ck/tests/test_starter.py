"""Exercise the starter through the exact Catalog-owned interpreter asset."""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from pathlib import Path
import sys


def main() -> int:
    interpreter_path = Path(sys.argv[1])
    source_path = Path(sys.argv[2])
    loader = SourceFileLoader(
        "catalog_brainf_ck_interpreter", str(interpreter_path)
    )
    specification = spec_from_loader(loader.name, loader)
    if specification is None or specification.loader is None:
        raise RuntimeError("Catalog-owned interpreter cannot be loaded")
    interpreter = module_from_spec(specification)
    specification.loader.exec_module(interpreter)
    program = interpreter.compile_program(source_path.read_text(encoding="ascii"))

    for seeded_move in b"RPS":
        encoded_turn = bytes((seeded_move, ord("R"), ord("R"))) + bytes(20)
        first = interpreter.execute(program, encoded_turn)
        second = interpreter.execute(program, encoded_turn)
        if first != bytes((seeded_move,)) or second != first:
            raise AssertionError("starter did not return its deterministic seeded move")
    print("Brainf-ck starter tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
