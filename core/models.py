from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator
from datetime import datetime

class StudentProfile(BaseModel):
    """Student profile used for scholarship discovery and eligibility matching."""
    course: str = Field(..., description="Student's degree or course of study, e.g. B.Tech, BCA")
    academic_year: str = Field(..., description="Current academic year, e.g. 1st Year, 2nd Year")
    college_name: Optional[str] = Field(None, description="College or university name")
    academic_performance: Optional[str] = Field(None, description="CGPA or percentage marks")
    state_of_domicile: str = Field(..., description="Home state / domicile of student")
    category: str = Field(..., description="Social category, e.g. General, OBC, SC, ST, EWS")
    family_income_band: str = Field(..., description="Annual family income band")
    interests: List[str] = Field(default_factory=list, description="Fields of interest and specialization")

    def max_income_numeric(self) -> Optional[float]:
        """Convert family income band to maximum numeric ceiling in INR."""
        band = self.family_income_band
        if "Below ₹1 lakh" in band:
            return 100000.0
        elif "1–2.5 lakh" in band or "1-2.5 lakh" in band:
            return 250000.0
        elif "2.5–5 lakh" in band or "2.5-5 lakh" in band:
            return 500000.0
        elif "5–8 lakh" in band or "5-8 lakh" in band:
            return 800000.0
        elif "Above ₹8 lakh" in band:
            return 1500000.0
        return None


class SourcePage(BaseModel):
    """Represents a discovered portal landing page, directory, or notice board.
    Distinct from an individual scholarship opportunity.
    """
    source_id: str = Field(..., description="Unique source page identifier")
    website_name: str = Field(..., description="Portal name, e.g. National Scholarship Portal")
    source_url: str = Field(..., description="Full URL of the source page")
    domain: str = Field(..., description="Domain name, e.g. scholarships.gov.in")
    source_type: str = Field(
        "Portal Homepage",
        description="Portal Homepage | Scholarship Directory | Scheme Announcement | Third-Party Platform"
    )
    authority_level: str = Field(
        "Official Central Government",
        description="Official Central Government | Official State Government | Official University / Educational | Third-Party Information Portal"
    )
    fetch_status: str = Field("unattempted", description="success | proxy_error | failed | unattempted")
    last_checked: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


class FieldEvidence(BaseModel):
    """Provenance and verification tracking for an individual extracted attribute."""
    value: Any = None
    evidence_snippet: Optional[str] = None
    evidence_url: Optional[str] = None
    extraction_method: str = "tinyfish_fetch"  # tinyfish_search | tinyfish_fetch | tinyfish_agent
    verification_status: str = "direct_page_verified"  # direct_page_verified | search_snippet_only | unverified | third_party_unverified


class ScholarshipOpportunity(BaseModel):
    """An individual, named scholarship scheme opportunity with field-level provenance."""
    scheme_id: str = Field(..., description="Unique opportunity identifier")
    scheme_name: str = Field(..., description="Specific official scheme title")
    provider: Optional[str] = Field(None, description="Department, Ministry or Authority providing the grant")
    description: Optional[str] = Field(None, description="Detailed description of the opportunity")
    eligibility: Optional[str] = Field(None, description="Extracted eligibility text criteria")
    eligible_courses: List[str] = Field(default_factory=list, description="Eligible degree courses")
    eligible_years: List[str] = Field(default_factory=list, description="Eligible academic years")
    eligible_states: List[str] = Field(default_factory=list, description="Eligible states / Central")
    eligible_categories: List[str] = Field(default_factory=list, description="Eligible social categories")
    income_limit: Optional[float] = Field(None, description="Maximum annual family income in INR")
    amount: Optional[str] = Field(None, description="Scholarship grant amount or waiver description")
    deadline: Optional[str] = Field(None, description="Application closing date in YYYY-MM-DD or text")
    application_status: str = Field(
        "Needs verification",
        description="Open | Closing soon | Deadline approaching | Closed | Upcoming | Needs verification"
    )
    source_url: str = Field(..., description="URL where opportunity was discovered")
    application_url: Optional[str] = Field(None, description="Verified direct portal application link")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Provenance tracking per field")
    verification_status: str = Field(
        "direct_page_verified",
        description="direct_page_verified | search_snippet_only | unverified | third_party_unverified"
    )
    last_verified: Optional[str] = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))

    @model_validator(mode="before")
    @classmethod
    def _remap_legacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Map legacy attributes to Phase 2 schema
            if "maximum_income" in data and "income_limit" not in data:
                data["income_limit"] = data.pop("maximum_income")
            if "eligible_academic_years" in data and "eligible_years" not in data:
                data["eligible_years"] = data.pop("eligible_academic_years")
            if "scholarship_amount" in data and "amount" not in data:
                data["amount"] = data.pop("scholarship_amount")
            if "application_deadline" in data and "deadline" not in data:
                data["deadline"] = data.pop("application_deadline")
        return data

    # Backward-compatibility property helpers for existing UI components
    @property
    def scholarship_amount(self) -> Optional[str]:
        return self.amount

    @property
    def application_deadline(self) -> Optional[str]:
        return self.deadline

    @property
    def maximum_income(self) -> Optional[float]:
        return self.income_limit

    @property
    def eligible_academic_years(self) -> List[str]:
        return self.eligible_years

    @property
    def source_domain(self) -> str:
        from urllib.parse import urlparse
        return urlparse(self.source_url).netloc.lower()

    @property
    def extraction_method(self) -> str:
        # Pull from evidence or default
        if "scheme_name" in self.evidence and isinstance(self.evidence["scheme_name"], dict):
            return self.evidence["scheme_name"].get("extraction_method", "TinyFish Fetch")
        return "TinyFish Fetch"

    @property
    def missing_fields(self) -> List[str]:
        missing = []
        if not self.amount:
            missing.append("Scholarship Grant Amount")
        if not self.deadline:
            missing.append("Application Deadline")
        if not self.application_url or self.application_url == self.source_url:
            missing.append("Direct Application Portal Link")
        if self.income_limit is None:
            missing.append("Explicit Income Ceiling")
        if not self.eligible_courses:
            missing.append("Specific Course Criteria")
        return missing


# Alias for backward compatibility
Scholarship = ScholarshipOpportunity


class MatchResult(BaseModel):
    """Result of running eligibility filtering and scoring on an individual scholarship."""
    scholarship: ScholarshipOpportunity
    relevance_score: float = Field(0.0, description="Relevance score from 0 to 100 based on interest and stream")
    eligibility_confidence: float = Field(0.0, description="Confidence in eligibility based strictly on verified conditions (0.0 to 1.0)")
    eligibility_status: str = Field(
        "Potential match",
        description="Eligible | Potential match | Ineligible"
    )
    is_eligible: bool = Field(True, description="True if no hard disqualification encountered")
    is_potential_match: bool = Field(True, description="True if status is Eligible or Potential match")
    rejection_reasons: List[str] = Field(default_factory=list, description="Confirmed reasons for hard ineligibility")
    missing_criteria: List[str] = Field(default_factory=list, description="Mandatory criteria that remain unverified")
    why_this_matches_you: str = Field("", description="Explainable personalized match justification citing verified facts")
    urgency: str = Field(
        "Time available",
        description="Urgent | Closing soon | Deadline approaching | Time available | Closed | Upcoming | Needs verification"
    )
    score_breakdown: Dict[str, float] = Field(default_factory=dict, description="Detailed score points by dimension")

    @property
    def match_score(self) -> float:
        """Alias for backward compatibility with existing card components."""
        return self.relevance_score

    @property
    def verification_needed(self) -> List[str]:
        return self.missing_criteria


class ScamCheckResult(BaseModel):
    """Analysis result from the 'Is This Real?' scam checking engine."""
    input_text: str
    verdict: str = Field("Unable to verify", description="Likely legitimate | Suspicious | Unable to verify")
    confidence: float = Field(0.0, description="Confidence score 0.0 to 1.0")
    evidence: List[str] = Field(default_factory=list, description="Concrete evidence observed")
    red_flags: List[str] = Field(default_factory=list, description="Identified warning signs or suspicious indicators")
    legitimate_indicators: List[str] = Field(default_factory=list, description="Positive signs of legitimacy")
    official_sources_found: List[str] = Field(default_factory=list, description="Discovered official corroborating URLs")
    recommendations: List[str] = Field(default_factory=list, description="Actionable safety advice for the student")


class TinyFishLogEntry(BaseModel):
    """Activity log entry tracking live TinyFish operations."""
    timestamp: str = Field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))
    operation: str = Field(..., description="SEARCH | FETCH | AGENT")
    target: str = Field(..., description="Query phrase or target URL")
    status: str = Field(..., description="SUCCESS | FAILED | PROXY_ERROR | STREAMING")
    details: str = Field(..., description="Item count, chars extracted, or error details")
