import os
import pathlib

import pandas as pd  # type: ignore
import pytest

from mate.db import connect_db, version_or_create_mate
from mate.generators import generate_baseline_stats

BASE = pathlib.Path(__file__).parent.parent.absolute()


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(BASE.joinpath("data/insurance.csv"), sep=",")


@pytest.fixture(scope="module")
def baseline_stats(df):
    os.environ["TESTING"] = "1"
    new_df = df.copy()
    X = new_df.drop(["charges"], axis=1)

    connect_db()
    version_or_create_mate("insurance")

    return generate_baseline_stats(X, "insurance")
