import typing
from pathlib import Path

import pandas as pd


def check_argument(argument):
    valid_types = {
        "direction": str,
        "criterion": typing.Callable,
        "params": pd.DataFrame,
        "algorithm": (str, typing.Callable),
        "criterion_kwargs": dict,
        "constraints": list,
        "algo_options": dict,
        "derivative": (type(None), typing.Callable),
        "derivative_kwargs": dict,
        "criterion_and_derivative": (type(None), typing.Callable),
        "criterion_and_derivative_kwargs": dict,
        "numdiff_options": dict,
        "logging": (bool, Path),
        "log_options": dict,
        "error_handling": str,
        "error_penalty": dict,
        "cache_size": (int, float),
    }

    for arg in argument:
        if not isinstance(argument[arg], valid_types[arg]):
            raise TypeError(
                f"Argument '{arg}' is {argument[arg]} which is not {valid_types[arg]}."
            )

    if argument["direction"] not in ["minimize", "maximize"]:
        raise ValueError("diretion must be 'minimize' or 'maximize'")

    if "value" not in argument["params"].columns:
        raise ValueError("The params DataFrame must contain a 'value' column.")

    if argument["error_handling"] not in ["raise", "continue"]:
        raise ValueError("error_handling must be 'raise' or 'continue'")
