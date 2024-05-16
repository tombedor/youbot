import inspect
from memgpt.functions.functions import load_all_function_sets


def reload_functions(self):
    """Refreshes implementations of user provided functions"""
    functions = load_all_function_sets()

    for function_name in self.functions_python.keys():
        self.functions_python[function_name] = functions[function_name]["python_function"]


def list_functions(self) -> str:
    """Returns a list of functions that are available to the agent

    Returns:
        str: The list of functions
    """
    return ", ".join(self.functions_python.keys())


def list_all_possible_functions(self) -> str:
    """Returns a list of all functions that could be added to the agent.

    Returns:
        str: The list of all functions.

    """

    return ", ".join(load_all_function_sets().keys())


def add_function(self, function_name: str) -> str:
    """Adds specified function to agent state.

    Args:
        function_name (str): name of the function to add

    Raises:
        Exception: occurs when the function does not exist or is not in the functions folder

    Returns:
        str: description of result.
    """
    return self.add_function(function_name)


def introspect_functions(self, function_name: str) -> str:
    """Returns the source code an agent-available function

    Args:
        function_name (str): name of the function

    Returns:
        str: source code of the function.
    """
    func = self.functions_python[function_name]
    return inspect.getsource(func)


def remove_function(self, function_name: str) -> str:
    """Removes the listed function from the agent. Function must be a user defined function.

    Args:
        function_name (str): name of the function to remove

    Raises:
        Exception: occurs when the function does not exist or is not in the functions folder

    Returns:
        str: description of result.
    """

    return self.remove_function(function_name)
