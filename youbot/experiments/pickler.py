import pandas as pd
import os
import pickle

def pickled_cache(func):
    def wrapper(*args, **kwargs):
        # Get the function name
        function_name = func.__name__

        # Check if a pickle file exists for the function
        pickle_file = f"{function_name}.pickle"
        if os.path.exists(pickle_file):
            # Load and return the DataFrame from the pickle file
            with open(pickle_file, "rb") as file:
                return pickle.load(file)
        else:
            # Run the function
            result = func(*args, **kwargs)

            # Write the result to the pickle file
            with open(pickle_file, "wb") as file:
                pickle.dump(result, file)

            # Return the result
            return result

    return wrapper

@pickled_cache
def foo():
    data = {"A": [1, 2, 3], "B": [4, 5, 6]}
    return pd.DataFrame(data)