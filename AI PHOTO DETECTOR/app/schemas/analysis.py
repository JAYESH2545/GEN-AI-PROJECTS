from typing import Any, Literal
from pydantic import BaseModel, Field

RiskLevel = Literal["low", "medium", "high", "critical"]
Verdict = Literal["malicious", "benign", "suspicious","Likely_Real", "Likely_AI_generated", "suspicious"]
Confidence = Literal["low", "medium", "high", "critical"]
Severity = Literal["low", "medium", "high", "critical"]

class Signal(BaseModel):
    name: str
    score: float = Field(ge=0.0, le=1.0)
    severity: Severity
    explanation: str
    category: str = Field(default="general", exclude=True, description="The category of the signal, e.g., 'network', 'file', 'behavior'")

class AnalysisResult(BaseModel):
    report_id: str
    file_hash: str
    ai_probability: float = Field(ge=0.0, le=1.0)
    risk_level: RiskLevel
    verdict: Verdict
    confidence: Confidence
    signals: list[Signal]
    metadata: dict[str, Any]
    tecchnical_details: dict[str, Any]
    recommendations: list[str]