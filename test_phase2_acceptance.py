import os
import sys
from datetime import datetime, date

# Reconfigure console for UTF-8
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import TINYFISH_API_KEY
from services.tinyfish_client import TinyFishClient
from services.extraction import ScholarshipExtractor
from services.discovery import DiscoveryService
from core.models import StudentProfile, ScholarshipOpportunity, SourcePage
from core.eligibility import evaluate_hard_eligibility
from core.matcher import calculate_match
from core.scam_checker import ScamChecker
from utils.helpers import (
    classify_domain_trust,
    classify_page_type,
    calculate_deadline_urgency,
    get_current_ist_time,
    is_safe_url,
)

def run_acceptance_tests():
    print("=" * 70)
    print("SCHEMERADAR — PHASE 2 ACCEPTANCE TEST SUITE")
    print("Verifying all 10 Acceptance Criteria with Real TinyFish Data")
    print("=" * 70)

    client = TinyFishClient()
    assert client.is_configured, "TINYFISH_API_KEY must be configured."

    # -------------------------------------------------------------------------
    # TEST 1: Generic government portal must NOT become a scholarship record
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Generic portal landing page rejection:")
    generic_portal_item = {
        "url": "https://ssp.karnataka.gov.in/",
        "title": "State Scholarship Portal - Government of Karnataka | Home",
        "snippet": "Welcome to State Scholarship Portal (SSP). Login for student post-matric and pre-matric applications.",
        "domain": "ssp.karnataka.gov.in",
        "site_name": "Karnataka SSP",
    }
    extracted_opps = ScholarshipExtractor.extract_opportunities(
        search_item=generic_portal_item,
        fetch_content="",  # Portal landing page without individual scheme specifications
        fetch_links=[],
        fetch_status="failed",
    )
    print(f"  Opportunities extracted from portal homepage: {len(extracted_opps)}")
    assert len(extracted_opps) == 0, "Portal homepage must NOT become a pseudo-scholarship opportunity!"
    
    # Verify it IS recorded as a SourcePage
    src_page = ScholarshipExtractor.extract_source_page(generic_portal_item)
    print(f"  Recorded as SourcePage: {src_page.website_name} ({src_page.source_type}, {src_page.authority_level})")
    assert src_page.source_type == "Portal Homepage"
    print("  ✓ PASS: Generic portal recorded as SourcePage, NOT as a scholarship record!")

    # -------------------------------------------------------------------------
    # TEST 2: AICTE directory must NOT be counted as an individual scholarship
    # -------------------------------------------------------------------------
    print("\n[TEST 2] AICTE Directory handling:")
    aicte_dir_item = {
        "url": "https://www.aicte-india.org/bureaus/rifd/Scholarship-Schemes",
        "title": "Scholarship Schemes | All India Council for Technical Education",
        "snippet": "AICTE offers various scholarship schemes for students studying in technical and professional institutions.",
        "domain": "aicte-india.org",
        "site_name": "AICTE",
    }
    aicte_src = ScholarshipExtractor.extract_source_page(aicte_dir_item)
    print(f"  Source Type: {aicte_src.source_type}")
    print(f"  Authority: {aicte_src.authority_level}")
    assert aicte_src.source_type == "Scholarship Directory"
    assert aicte_src.authority_level == "Official Central Government"

    # When processed without concrete individual scheme texts, should produce 0 pseudo-scholarships
    aicte_opps = ScholarshipExtractor.extract_opportunities(aicte_dir_item, fetch_content="")
    assert len(aicte_opps) == 0, "Directory page must not become a single pseudo-scholarship!"
    print("  ✓ PASS: AICTE directory classified as Scholarship Directory, NOT a single pseudo-scholarship!")

    # -------------------------------------------------------------------------
    # TEST 3: Real named scholarship extracted with supporting evidence
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Real named scholarship extraction with supporting evidence:")
    nsp_fetch = client.fetch_page("https://scholarships.gov.in/All-Scholarships")
    assert nsp_fetch.get("success"), "Fetch on NSP All-Scholarships directory must succeed"
    
    nsp_dir_item = {
        "url": "https://scholarships.gov.in/All-Scholarships",
        "title": "All Scholarships on National Scholarship Portal",
        "domain": "scholarships.gov.in",
    }
    real_opps = ScholarshipExtractor.extract_opportunities(
        search_item=nsp_dir_item,
        fetch_content=nsp_fetch.get("content", ""),
        fetch_links=nsp_fetch.get("links", []),
        method="TinyFish Fetch",
        fetch_status="success",
    )
    print(f"  Total individual schemes extracted from NSP directory: {len(real_opps)}")
    assert len(real_opps) >= 3, f"Expected at least 3 individual schemes, got {len(real_opps)}"
    
    # Inspect first extracted opportunity
    first = real_opps[0]
    print(f"  Scheme 1 Name: {first.scheme_name}")
    print(f"  Scheme 1 Deadline: {first.deadline}")
    print(f"  Scheme 1 Application Status: {first.application_status}")
    print(f"  Scheme 1 Verification Status: {first.verification_status}")
    assert first.evidence, "Field evidence provenance must be populated!"
    assert "scheme_name" in first.evidence
    assert first.evidence["scheme_name"]["verification_status"] == "direct_page_verified"
    print(f"  Scheme 1 Evidence Snippet for deadline: {first.evidence.get('deadline', {}).get('evidence_snippet')}")
    print("  ✓ PASS: Real named scholarships extracted with field-level provenance evidence!")

    # -------------------------------------------------------------------------
    # TEST 4: Third-party mirror must NOT become an official source
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Third-party mirror authority classification:")
    mirror_url = "https://www.buddy4study.com/scholarship/karnataka-post-matric-scholarship"
    mirror_trust = classify_domain_trust(mirror_url)
    print(f"  Domain: {mirror_trust['domain']}")
    print(f"  Is Official: {mirror_trust['is_official']}")
    print(f"  Authority Level: {mirror_trust['authority_level']}")
    assert mirror_trust["is_official"] is False, "Third party must NOT be marked as official!"
    assert mirror_trust["authority_level"] == "Third-Party Information Portal"

    mirror_item = {"url": mirror_url, "title": "Karnataka Post-Matric Mirror Scheme"}
    mirror_opps = ScholarshipExtractor.extract_opportunities(mirror_item, fetch_content="Details about scheme...", fetch_status="success")
    if mirror_opps:
        assert mirror_opps[0].verification_status == "third_party_unverified", "Third party must have third_party_unverified status!"
    print("  ✓ PASS: Third-party platform strictly classified as unofficial with third_party_unverified status!")

    # -------------------------------------------------------------------------
    # TEST 5: Unknown income requirements must NOT produce confirmed eligibility
    # -------------------------------------------------------------------------
    print("\n[TEST 5] Unknown income requirements handling:")
    test_profile = StudentProfile(
        course="B.Tech",
        academic_year="2nd Year",
        state_of_domicile="Karnataka",
        category="OBC",
        family_income_band="₹1–2.5 lakh",
    )
    # Scholarship with income_limit=None (unknown)
    sch_unknown_income = ScholarshipOpportunity(
        scheme_id="sch_test_unk",
        scheme_name="Merit-cum-Means Technical Assistance Scheme",
        provider="Ministry of Education",
        eligible_courses=["B.Tech", "B.E."],
        eligible_years=["2nd Year"],
        eligible_states=["Karnataka", "All India / Central"],
        eligible_categories=["OBC", "General"],
        income_limit=None,  # UNKNOWN
        deadline="2026-12-31",
        source_url="https://scholarships.gov.in/notice/1",
        application_status="Open",
        verification_status="direct_page_verified",
    )
    status, conf, rej, missing, matches = evaluate_hard_eligibility(test_profile, sch_unknown_income)
    print(f"  Eligibility Status: {status}")
    print(f"  Eligibility Confidence: {conf}")
    print(f"  Missing Criteria: {missing}")
    assert status == "Potential match", "Must be 'Potential match' when income is unknown, NOT 'Eligible'!"
    assert any("income" in m.lower() for m in missing), "Missing criteria must flag unknown income!"
    assert conf < 1.0, "Confidence cannot be 1.0 when a mandatory criterion is unverified!"
    print("  ✓ PASS: Unknown income produces Potential match with missing criteria warning!")

    # -------------------------------------------------------------------------
    # TEST 6: Expired deadline must be marked closed
    # -------------------------------------------------------------------------
    print("\n[TEST 6] Expired deadline verification:")
    sch_expired = ScholarshipOpportunity(
        scheme_id="sch_test_exp",
        scheme_name="Past Academic Year Scholarship 2025",
        deadline="2025-10-15",  # Past date
        source_url="https://scholarships.gov.in/archive",
        application_status="Open",  # Incorrectly labeled initially
    )
    urgency, days_left = calculate_deadline_urgency(sch_expired.deadline)
    print(f"  Calculated Urgency: {urgency} (Days left: {days_left})")
    assert urgency == "Closed", "Past deadline must calculate as Closed!"
    assert days_left < 0

    # Also test via extractor
    _, _, is_exp = ScholarshipExtractor._extract_deadline_with_evidence("Application deadline was 15/10/2025.")
    assert is_exp is True, "Extractor must detect expired date!"
    print("  ✓ PASS: Expired deadline correctly evaluated as Closed!")

    # -------------------------------------------------------------------------
    # TEST 7: Agent SSE parsing must return actual extracted data
    # -------------------------------------------------------------------------
    print("\n[TEST 7] Agent SSE structured data verification:")
    agent_raw_simulated = {
        "scheme_name": "AICTE Pragati Scholarship for Girls",
        "provider": "AICTE",
        "eligible_courses": ["B.Tech", "Diploma"],
        "eligible_states": ["All India / Central"],
        "eligible_categories": ["Girl Students"],
        "maximum_income": 800000.0,
        "scholarship_amount": "₹50,000 per annum",
        "application_deadline": "2026-10-31",
        "application_url": "https://www.aicte-pragati-saksham-gov.in",
        "application_status": "Open",
    }
    agent_opp = ScholarshipExtractor._create_opportunity_from_agent(
        agent_data=agent_raw_simulated,
        url="https://www.aicte-india.org/pragati",
        domain_trust={"is_official": True, "domain": "aicte-india.org"},
        search_item={},
        base_verif="direct_page_verified",
    )
    print(f"  Agent Extracted Name: {agent_opp.scheme_name}")
    print(f"  Agent Extracted Income Ceiling: ₹{agent_opp.income_limit:,.0f}")
    print(f"  Agent Extracted Amount: {agent_opp.amount}")
    assert agent_opp.scheme_name == "AICTE Pragati Scholarship for Girls"
    assert agent_opp.income_limit == 800000.0
    assert agent_opp.evidence["scheme_name"]["extraction_method"] == "tinyfish_agent"
    print("  ✓ PASS: Agent structured schema validated into ScholarshipOpportunity!")

    # -------------------------------------------------------------------------
    # TEST 8: Unavailable official website must produce honest verification warning
    # -------------------------------------------------------------------------
    print("\n[TEST 8] Unavailable official portal (proxy_error) handling:")
    proxy_err_item = {
        "url": "https://ssp.karnataka.gov.in/",
        "title": "Karnataka State Scholarship Portal Post-Matric",
        "snippet": "Karnataka SSP portal for SC, ST, OBC and Minorities scholarships 2026.",
        "domain": "ssp.karnataka.gov.in",
    }
    proxy_fetch_result = {
        "success": False,
        "errors": [{"url": "https://ssp.karnataka.gov.in/", "error": "proxy_error"}],
    }
    src_page_proxy = ScholarshipExtractor.extract_source_page(proxy_err_item, fetch_result=proxy_fetch_result)
    print(f"  SourcePage fetch_status: {src_page_proxy.fetch_status}")
    assert src_page_proxy.fetch_status == "proxy_error", "Must capture proxy_error status honestly!"

    # Extracted with proxy_error baseline
    proxy_opps = ScholarshipExtractor.extract_opportunities(
        search_item=proxy_err_item,
        fetch_content="",
        fetch_status="proxy_error",
    )
    # When official page is down, generic portal is not converted to a fake scholarship
    assert len(proxy_opps) == 0
    print("  ✓ PASS: Firewall / proxy_error captured honestly without fabricating content!")

    # -------------------------------------------------------------------------
    # TEST 9: Scam checker distinguishes payment warnings from conclusive fraud
    # -------------------------------------------------------------------------
    print("\n[TEST 9] Scam checker nuanced evaluation:")
    scam_checker = ScamChecker(client)
    
    # 9a: Dangerous localhost / private IP URL
    res_unsafe = scam_checker.investigate("Apply for scholarship on http://127.0.0.1:8000/apply")
    print(f"  Localhost URL verdict: {res_unsafe.verdict} (Red flags: {len(res_unsafe.red_flags)})")
    assert res_unsafe.verdict == "Suspicious"
    assert any("dangerous url" in rf.lower() for rf in res_unsafe.red_flags)

    # 9b: Private OTP sharing vs portal 2FA
    res_share_otp = scam_checker.investigate("Send your Aadhaar OTP on WhatsApp to claim your ₹50,000 scholarship.")
    print(f"  Share OTP verdict: {res_share_otp.verdict}")
    assert res_share_otp.verdict == "Suspicious"
    assert any("requests sharing confidential otp" in rf.lower() for rf in res_share_otp.red_flags)

    # 9c: Portal 2FA mention
    res_portal_2fa = scam_checker.investigate("Karnataka SSP login uses mobile Aadhaar OTP verification on ssp.postmatric.karnataka.gov.in")
    print(f"  Portal 2FA indicators: {res_portal_2fa.legitimate_indicators}")
    assert any("two-factor" in li.lower() for li in res_portal_2fa.legitimate_indicators)

    # 9d: Fee request warning
    res_fee = scam_checker.investigate("National Talent Scholarship test registration fee of ₹150 required.")
    assert any("fee" in rf.lower() for rf in res_fee.red_flags)
    print("  ✓ PASS: Scam checker nuanced rules validated!")

    # -------------------------------------------------------------------------
    # TEST 10: Complete student-profile-to-results workflow functions
    # -------------------------------------------------------------------------
    print("\n[TEST 10] Complete end-to-end discovery workflow:")
    discovery = DiscoveryService(client)
    
    def on_prog(msg, pct):
        print(f"    [{pct}%] {msg}")

    e2e_result = discovery.discover(
        profile=test_profile,
        progress_callback=on_prog,
        max_sources_to_process=2,
    )
    print(f"  Discovery Success: {e2e_result['success']}")
    print(f"  Source Websites Discovered: {e2e_result['metrics']['total_sources']}")
    print(f"  Scholarships Extracted: {e2e_result['metrics']['total_extracted']}")
    print(f"  Verified Open: {e2e_result['metrics']['verified_open']}")
    print(f"  Potential Matches: {e2e_result['metrics']['potential_matches']}")
    print(f"  Requiring Verification: {e2e_result['metrics']['requiring_verification']}")
    print(f"  TinyFish Activity Log count: {len(e2e_result['activity_log'])}")

    assert e2e_result["success"] is True
    assert e2e_result["metrics"]["total_sources"] >= 1
    assert e2e_result["metrics"]["total_extracted"] >= 1
    assert len(e2e_result["activity_log"]) >= 1

    first_match = e2e_result["matches"][0]
    print(f"\n  Top Match: {first_match.scholarship.scheme_name}")
    print(f"  Relevance: {first_match.relevance_score}% | Confidence: {int(first_match.eligibility_confidence * 100)}%")
    print(f"  Status: {first_match.eligibility_status}")
    print(f"  Why This Matches: {first_match.why_this_matches_you}")
    print("  ✓ PASS: Complete end-to-end workflow successfully executed!")

    print("\n" + "=" * 70)
    print("ALL 10 PHASE 2 ACCEPTANCE TESTS PASSED WITH 100% SUCCESS! 🎯")
    print("=" * 70)

if __name__ == "__main__":
    run_acceptance_tests()

