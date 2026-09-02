from typing import List, Optional, Union

from pydantic import BaseModel, field_validator


class LabResultIn(BaseModel):
    test_name: str
    value: Optional[Union[float, str]] = None
    unit: Optional[str] = None
    min_reference: Optional[float] = None
    max_reference: Optional[float] = None

    @field_validator("test_name")
    @classmethod
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("test_name cannot be empty")
        return v


class AnalyzeRequest(BaseModel):
    patient_id: Optional[str] = None
    labs: List[LabResultIn]


class ExplainedResult(BaseModel):
    test_name: str
    value: Union[float, str]
    unit: str
    status: str
    normal_range: Optional[List[float]] = None
    explanation: str
    next_steps: List[str] = []
    error: Optional[str] = None


class AnalyzeResponse(BaseModel):
    patient_id: Optional[str] = None
    critical: List[ExplainedResult]
    warning: List[ExplainedResult]
    normal: List[ExplainedResult]
    unresolved: List[ExplainedResult]