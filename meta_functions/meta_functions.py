import os
import inspect
from pathlib import Path
import sys
from memgpt.constants import MEMGPT_DIR

FUNCTIONS_DIR = os.path.join(MEMGPT_DIR, "functions")
AGENT_CREATED_PREFIX = "agent_created_"

def debugger(self):
    """Triggers a debugger breakpoint"""
    import pdb; pdb.set_trace()


def list_functions(self) -> str:
    """Returns a list of functions that are available to the agent

    Returns:
        str: The list of functions
    """
    return ", ".join(self.functions_python.keys())


def reload_functions(self):
    """Triggers a reload of functions"""
    return self.reload_functions()


def introspect_functions(self, function_name: str) -> str:
    """Returns the source code an agent-available function

    Args:
        function_name (str): name of the function

    Returns:
        str: source code of the function.
    """
    func = self.functions_python[function_name]
    return inspect.getsource(func)

import ast
import astunparse

def delete_function(self, function_name: str) -> str:
    """Deletes the listed function. function MUST be in the functions folder

    Args:
        function_name (str): name of the function to delete

    Raises:
        Exception: occurs when the function does not exist or is not in the functions folder

    Returns:
        str: description of result.
    """
    if function_name not in self.functions_python.keys():
        raise Exception(f"Function {function_name} does not exist. To create it, use function `create_function`.")

    file_path = inspect.getfile(self.functions_python[function_name])

    with open(file_path, "r") as f:
        previous_module_source = ast.parse(f.read())

    function_nodes = [node for node in ast.walk(previous_module_source) if isinstance(node, ast.FunctionDef) and
node.name == function_name]

    if not function_nodes:
        raise Exception(f"Function {function_name} was not found in its source file.")

    previous_module_source.body.remove(function_nodes[0])

    new_source = astunparse.unparse(previous_module_source)

    with open(file_path, "w") as f:
        f.write(new_source)
        
    self.reload_functions()

    return f"Deleted function {function_name} from file {file_path}."


def create_function(self, function_name: str, function_code_with_docstring: str, module_name: str) -> str:
    """Creates an agent accessible function in Python. Function MUST include a docstring, and MUST include self as first argument.

    Args:
        function_name (str): The name of the function
        function_code_with_docstring (str): The code of the function, including the docstring
        module_name (str): The name of the module to create the function in

    Raises:
        Exception: Exception if the function already exists
        Exception: Exception if the function does not start with def function_name(self, ...
        Exception: Exception if the function does not include a docstring.
        Exception: Exception if the function is not in the functions directory.

    Returns:
        str: The result of the function creation attempt.
    """
    """
    
    # setup
    if not os.path.exists(FUNCTIONS_DIR):
        os.makedirs(FUNCTIONS_DIR)
    """
    
    # setup
    if not os.path.exists(FUNCTIONS_DIR):
        os.makedirs(FUNCTIONS_DIR)
        
    # Make sure that if the function is already defined, overwrite = true and it is an agent defined function
    if function_name in self.functions_python.keys():
        raise Exception(f"Function {function_name} already exists. To overwrite, first delete with the delete_function function.")
        

    if not function_code_with_docstring.split("\n")[0].strip().startswith('def ' + function_name + '(self'):
        raise Exception("Function must start with def " + function_name + "(self, ...")
    
    if '"""' not in function_code_with_docstring and "'''" not in function_code_with_docstring:
        raise Exception("Function code must have a docstring.")
    
    file_path = os.path.join(FUNCTIONS_DIR, module_name + ".py")    
    
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            previous_source = f.read()
    else:
        previous_source = ""

    # write new module:
    with open(os.path.join(file_path), "w") as f:
        f.write(previous_source + "\n\n" + function_code_with_docstring)
        
    self.reload_functions()
    return f"added function {function_name} to file {file_path}"

