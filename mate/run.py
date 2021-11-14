import logging
import traceback
from time import perf_counter
from typing import List, Optional

import pandas as pd  # type: ignore

from mate.alerts import Alert, AlertTarget, FeatureAlertKind, InferenceException
from mate.checks import is_out_of_bounds, is_outlier
from mate.db import (
    Feature,
    FeatureAlert,
    FeatureValue,
    Inference,
    NumericalStats,
    StringStats,
    get_current_mate,
    get_features,
    get_statistics,
)
from mate.stats import FeatureType, Statistics

MATE_STATISTICS_PATH_VAR = "MATE_STATISTICS_PATH"
MATE_CONSTRAINTS_PATH_VAR = "MATE_CONSTRAINTS_PATH"


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
        should_save_all_feature_values: bool = False,
    ):
        self.mate_name = mate_name
        self.mate_version = mate_version
        self.targets = targets
        self.should_save_all_feature_values = should_save_all_feature_values

        self.mate = get_current_mate(self.mate_name)

        if self.mate:
            self.features = get_features(self.mate)
            self.inference = Inference.create(mate=self.mate)

            logger.info("\n")
            logger.info(f"Using mate version {self.mate_version}.")

            if self.should_save_all_feature_values:
                for feature in self.features:
                    col = df[feature.name]
                    FeatureValue.create(
                        value=col.item(),
                        feature=feature,
                        inference=self.inference,
                    )

            self.feature_alerts: List[FeatureAlert] = []
            self.feature_alerts.extend(self._check_statistics(df))
        else:
            logger.info("\n")
            logger.info(f"Mate version {self.mate_version} not found.")

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

        if feature.inferred_type in [
            FeatureType.INTEGER.value,
            FeatureType.FRACTION.value,
        ]:
            numerical_statistic = get_statistics(NumericalStats, feature)

            # outlier check
            if is_outlier(
                float(col.item()), numerical_statistic.mean, numerical_statistic.std_dev
            ):
                feature_value, created = FeatureValue.get_or_create(
                    feature=feature, value=col.item(), inference=self.inference
                )

                result.append(
                    FeatureAlert.create(
                        name=col.name,
                        kind=FeatureAlertKind.OUTLIER.value,
                        feature_value=feature_value,
                        feature=feature,
                    )
                )

            # bound check
            if is_out_of_bounds(
                float(col.item()),
                float(numerical_statistic.min),
                float(numerical_statistic.max),
            ):
                feature_value, created = FeatureValue.get_or_create(
                    feature=feature, value=col.item(), inference=self.inference
                )

                result.append(
                    FeatureAlert.create(
                        name=col.name,
                        kind=FeatureAlertKind.BOUND.value,
                        feature_value=feature_value,
                        feature=feature,
                        inference=self.inference,
                    )
                )

            num_missing = numerical_statistic.num_missing

        if feature.inferred_type == FeatureType.STRING.value:
            string_statistic = get_statistics(StringStats, feature)

            num_missing = string_statistic.num_missing

        # null check
        if num_missing is not None and num_missing == 0:
            if col.isnull().any():
                feature_value, created = FeatureValue.get_or_create(
                    feature=feature, value=col.item(), inference=self.inference
                )

                result.append(
                    FeatureAlert.create(
                        name=col.name,
                        kind=FeatureAlertKind.NULL.value,
                        feature_value=feature_value,
                        feature=feature,
                        inference=self.inference,
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
