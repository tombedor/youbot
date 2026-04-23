from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

MODULE_LINE_LIMIT = 350
FUNCTION_LINE_LIMIT = 80
ROOTS = (Path("youbot"), Path("tests"))

MODULE_ALLOWLIST: set[str] = set()
FUNCTION_ALLOWLIST: set[tuple[str, str]] = set()


@dataclass(frozen=True)
class Violation:
    path: str
    label: str
    size: int
    limit: int
    location: str


class FunctionCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self._stack: list[str] = []
        self.violations: list[Violation] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._record_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._record_function(node)

    def _record_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        qualname = ".".join([*self._stack, node.name]) if self._stack else node.name
        end = node.end_lineno if node.end_lineno is not None else node.lineno
        size = end - node.lineno + 1
        self.violations.append(
            Violation(
                path="",
                label=qualname,
                size=size,
                limit=FUNCTION_LINE_LIMIT,
                location=f"{node.lineno}-{node.end_lineno}",
            )
        )
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for root in ROOTS:
        if root.exists():
            files.extend(sorted(root.rglob("*.py")))
    return files


def _check_module(path: Path) -> Violation | None:
    line_count = len(path.read_text().splitlines())
    relative_path = path.as_posix()
    if line_count <= MODULE_LINE_LIMIT or relative_path in MODULE_ALLOWLIST:
        return None
    return Violation(
        path=relative_path,
        label="module",
        size=line_count,
        limit=MODULE_LINE_LIMIT,
        location="1",
    )


def _check_functions(path: Path) -> list[Violation]:
    relative_path = path.as_posix()
    tree = ast.parse(path.read_text(), filename=relative_path)
    collector = FunctionCollector()
    collector.visit(tree)
    violations: list[Violation] = []
    for violation in collector.violations:
        keyed_violation = (relative_path, violation.label)
        if violation.size <= FUNCTION_LINE_LIMIT or keyed_violation in FUNCTION_ALLOWLIST:
            continue
        violations.append(
            Violation(
                path=relative_path,
                label=violation.label,
                size=violation.size,
                limit=FUNCTION_LINE_LIMIT,
                location=violation.location,
            )
        )
    return violations


def main() -> int:
    violations: list[Violation] = []
    for path in _iter_python_files():
        module_violation = _check_module(path)
        if module_violation is not None:
            violations.append(module_violation)
        violations.extend(_check_functions(path))

    if not violations:
        print("Size checks passed.")
        return 0

    print("Size check failures:")
    for violation in violations:
        print(
            f"- {violation.path}:{violation.location}: {violation.label} "
            f"has {violation.size} lines (limit {violation.limit})"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
