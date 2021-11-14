import os

from mate.db import (
    Feature,
    Mate,
    NumericalStats,
    StringStats,
    connect_db,
    version_or_create_mate,
)
from mate.generators import generate_baseline_stats


def test_generate_baseline_stats(df):
    os.environ["TESTING"] = "1"
    connect_db()

    assert Mate.select().count() == 0
    assert Feature.select().count() == 0
    assert NumericalStats.select().count() == 0
    assert StringStats.select().count() == 0

    new_df = df.copy()
    X = new_df.drop(["charges"], axis=1)

    version_or_create_mate("insurance")
    assert Mate.select().count() == 1

    generate_baseline_stats(X, "insurance")
    assert Feature.select().count() == 6
    assert NumericalStats.select().count() == 3
    assert StringStats.select().count() == 3

    # create new version
    version_or_create_mate("insurance")
    assert Mate.select().count() == 2

    generate_baseline_stats(X, "insurance")
    assert Feature.select().count() == 12
    assert NumericalStats.select().count() == 6
    assert StringStats.select().count() == 6
