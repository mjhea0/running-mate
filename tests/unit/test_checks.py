import pytest

from mate.checks import is_out_of_bounds, is_outlier


@pytest.mark.parametrize(
    "feature_value, mean, std_dev, expected",
    [
        (31.0, 39.20702541106129, 14.049960379216154, False),
        (2.0, 1.0949177877429, 1.205492739781914, False),
        (96.0, 39.20702541106129, 14.049960379216154, True),
    ],
)
def test_is_outlier(feature_value, mean, std_dev, expected):
    assert is_outlier(feature_value, mean, std_dev) == expected


@pytest.mark.parametrize(
    "feature_value, lower_bound, upper_bound, expected",
    [
        (31.0, 18.0, 64.0, False),
        (2.0, 0.0, 5.0, False),
        (-1.0, 18.0, 64.0, True),
        (2.0, 0.0, 5.0, False),
    ],
)
def test_is_out_of_bounds(feature_value, lower_bound, upper_bound, expected):
    assert is_out_of_bounds(feature_value, lower_bound, upper_bound) == expected
