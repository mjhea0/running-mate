from mate import generators
from mate.stats import FeatureStatistics, FeatureType


def test_create_statistics_feature(df):
    for name, feature_series in df.iteritems():
        feature_stats = generators._create_statistics_feature(feature_series)
        assert isinstance(feature_stats, FeatureStatistics)


def test_infer_feature_type(df):
    mapping = {
        "age": FeatureType.INTEGER,
        "sex": FeatureType.STRING,
        "bmi": FeatureType.FRACTION,
        "children": FeatureType.INTEGER,
        "smoker": FeatureType.STRING,
        "region": FeatureType.STRING,
    }

    for name, feature_series in df.iteritems():
        feature_type = generators._infer_feature_type(feature_series)
        assert feature_type == mapping[name]
