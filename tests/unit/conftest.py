import pathlib

import pandas as pd  # type: ignore
import pytest

BASE = pathlib.Path(__file__).parent.parent.absolute()


@pytest.fixture(scope="module")
def df():
    df = pd.read_csv(BASE.joinpath("data/insurance.csv"), sep=",")
    return df.drop(["charges"], axis=1)
