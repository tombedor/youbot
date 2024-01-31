# from memgpt.functions.functions import load_all_function_sets

def debugger(self):
    """Triggers a debugger breakpoint"""
    import pdb; pdb.set_trace()
    

def read_file_lines(file_path: str, start_ln: int, end_ln: int) -> str:
    """ returns the lines of a file from start_ln to end_ln.

    Args:
        file_path (str): Path of the file to read. Line numbers are 1-indexed to match tracebacks
        start_ln (int): index of first line to read
        end_ln (_type_): index of last line to read

    Returns:
        str: _description_
    """
    LINE_LIMIT = 25

    with open(file_path, 'r') as file:
        lines = file.readlines()
        
    if start_ln > len(lines) or end_ln > len(lines):
        raise ValueError(f"Line numbers out of range for file {file_path}. File has only {len(lines)} lines, but start_ln is {start_ln} and end_ln is {end_ln}")        
    
    if start_ln > end_ln:
        raise ValueError(f"start_ln {start_ln} is greater than end_ln {end_ln}")

    if end_ln - start_ln > LINE_LIMIT:
        raise ValueError(f"Line range too large. Must be less than {LINE_LIMIT} lines.")
        
    zero_indexed_start_ln = start_ln - 1
    zero_indexed_end_ln = end_ln - 1
    
    return "".join(lines[zero_indexed_start_ln:zero_indexed_end_ln])

if __name__ == "__main__":
    print(read_file_lines("/Users/tombedor/development/youbot/.venv/lib/python3.10/site-packages/memgpt/persistence_manager.py", 101, 103))


        