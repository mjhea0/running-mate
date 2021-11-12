import logging
import traceback
from time import perf_counter
from typing import List, Optional

import pandas as pd  # type: ignore

from mate.alerts import Alert, AlertTarget, FeatureAlertKind, InferenceException
from mate.db import (
    Feature,
    FeatureAlert,
    NumericalStats,
    StringStats,
    get_current_mate,
    get_features,
    get_statistics,
)
from mate.stats import FeatureType, Statistics

MATE_STATISTICS_PATH_VAR = "MATE_STATISTICS_PATH"
MATE_CONSTRAINTS_PATH_VAR = "MATE_CONSTRAINTS_PATH"
OUTLIER_CUTOFF = 4.0


logger = logging.getLogger("mate")


class RunningMate(object):
    mate_name: str
    statistics: Optional[Statistics]
    feature_alerts: List[FeatureAlert]
    targets: List[AlertTarget]

    def __init__(
        self,
        mate_name: str,
        mate_version: int,
        df: pd.DataFrame,
        targets: List[AlertTarget],
    ):
        self.mate_name = mate_name
        self.mate_version = mate_version
        self.targets = targets

        self.mate = get_current_mate(self.mate_name)

        if self.mate:
            self.features = get_features(self.mate)

        logger.info(f"\nUsing model version {self.mate_version}.")

        self.feature_alerts: List[FeatureAlert] = []
        self.feature_alerts.extend(self._check_statistics(df))

    def _check_statistics(self, df: pd.DataFrame) -> List[FeatureAlert]:
        result = []

        for feature in self.features:
            col = df[feature.name]
            result.extend(self._check_feature_statistics(feature, col))

        logger.info(f"Found {len(result)} statistical alerts.")

        return result

    def _check_feature_statistics(
        self, feature: Feature, col: pd.Series
    ) -> List[FeatureAlert]:
        result: List[FeatureAlert] = []
        num_missing = None

        if feature.inferred_type == FeatureType.INTEGRAL.value:
            numerical_statistic = get_statistics(NumericalStats, feature)

            # outlier check
            if (
                (abs(col - numerical_statistic.mean) / numerical_statistic.std_dev)
                > OUTLIER_CUTOFF
            ).any():
                result.append(
                    FeatureAlert.create(
                        name=col.name,
                        kind=FeatureAlertKind.OUTLIER.value,
                        value=col.item(),
                        feature=feature,
                    )
                )

            # bound check
            if (col < numerical_statistic.min).any() or (
                col > numerical_statistic.max
            ).any():
                result.append(
                    FeatureAlert.create(
                        name=col.name,
                        kind=FeatureAlertKind.BOUND.value,
                        value=col.item(),
                        feature=feature,
                    )
                )

            num_missing = numerical_statistic.num_missing

        if feature.inferred_type == FeatureType.STRING.value:
            string_statistic = get_statistics(StringStats, feature)

            num_missing = string_statistic.num_missing

        # null check
        if num_missing is not None and num_missing == 0:
            if col.isnull().any():
                result.append(
                    FeatureAlert.create(
                        name=col.name,
                        kind=FeatureAlertKind.NULL.value,
                        value=col.item(),
                        feature=feature,
                    )
                )

        return result

    def __enter__(self):
        self.time_start = perf_counter()

    def __exit__(self, type, value, tb):
        time_end = perf_counter()
        logger.info(f"Elapsed inference time in seconds: {time_end - self.time_start}")

        inference_exception = None

        if type is not None:
            logger.exception(f"Exception occurred during model inference: {value}")
            inference_exception = InferenceException(
                message=value,
                traceback="\n".join(traceback.format_exception(type, value, tb)),
            )

        alert = Alert(self.mate_name, self.feature_alerts, inference_exception)

        if len(alert.features) > 0 or alert.exception is not None:
            for target in self.targets:
                target.send_alert(alert)
