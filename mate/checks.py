def is_out_of_bounds(
    feature_value: float, lower_bound: float, upper_bound: float
) -> bool:
    """
    Checks if the feature_value is outside of the lower or upper bounds.
    """

    return (feature_value < lower_bound) or (feature_value > upper_bound)


def is_outlier(
    feature_value: float, mean: float, std_dev: float, outlier_cutoff: float = 4.0
) -> bool:
    """
    Checks if the Median Absolute Deviation (MAD) is greater than the outlier_cutoff (defaults to 4.0).
    """

    return (abs(feature_value - mean) / std_dev) > outlier_cutoff
