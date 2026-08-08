from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StudentSearchProfile:
    raw_query: str
    language: str = "ar"
    target_country: Optional[str] = None
    major: Optional[str] = None
    degree_level: Optional[str] = None
    funding_type: Optional[str] = None
    keywords: List[str] = field(default_factory=list)


@dataclass
class RankedScholarship:
    scholarship: dict
    score: int
    reasons: List[str] = field(default_factory=list)
