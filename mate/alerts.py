import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Dict, List, Optional, Union

import requests  # type: ignore

from mate.db import FeatureAlert

logger = logging.getLogger("mate")


class FeatureAlertKind(Enum):
    OUTLIER = "outlier"  # median absolute deviation is greater than 4.0
    BOUND = "bound"  # outside of lower or upper bounds
    TYPE = "type"  # incorrect data type
    NULL = "null"  # null when feature is non-nullable


@dataclass
class InferenceException:
    message: str
    traceback: str


@dataclass
class Alert:
    mate_name: str
    features: List[FeatureAlert]
    exception: Optional[InferenceException]


@dataclass
class AlertOut:
    mate_name: str
    mate_version: int
    features: List[Dict[str, str]]


class AlertTarget(ABC):
    @abstractmethod
    def _alert_webhook_url(self) -> str:
        pass

    @abstractmethod
    def _format_alert(self, alert: Alert) -> Union[str, Dict]:
        pass

    def send_alert(self, alert: Alert):
        pass


class AlertWebhookTarget(AlertTarget):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def _alert_webhook_url(self) -> str:
        return self.webhook_url

    def _format_alert(self, alert: Alert) -> Dict[str, str]:
        features: List[Dict[str, str]] = []

        for feature_alert in alert.features:
            features.append(
                {
                    "feature_name": feature_alert.name,
                    "feature_alert_kind": feature_alert.kind,
                    "feature_value": feature_alert.feature_value.value,
                }
            )
            mate_version = feature_alert.feature.mate.version

        alert_out = AlertOut(
            mate_name=alert.mate_name, mate_version=mate_version, features=features
        )

        return asdict(alert_out)

    def send_alert(self, alert: Alert):
        if (alert.exception is None) and (len(alert.features) == 0):
            logger.error("Alert has no exception/feature alerts. Not sending")
            return

        formatted_alert = self._format_alert(alert)
        logger.info(formatted_alert)

        resp = requests.post(self._alert_webhook_url(), json=formatted_alert)

        if resp.ok:
            logger.info(f"Sent alert to {type(self).__name__}")
        else:
            logger.error(
                f"Failed to send alert to {type(self).__name__}. "
                + f"Code: {resp.status_code}. Body: {resp.text}"
            )


class TerminalAlertTarget(AlertTarget):
    """
    Output alert to the terminal
    """

    def _alert_webhook_url(self) -> str:
        pass

    def _format_alert(self, alert: Alert) -> Union[str, Dict]:
        alert_message = f"\nFeature Alerts for the '{alert.mate_name}' mate:\n"

        for feature_alert in alert.features:
            feature_message = (
                f"\n    Feature Name: {feature_alert.name}"
                + f"\n    Feature Alert Kind: {feature_alert.kind}"
                + f"\n    Feature Value: {feature_alert.feature_value.value}\n"
            )
            alert_message += feature_message

        return alert_message

    def send_alert(self, alert: Alert):
        print(self._format_alert(alert))


class SlackAlertTarget(AlertWebhookTarget):
    """
    Output alert to a Slack Channel via a Slack Webhook

        Parameters:
            slack_webhook_path (str):
                - Slack Webhook path
                - FORMAT: /XXXXX/XXXXXX/XXXXXXXXXXXXXXXXXXXX)
                - EXAMPLE:
                    Given https://hooks.slack.com/services/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 the
                    slack_webhook_path would be /TG8BB9UKZ/B02LE8DAU5V/KJ1Uyc1ZZcK1pEal44X5GWdL
    """

    def __init__(self, slack_webhook_path: str):
        self.slack_webhook_path = slack_webhook_path

    def _alert_webhook_url(self) -> str:
        return f"https://hooks.slack.com/services{self.slack_webhook_path}"

    def _format_alert(self, alert: Alert) -> Dict[str, str]:
        features: List[Dict[str, str]] = []

        for feature_alert in alert.features:
            features.append(
                {
                    "feature_name": feature_alert.name,
                    "feature_alert_kind": feature_alert.kind,
                    "feature_value": feature_alert.feature_value.value,
                }
            )
            mate_version = feature_alert.feature.mate.version

        alert_out = AlertOut(
            mate_name=alert.mate_name, mate_version=mate_version, features=features
        )

        return {"text": json.dumps(asdict(alert_out))}
