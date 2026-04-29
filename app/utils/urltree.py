from __future__ import annotations


class UrlTreeUtils:
    @staticmethod
    def structure2dict(structure: str) -> dict:
        root: dict = {}
        stack: list[tuple[int, dict]] = [(-1, root)]

        for raw_line in structure.splitlines():
            if not raw_line.strip():
                continue

            indent = len(raw_line) - len(raw_line.lstrip(" "))
            line = raw_line.strip()
            parts = line.split(" | ")
            name = parts[0]

            while stack and indent <= stack[-1][0]:
                stack.pop()
            parent = stack[-1][1]

            if len(parts) >= 4:
                parent[name] = [parts[1], parts[2], " | ".join(parts[3:])]
            else:
                current: dict = {}
                parent[name] = current
                stack.append((indent, current))

        return root

    @classmethod
    def dict2structure(cls, data: dict) -> str:
        lines: list[str] = []
        cls._append_lines(data, lines, 0)
        return "\n".join(lines)

    @classmethod
    def _append_lines(cls, data: dict, lines: list[str], depth: int) -> None:
        indent = "  " * depth
        for name in sorted(data):
            value = data[name]
            if isinstance(value, dict):
                lines.append(f"{indent}{name}")
                cls._append_lines(value, lines, depth + 1)
            elif isinstance(value, (list, tuple)) and len(value) >= 3:
                lines.append(f"{indent}{name} | {value[0]} | {value[1]} | {value[2]}")

