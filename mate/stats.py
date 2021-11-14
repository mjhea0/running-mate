from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class FeatureType(Enum):
    FRACTION = "fraction"
    INTEGER = "integer"
    STRING = "string"
    UNKNOWN = "unknown"


@dataclass
class CommonStatistics:
    num_present: int
    num_missing: int


@dataclass
class NumericalStatistics:
    common: CommonStatistics
    mean: float
    sum: float
    std_dev: float
    min: float
    max: float


@dataclass
class StringStatistics:
    common: CommonStatistics
    distinct_count: int


@dataclass
class FeatureStatistics:
    name: str
    inferred_type: str
    numerical_statistics: Optional[NumericalStatistics] = None
    string_statistics: Optional[StringStatistics] = None


@dataclass
class Statistics:
    item_count: int
    version: int = 0
    features: List[FeatureStatistics] = field(default_factory=list)
