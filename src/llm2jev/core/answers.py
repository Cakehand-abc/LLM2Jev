from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar, TypeAlias

from ..utils.json import is_json_content
from ..utils.probability import copy_probability_distribution, validate_probability
from .types import JSONContent


@dataclass(frozen=True, slots=True, kw_only=True)
class ChoiceAnswer:
    """A selected choice and the probability distribution of available choices.

    Attributes:
        choice: The selected candidate choice with the highest probability.
        confidence: The confidence score of the winning choice.
        probabilities: Mapping of candidate choice names to normalized probabilities
            (sum-of-yes normalized across all evaluated candidate criteria).
        raw_probabilities: Optional mapping of candidate choice names to unnormalized
            binary yes-probabilities P(yes | candidate). Preserving these raw binary
            scores protects downstream systems (e.g. hierarchical routers, safety
            guardrails, confidence calibrators) against denominator dilution when
            multiple orthogonal or co-occurring criteria score highly simultaneously.
    """

    choice: str
    confidence: float
    probabilities: Mapping[str, float]
    raw_probabilities: Mapping[str, float] | None = None

    type: ClassVar[str] = "choice"

    def __post_init__(self) -> None:
        if not isinstance(self.choice, str) or not self.choice:
            raise ValueError("choice must be a non-empty string")
        validate_probability(self.confidence, "confidence")
        probabilities = copy_probability_distribution(self.probabilities)
        if any(not isinstance(name, str) or not name for name in probabilities):
            raise ValueError("probability keys must be non-empty strings")
        if self.choice not in probabilities:
            raise ValueError("choice must be present in probabilities")
        if not math.isclose(probabilities[self.choice], max(probabilities.values()), abs_tol=1e-12):
            raise ValueError("choice must have the highest probability")
        object.__setattr__(self, "probabilities", probabilities)

        if self.raw_probabilities is not None:
            raw_probabilities = dict(self.raw_probabilities)
            # Validate key types: choice keys must always be non-empty strings
            if any(not isinstance(name, str) or not name for name in raw_probabilities):
                raise ValueError("raw_probability keys must be non-empty strings")
            # Defensive integrity check: raw_probabilities must exactly mirror choice candidates
            if set(raw_probabilities) != set(probabilities):
                raise ValueError("raw_probabilities and probabilities must contain the same choices")
            # Ensure each unnormalized score is a valid finite probability in [0.0, 1.0]
            for prob in raw_probabilities.values():
                validate_probability(prob, "raw_probability")
            object.__setattr__(self, "raw_probabilities", raw_probabilities)

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "type": self.type,
            "choice": self.choice,
            "confidence": self.confidence,
            "probabilities": dict(self.probabilities),
        }
        if self.raw_probabilities is not None:
            data["raw_probabilities"] = dict(self.raw_probabilities)
        return data


@dataclass(frozen=True, slots=True, kw_only=True)
class ScoreAnswer:
    """A probability-weighted score and its ordered rubric distribution.

    Attributes:
        score: The expected value (probability-weighted average) across rubric levels.
        confidence: The confidence score of the predicted distribution.
        legend: Mapping of integer levels to their descriptive rubric criteria.
        probabilities: Mapping of integer levels to normalized probabilities
            (sum-of-yes normalized across all rubric levels).
        raw_probabilities: Optional mapping of integer levels to unnormalized
            binary yes-probabilities P(yes | level). Retaining raw binary scores
            allows downstream calibration, multi-level gating, and anomaly detection
            without distortion from relative normalizations.
    """

    score: float
    confidence: float
    legend: Mapping[int, JSONContent]
    probabilities: Mapping[int, float]
    raw_probabilities: Mapping[int, float] | None = None

    type: ClassVar[str] = "score"

    def __post_init__(self) -> None:
        if isinstance(self.score, bool) or not isinstance(self.score, (int, float)) or not math.isfinite(self.score):
            raise ValueError("score must be a finite number")
        validate_probability(self.confidence, "confidence")

        legend = dict(self.legend)
        if not legend:
            raise ValueError("legend must not be empty")
        if any(isinstance(level, bool) or not isinstance(level, int) or level < 0 for level in legend):
            raise ValueError("legend keys must be non-negative integers")
        if set(legend) != set(range(len(legend))):
            raise ValueError("legend levels must be contiguous and start at 0")
        if any(not is_json_content(description) for description in legend.values()):
            raise ValueError("legend descriptions must be JSON content")

        probabilities = copy_probability_distribution(self.probabilities)
        if any(isinstance(level, bool) or not isinstance(level, int) for level in probabilities):
            raise ValueError("score probability keys must be integers")
        if set(probabilities) != set(legend):
            raise ValueError("legend and probabilities must contain the same levels")

        expected_score = math.fsum(level * probability for level, probability in probabilities.items())
        if not math.isclose(self.score, expected_score, abs_tol=1e-6):
            raise ValueError("score must equal the probability-weighted average of its levels")

        object.__setattr__(self, "legend", legend)
        object.__setattr__(self, "probabilities", probabilities)

        if self.raw_probabilities is not None:
            raw_probabilities = dict(self.raw_probabilities)
            # Level keys must be exact integers (explicitly rejecting booleans)
            if any(isinstance(level, bool) or not isinstance(level, int) for level in raw_probabilities):
                raise ValueError("raw_probability keys must be integers")
            # Defensive integrity check: raw_probabilities must exactly mirror rubric levels
            if set(raw_probabilities) != set(legend):
                raise ValueError("legend and raw_probabilities must contain the same levels")
            # Ensure each unnormalized score is a valid finite probability in [0.0, 1.0]
            for prob in raw_probabilities.values():
                validate_probability(prob, "raw_probability")
            object.__setattr__(self, "raw_probabilities", raw_probabilities)

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "type": self.type,
            "score": self.score,
            "confidence": self.confidence,
            "legend": {str(level): description for level, description in self.legend.items()},
            "probabilities": {str(level): probability for level, probability in self.probabilities.items()},
        }
        if self.raw_probabilities is not None:
            data["raw_probabilities"] = {str(level): prob for level, prob in self.raw_probabilities.items()}
        return data


@dataclass(frozen=True, slots=True, kw_only=True)
class NoulAnswer:
    """The probability that the answer is yes or the statement is true."""

    noul: float

    type: ClassVar[str] = "noul"

    def __post_init__(self) -> None:
        validate_probability(self.noul, "noul")

    def to_dict(self) -> dict[str, object]:
        return {"type": self.type, "noul": self.noul}


Answer: TypeAlias = ChoiceAnswer | ScoreAnswer | NoulAnswer
