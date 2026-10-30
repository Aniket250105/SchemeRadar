from typing import Tuple, List, Dict, Any
from core.models import StudentProfile, ScholarshipOpportunity

def evaluate_hard_eligibility(
    profile: StudentProfile,
    scholarship: ScholarshipOpportunity,
) -> Tuple[str, float, List[str], List[str], List[str]]:
    """Stage 1: Evaluate eligibility according to strict 3-state logic with confidence scoring.
    
    Returns:
        (
            eligibility_status: "Eligible" | "Potential match" | "Ineligible",
            eligibility_confidence: float (0.0 to 1.0),
            ineligibility_reasons: List[str],
            missing_criteria: List[str],
            verified_matches: List[str]
        )
        
    Rule:
        - "Eligible": Required conditions have been verified and matched.
        - "Potential match": Relevant info exists, but mandatory conditions remain unknown.
        - "Ineligible": A verified mandatory condition directly conflicts with the profile.
        Unknown conditions must NOT be treated as satisfied.
    """
    ineligibility_reasons: List[str] = []
    missing_criteria: List[str] = []
    verified_matches: List[str] = []

    criteria_points = 0.0
    total_criteria_weights = 5.0  # State, Course, Year, Category, Income

    # 1. State / Domicile
    if scholarship.eligible_states:
        norm_states = [s.strip().lower() for s in scholarship.eligible_states]
        student_state = profile.state_of_domicile.strip().lower()
        is_central = any(
            any(cs in s for cs in ["all india", "central", "pan india", "national", "india"])
            for s in norm_states
        )
        state_matched = is_central or any(student_state in s or s in student_state for s in norm_states)

        if state_matched:
            criteria_points += 1.0
            if is_central:
                verified_matches.append(f"Central / National scheme open to {profile.state_of_domicile}")
            else:
                verified_matches.append(f"Domicile matches {profile.state_of_domicile}")
        else:
            ineligibility_reasons.append(
                f"State restricted to {', '.join(scholarship.eligible_states)} (Student is from {profile.state_of_domicile})"
            )
    else:
        missing_criteria.append("State domicile criteria is not published on portal")

    # 2. Course Eligibility
    if scholarship.eligible_courses:
        norm_courses = [c.strip().lower() for c in scholarship.eligible_courses]
        student_course = profile.course.strip().lower()
        
        course_matched = False
        for ec in norm_courses:
            if ec in student_course or student_course in ec:
                course_matched = True
                break
            if "engineering" in ec and student_course in ["b.tech", "b.e.", "m.tech", "diploma"]:
                course_matched = True
                break
            if "technical" in ec or "professional" in ec or "stem" in ec:
                course_matched = True
                break
            if "undergraduate" in ec or "ug" in ec:
                if student_course in ["b.tech", "b.e.", "bca", "b.sc", "b.com", "ba", "mbbs"]:
                    course_matched = True
                    break

        if course_matched:
            criteria_points += 1.0
            verified_matches.append(f"Course matches {profile.course}")
        else:
            ineligibility_reasons.append(
                f"Course restricted to {', '.join(scholarship.eligible_courses)} (Student is studying {profile.course})"
            )
    else:
        missing_criteria.append("Specific course criteria needs verification on official portal")

    # 3. Academic Year Eligibility
    if scholarship.eligible_academic_years:
        norm_years = [y.strip().lower() for y in scholarship.eligible_academic_years]
        student_year = profile.academic_year.strip().lower()
        
        year_matched = any(
            sy in student_year or student_year in sy or "all" in sy
            for sy in norm_years
        )
        if year_matched:
            criteria_points += 1.0
            verified_matches.append(f"Academic year ({profile.academic_year}) is eligible")
        else:
            # Check fresher vs renewal restriction
            if any("1st" in y or "fresh" in y for y in norm_years) and ("2nd" in student_year or "3rd" in student_year or "4th" in student_year):
                ineligibility_reasons.append(
                    f"Only open to {', '.join(scholarship.eligible_academic_years)} (Student is in {profile.academic_year})"
                )
            else:
                missing_criteria.append(f"Year criteria {', '.join(scholarship.eligible_academic_years)} requires verification")
    else:
        missing_criteria.append("Academic year eligibility not specified on this notice")

    # 4. Social Category Eligibility
    if scholarship.eligible_categories:
        norm_cats = [c.strip().lower() for c in scholarship.eligible_categories]
        student_cat = profile.category.strip().lower()
        
        cat_matched = any(
            sc in student_cat or student_cat in sc or "all" in sc or "general" in sc
            for sc in norm_cats
        )
        if cat_matched:
            criteria_points += 1.0
            verified_matches.append(f"Open to your category ({profile.category})")
        else:
            ineligibility_reasons.append(
                f"Reserved for {', '.join(scholarship.eligible_categories)} (Student reported {profile.category})"
            )
    else:
        missing_criteria.append("Social category criteria open to all or unstated")

    # 5. Family Income Limit (Crucial: Unknown income must NOT be treated as satisfied!)
    student_max_income = profile.max_income_numeric()
    if scholarship.income_limit is not None and student_max_income is not None:
        band = profile.family_income_band
        student_lower_bound = 0.0
        if "1–2.5 lakh" in band or "1-2.5 lakh" in band:
            student_lower_bound = 100000.0
        elif "2.5–5 lakh" in band or "2.5-5 lakh" in band:
            student_lower_bound = 250000.0
        elif "5–8 lakh" in band or "5-8 lakh" in band:
            student_lower_bound = 500000.0
        elif "Above ₹8 lakh" in band:
            student_lower_bound = 800000.0

        if student_lower_bound > scholarship.income_limit:
            ineligibility_reasons.append(
                f"Income ceiling is ₹{scholarship.income_limit:,.0f} (Student's family income band is {profile.family_income_band})"
            )
        else:
            criteria_points += 1.0
            verified_matches.append(f"Family income ({profile.family_income_band}) is within limit of ₹{scholarship.income_limit:,.0f}")
    elif scholarship.income_limit is None:
        missing_criteria.append("Family income ceiling not published on official notice")

    # Determine 3-state eligibility
    if ineligibility_reasons:
        eligibility_status = "Ineligible"
        eligibility_confidence = 0.0
    elif not missing_criteria:
        eligibility_status = "Eligible"
        eligibility_confidence = round(criteria_points / total_criteria_weights, 2)
    else:
        eligibility_status = "Potential match"
        eligibility_confidence = round(criteria_points / total_criteria_weights, 2)

    return (
        eligibility_status,
        eligibility_confidence,
        ineligibility_reasons,
        missing_criteria,
        verified_matches,
    )
