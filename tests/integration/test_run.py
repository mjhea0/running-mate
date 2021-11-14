import os
import pathlib

import pandas as pd  # type: ignore

from mate.db import Inference, Mate
from mate.run import RunningMate

BASE = pathlib.Path(__file__).parent.parent.absolute()


def test_running_mate_no_alerts(baseline_stats):
    os.environ["TESTING"] = "1"

    assert Mate.select().count() == 1

    alert_targets = []
    df = pd.read_csv(BASE.joinpath("data/insurance_infer.csv"), sep=",")

    test_mate = RunningMate(
        "insurance", 1, df, alert_targets, should_save_all_feature_values=True
    )

    assert Inference.select().count() == 1
    assert test_mate.mate_name == "insurance"
    assert test_mate.should_save_all_feature_values
    assert len(test_mate._check_statistics(df)) == 0


def test_running_mate_with_alerts(baseline_stats):
    os.environ["TESTING"] = "1"

    assert Mate.select().count() == 1

    alert_targets = []
    df = pd.read_csv(BASE.joinpath("data/insurance_infer.csv"), sep=",")
    df["age"] = -1

    test_mate = RunningMate(
        "insurance", 1, df, alert_targets, should_save_all_feature_values=True
    )

    assert Inference.select().count() == 2
    assert test_mate.mate_name == "insurance"
    assert test_mate.should_save_all_feature_values
    assert len(test_mate._check_statistics(df)) == 1
