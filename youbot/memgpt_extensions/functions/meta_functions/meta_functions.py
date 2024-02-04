import os
import inspect
from dotenv import load_dotenv
from memgpt.constants import MEMGPT_DIR
from memgpt.functions.functions import load_all_function_sets

FUNCTIONS_DIR = os.path.join(MEMGPT_DIR, "functions")
AGENT_CREATED_PREFIX = "agent_created_"

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
        
    return f"added function {function_name} to file {file_path}"


from sqlalchemy import MetaData, NullPool, Table
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

load_dotenv()
POSTGRES_URL = os.getenv("POSTGRES_URL")

engine = create_engine(POSTGRES_URL, poolclass=NullPool)

declarative_base().metadata.create_all(engine)
session_maker = sessionmaker(bind=engine)

def get_table_schema(self, table_name: str) -> str:
    """Fetches the schema of a table in the database and returns it as a string

    Args:
        table_name (str): The name of the table.

    Returns:
        str: The schema of the table.
    """
    with session_maker() as session:
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=session.bind)
    
        schema_string = ""
    
        for column in table.columns:
            schema_string += f"{column.name} {column.type}\n"

        return schema_string.strip()
