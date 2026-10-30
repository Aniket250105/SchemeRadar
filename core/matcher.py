from typing import List, Dict, Any
from core.models import StudentProfile, ScholarshipOpportunity, MatchResult
from core.eligibility import evaluate_hard_eligibility
from utils.helpers import calculate_deadline_urgency

def calculate_match(profile: StudentProfile, scholarship: ScholarshipOpportunity) -> MatchResult:
    """Stage 2: Calculate separated relevance score (0-100) and eligibility confidence (0.0-1.0).
    Generates transparent, explainable feedback distinguishing verified matches from missing data.
    """
    (
        eligibility_status,
        eligibility_confidence,
        ineligibility_reasons,
        missing_criteria,
        verified_matches,
    ) = evaluate_hard_eligibility(profile, scholarship)

    score_breakdown: Dict[str, float] = {}

    # 1. State / Domicile Compatibility (Max 20 pts)
    state_score = 0.0
    if scholarship.eligible_states:
        norm_states = [s.strip().lower() for s in scholarship.eligible_states]
        s_state = profile.state_of_domicile.strip().lower()
        is_central = any(
            any(cs in s for cs in ["all india", "central", "national", "pan india", "india"])
            for s in norm_states
        )
        if any(s_state in s or s in s_state for s in norm_states):
            state_score = 20.0
        elif is_central:
            state_score = 18.0
        else:
            state_score = 0.0
    else:
        state_score = 10.0  # Open / Unspecified
    score_breakdown["State Compatibility"] = state_score

    # 2. Course Compatibility (Max 20 pts)
    course_score = 0.0
    if scholarship.eligible_courses:
        norm_courses = [c.strip().lower() for c in scholarship.eligible_courses]
        s_course = profile.course.strip().lower()
        if any(s_course in c or c in s_course for c in norm_courses):
            course_score = 20.0
        elif "engineering" in "".join(norm_courses) and s_course in ["b.tech", "b.e."]:
            course_score = 20.0
        elif any(term in "".join(norm_courses) for term in ["technical", "stem", "undergraduate", "ug"]):
            course_score = 16.0
        else:
            course_score = 5.0
    else:
        course_score = 10.0
    score_breakdown["Course Compatibility"] = course_score

    # 3. Academic Year (Max 15 pts)
    year_score = 0.0
    if scholarship.eligible_academic_years:
        norm_years = [y.strip().lower() for y in scholarship.eligible_academic_years]
        s_year = profile.academic_year.strip().lower()
        if any(s_year in y or y in s_year or "all" in y for y in norm_years):
            year_score = 15.0
        else:
            year_score = 4.0
    else:
        year_score = 10.0
    score_breakdown["Academic Year"] = year_score

    # 4. Social Category (Max 15 pts)
    category_score = 0.0
    if scholarship.eligible_categories:
        norm_cats = [c.strip().lower() for c in scholarship.eligible_categories]
        s_cat = profile.category.strip().lower()
        if any(s_cat in c or c in s_cat for c in norm_cats):
            category_score = 15.0
        elif any(c in ["general", "all", "open"] for c in norm_cats):
            category_score = 13.0
        else:
            category_score = 3.0
    else:
        category_score = 9.0
    score_breakdown["Category"] = category_score

    # 5. Income Compatibility (Max 15 pts)
    income_score = 0.0
    student_max = profile.max_income_numeric()
    if scholarship.income_limit is not None:
        if student_max is not None and student_max <= scholarship.income_limit:
            income_score = 15.0
        elif student_max is not None and student_max > scholarship.income_limit:
            income_score = 2.0
        else:
            income_score = 8.0
    else:
        # Income ceiling not explicitly specified
        income_score = 8.0
    score_breakdown["Income Eligibility"] = income_score

    # 6. Interest Alignment (Max 10 pts)
    interest_score = 0.0
    if profile.interests:
        matched_interests = []
        blob = f"{scholarship.scheme_name} {scholarship.description or ''} {scholarship.eligibility or ''}".lower()
        for interest in profile.interests:
            if interest.lower() in blob:
                matched_interests.append(interest)
        
        if matched_interests:
            interest_score = min(10.0, len(matched_interests) * 5.0)
            verified_matches.append(f"Aligns with your interest in {', '.join(matched_interests)}")
        else:
            interest_score = 4.0
    else:
        interest_score = 5.0
    score_breakdown["Interests Relevance"] = interest_score

    # 7. Verified Application Portal (Max 5 pts)
    portal_score = 0.0
    if scholarship.application_url and scholarship.application_url.startswith("http"):
        portal_score = 5.0
    elif scholarship.source_url:
        portal_score = 3.0
    score_breakdown["Portal Availability"] = portal_score

    # Compute Total Relevance Score (0 to 100)
    relevance_score = sum(score_breakdown.values())
    relevance_score = min(100.0, max(0.0, round(relevance_score, 1)))

    if eligibility_status == "Ineligible":
        relevance_score = min(30.0, relevance_score)

    # Deadline Urgency
    urgency, _ = calculate_deadline_urgency(scholarship.deadline)

    # Build Explainable "Why this matches you"
    parts = []
    if verified_matches:
        parts.append(f"Verified match: {', '.join(verified_matches)}.")
    if missing_criteria:
        parts.append(f"Requires verification: {', '.join(missing_criteria)}.")
    if ineligibility_reasons:
        parts.append(f"Incompatible criteria: {'; '.join(ineligibility_reasons)}.")

    why_text = " ".join(parts) if parts else "Meets general student criteria; check official guidelines on portal."

    return MatchResult(
        scholarship=scholarship,
        relevance_score=relevance_score,
        eligibility_confidence=eligibility_confidence,
        eligibility_status=eligibility_status,
        is_eligible=(eligibility_status == "Eligible"),
        is_potential_match=(eligibility_status in ("Eligible", "Potential match")),
        rejection_reasons=ineligibility_reasons,
        missing_criteria=missing_criteria,
        why_this_matches_you=why_text,
        urgency=urgency,
        score_breakdown=score_breakdown,
    )

def rank_matches(matches: List[MatchResult], sort_by: str = "Highest match") -> List[MatchResult]:
    """Sort matches according to user preference."""
    if sort_by == "Highest match":
        return sorted(
            matches,
            key=lambda m: (m.eligibility_status == "Eligible", m.eligibility_status == "Potential match", m.relevance_score),
            reverse=True
        )
    elif sort_by == "Deadline approaching":
        urgency_order = {"Urgent": 0, "Closing soon": 1, "Deadline approaching": 2, "Time available": 3, "Needs verification": 4, "Closed": 5}
        return sorted(matches, key=lambda m: (urgency_order.get(m.urgency, 99), -m.relevance_score))
    elif sort_by == "Highest scholarship amount":
        def extract_amt(m: MatchResult) -> float:
            amt_str = m.scholarship.amount or ""
            import re
            nums = re.findall(r"\d+", amt_str.replace(",", ""))
            return float(nums[0]) if nums else 0.0
        return sorted(matches, key=lambda m: (m.is_potential_match, extract_amt(m), m.relevance_score), reverse=True)
    return matches
