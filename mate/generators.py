import pandas as pd  # type: ignore

from mate.db import Feature, NumericalStats, StringStats, get_current_mate
from mate.stats import (
    CommonStatistics,
    FeatureStatistics,
    FeatureType,
    NumericalStatistics,
    Statistics,
    StringStatistics,
)


def generate_baseline_stats(df: pd.DataFrame, name: str):
    statistics = _gen_statistics(df)

    mate = get_current_mate(name)
    if mate:
        mate.item_count = statistics.item_count
        mate.save()

    for feature in statistics.features:
        feature_stats = Feature(
            name=feature.name, inferred_type=feature.inferred_type, mate=mate
        )
        feature_stats.save()

        if feature.numerical_statistics:
            NumericalStats.create(
                num_present=feature.numerical_statistics.common.num_present,
                num_missing=feature.numerical_statistics.common.num_missing,
                mean=feature.numerical_statistics.mean,
                sum=feature.numerical_statistics.sum,
                std_dev=feature.numerical_statistics.std_dev,
                min=feature.numerical_statistics.min,
                max=feature.numerical_statistics.max,
                feature=feature_stats,
            )

        if feature.string_statistics:
            StringStats.create(
                num_present=feature.string_statistics.common.num_present,
                num_missing=feature.string_statistics.common.num_missing,
                distinct_count=feature.string_statistics.distinct_count,
                feature=feature_stats,
            )


def _create_statistics_feature(feature_series: pd.Series) -> FeatureStatistics:
    feature_name = feature_series.name
    feature_type = _infer_feature_type(feature_series)

    feature = FeatureStatistics(name=feature_name, inferred_type=feature_type.value)

    n_missing = feature_series.isna().sum()
    n_present = len(feature_series) - n_missing

    common = CommonStatistics(n_present, n_missing)

    if feature_type in [FeatureType.INTEGER, FeatureType.FRACTION]:
        feature.numerical_statistics = NumericalStatistics(
            common=common,
            mean=feature_series.mean(),
            sum=feature_series.sum(),
            std_dev=feature_series.std(),
            min=feature_series.min(),
            max=feature_series.max(),
        )

    elif feature_type == FeatureType.STRING:
        feature.string_statistics = StringStatistics(
            common=common, distinct_count=len(feature_series.dropna().unique())
        )

    return feature


def _gen_statistics(df: pd.DataFrame) -> Statistics:
    statistics = Statistics(
        item_count=len(df),
        features=[
            _create_statistics_feature(feature_series)
            for name, feature_series in df.iteritems()
        ],
    )
    return statistics


def _infer_feature_type(feature_series: pd.Series) -> FeatureType:
    dtype_name = str(feature_series.dtype)

    # {"int8", "int16", "int32", "int64", "intp"}
    # {"uint8", "uint16", "uint32", "uint64", "uintp"}
    if dtype_name.startswith("int") or dtype_name.startswith("uint"):
        feature_type = FeatureType.INTEGER

    # {"float16", "float32", "float64", "float96", "float128"}:
    elif dtype_name.startswith("float"):
        feature_type = FeatureType.FRACTION

    # {"string", "<U16/32/...", ">U16/32/...", "=U16/32/..."}
    elif (dtype_name == "string") or (dtype_name[:2] in {"<U", ">U", "=U"}):
        feature_type = FeatureType.STRING

    elif dtype_name == "object":
        feature_type = FeatureType.UNKNOWN

        # attempt to infer if object dtype is actually a string
        types = set(map(type, feature_series.dropna()))
        if types == {str}:
            feature_type = FeatureType.STRING

    else:
        # Bools, datetimes, etc are all treated as unknown
        feature_type = FeatureType.UNKNOWN

    return feature_type
