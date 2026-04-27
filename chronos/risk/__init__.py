"""
Predictive risk scoring — rank entities by likelihood of next failure.

Reads from the in-process incident store (which is hydrated from FalkorDB
on startup, so historical investigations contribute to the score).

Uses a transparent weighted-sum heuristic, not ML — every score is
explainable to a judge in 30 seconds via ``RiskScore.factors``.
"""

from chronos.risk.scorer import (
    RiskFactors,
    RiskScore,
    explain_entity,
    top_at_risk,
)

__all__ = ["RiskFactors", "RiskScore", "explain_entity", "top_at_risk"]
