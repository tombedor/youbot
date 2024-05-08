# def create_function(self, function_name: str, function_code_with_docstring: str, module_name: str) -> str:
#     """Creates an agent accessible function in Python. Function MUST include a docstring, and MUST include self as first argument.

#     Args:
#         function_name (str): The name of the function
#         function_code_with_docstring (str): The code of the function, including the docstring
#         module_name (str): The name of the module to create the function in

#     Raises:
#         Exception: Exception if the function already exists
#         Exception: Exception if the function does not start with def function_name(self, ...
#         Exception: Exception if the function does not include a docstring.
#         Exception: Exception if the function is not in the functions directory.

#     Returns:
#         str: The result of the function creation attempt.
#     """
#     """
    
#     # setup
#     if not os.path.exists(FUNCTIONS_DIR):
#         os.makedirs(FUNCTIONS_DIR)
#     """

#     # setup
#     if not os.path.exists(FUNCTIONS_DIR):
#         os.makedirs(FUNCTIONS_DIR)

#     # Make sure that if the function is already defined, overwrite = true and it is an agent defined function
#     if function_name in self.functions_python.keys():
#         raise Exception(f"Function {function_name} already exists. To overwrite, first delete with the delete_function function.")

#     if not function_code_with_docstring.split("\n")[0].strip().startswith("def " + function_name + "(self"):
#         raise Exception("Function must start with def " + function_name + "(self, ...")

#     if '"""' not in function_code_with_docstring and "'''" not in function_code_with_docstring:
#         raise Exception("Function code must have a docstring.")

#     file_path = os.path.join(FUNCTIONS_DIR, module_name + ".py")

#     if os.path.exists(file_path):
#         with open(file_path, "r") as f:
#             previous_source = f.read()
#     else:
#         previous_source = ""

#     # write new module:
#     with open(os.path.join(file_path), "w") as f:
#         f.write(previous_source + "\n\n" + function_code_with_docstring)
