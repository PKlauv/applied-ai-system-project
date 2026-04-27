from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class BugFinding:
    label: str
    severity: str  # "low" | "medium" | "high"
    confidence: float  # 0.0 – 1.0
    line: Optional[int]
    explanation: str


@dataclass
class IterationResult:
    iteration: int
    bugs_found: List[BugFinding]
    fixed_code: Optional[str]
    pytest_passed: bool
    pytest_output: str


@dataclass
class Report:
    run_id: str
    source_file: str
    iterations: List[IterationResult]
    final_bugs: List[BugFinding]
    final_pytest_passed: bool
    final_pytest_output: str
    avg_confidence: float = field(init=False)

    def __post_init__(self):
        confidences = [b.confidence for b in self.final_bugs]
        self.avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
