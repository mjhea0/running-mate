import functools
import operator

from mate.db import Feature, Mate, NumericalStats, StringStats


def generate_feature_stats_summary_report(name: str, version: int = None) -> str:
    clauses = [(Mate.name == name)]
    if version:
        clauses.append((Mate.version == 1))

    mate = (
        Mate.select()
        .where(functools.reduce(operator.and_, clauses))
        .order_by(Mate.version.desc())
        .limit(1)
        .prefetch(Feature, NumericalStats, StringStats)
    )[0]

    output_message = f"\nSummary Stats for version '{mate.__data__['version']}' of the '{mate.__data__['name']}' mate:\n"

    for feature in mate.feature_set:
        feature_message = (
            f"\n    Feature Name: {feature.name}"
            + f"\n    Feature ID: {feature.id}"
            + f"\n    Feature Inferred Type: {feature.inferred_type}\n"
        )

        if feature.stringstats_set:
            for string_stat in feature.stringstats_set:
                string_stat_message = (
                    f"\n        String Stat ID: {string_stat.id}"
                    + f"\n        Num Present: {string_stat.num_present}"
                    + f"\n        Num Missing: {string_stat.num_missing}"
                    + f"\n        Distinct Count: {string_stat.distinct_count}\n"
                )
                feature_message += string_stat_message

        if feature.numericalstats_set:
            for numerical_stat in feature.numericalstats_set:
                numerical_stat_message = (
                    f"\n        Numerical Stat ID: {numerical_stat.id}"
                    + f"\n        Num Present: {numerical_stat.num_present}"
                    + f"\n        Num Missing: {numerical_stat.num_missing}"
                    + f"\n        Mean: {numerical_stat.mean}"
                    + f"\n        Sum: {numerical_stat.sum}"
                    + f"\n        Std Dev: {numerical_stat.std_dev}"
                    + f"\n        Min: {numerical_stat.min}"
                    + f"\n        Max: {numerical_stat.max}\n"
                )
                feature_message += numerical_stat_message

        output_message += feature_message

    return output_message
