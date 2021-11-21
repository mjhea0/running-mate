import os

from mate.reports import generate_feature_stats_summary_report


def test_generate_feature_stats_summary_report(baseline_stats):
    os.environ["TESTING"] = "1"

    assert type(generate_feature_stats_summary_report("insurance")) == str
