# from memgpt.functions.functions import load_all_function_sets
# pylint: disable=forgotten-debug-statement
def debugger(self):
    """Triggers a debugger breakpoint"""
    import pdb

    pdb.set_trace()


def read_file_lines(file_path: str, start_ln: int, end_ln: int) -> str:
    """returns the lines of a file from start_ln to end_ln.

    Args:
        file_path (str): Path of the file to read. Line numbers are 1-indexed to match tracebacks
        start_ln (int): index of first line to read
        end_ln (_type_): index of last line to read

    Returns:
        str: _description_
    """
    LINE_LIMIT = 25

    with open(file_path, "r") as file:
        lines = file.readlines()

    if start_ln > len(lines) or end_ln > len(lines):
        raise ValueError(
            f"Line numbers out of range for file {file_path}. File has only {len(lines)} lines, but start_ln is {start_ln} and end_ln is {end_ln}"
        )

    if start_ln > end_ln:
        raise ValueError(f"start_ln {start_ln} is greater than end_ln {end_ln}")

    if end_ln - start_ln > LINE_LIMIT:
        raise ValueError(f"Line range too large. Must be less than {LINE_LIMIT} lines.")

    zero_indexed_start_ln = start_ln - 1
    zero_indexed_end_ln = end_ln - 1

    return "".join(lines[zero_indexed_start_ln:zero_indexed_end_ln])


import os

import os

import os


def find_text(self, root_dir: str, target_text: str) -> str:
    """Finds text matches for string within a directory

    Args:
        root_dir (str): root dir to search
        target_text (str): text to search for

    Returns:
        str: matches
    """
    results = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            filename = os.path.join(root, file)
            if not filename.endswith(".py"):
                continue
            with open(filename, "r") as f:
                prev_line = ""
                for line_no, line in enumerate(f, 1):
                    next_line = f.readline()
                    if target_text in line:
                        results.append(
                            f"{filename}:{line_no}:\n{prev_line + line + next_line}"
                        )
                    prev_line = line

            if len(results) > 5:
                results.append(f"{len(results)} results found. Stopping search.")
                break
    return "---\n".join(results)


# def find_usage(root_dir, target_fn):
#     files_with_usage = set()
#     class FuncFinder(ast.NodeVisitor):
#         def visit_Call(self, node):
#             if isinstance(node.func, ast.Name) and node.func.id == target_fn:
#                 files_with_usage.add(filename)

#     for root, dirs, files in os.walk(root_dir):
#         for file in files:
#             if file.endswith('.py'):
#                 filename = os.path.join(root, file)
#                 with open(filename, 'r') as f:
#                     data = f.read()
#                 tree = ast.parse(data)
#                 FuncFinder().visit(tree)
#     return list(files_with_usage)
