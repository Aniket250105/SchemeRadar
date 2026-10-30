import re
import uuid
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlparse
from datetime import datetime

from core.models import SourcePage, ScholarshipOpportunity, FieldEvidence, Scholarship
from utils.helpers import (
    extract_income_ceiling,
    parse_date_string,
    classify_domain_trust,
    classify_page_type,
    calculate_deadline_urgency,
    get_current_ist_time,
    is_safe_url,
)

class ScholarshipExtractor:
    """Extracts structured SourcePages and individual ScholarshipOpportunities
    with field-level provenance and verification tracking.
    """

    @staticmethod
    def extract_source_page(
        search_item: Dict[str, Any],
        fetch_result: Optional[Dict[str, Any]] = None,
    ) -> SourcePage:
        """Create a distinct SourcePage record representing a portal, directory, or website."""
        url = search_item.get("url", "").strip()
        trust = classify_domain_trust(url)
        title = search_item.get("title", "")
        site_name = search_item.get("site_name", "") or trust.get("tier", "")
        
        # Determine fetch status and content
        fetch_status = "unattempted"
        content = ""
        if fetch_result is not None:
            if fetch_result.get("success"):
                fetch_status = "success"
                content = fetch_result.get("content", "")
            else:
                errors = str(fetch_result.get("errors", "")) + " " + str(fetch_result.get("error", ""))
                if "proxy_error" in errors.lower():
                    fetch_status = "proxy_error"
                else:
                    fetch_status = "failed"

        page_type = classify_page_type(url, title=title, text=content)
        source_id = f"src_{abs(hash(url)) % 1000000:06d}"

        website_name = site_name if len(site_name) > 3 else trust["domain"]
        if "ssp.karnataka" in url.lower():
            website_name = "Karnataka State Scholarship Portal (SSP)"
        elif "scholarships.gov.in" in url.lower():
            website_name = "National Scholarship Portal (NSP)"
        elif "aicte-india" in url.lower():
            website_name = "AICTE Scholarship Portal"

        return SourcePage(
            source_id=source_id,
            website_name=website_name,
            source_url=url,
            domain=trust["domain"],
            source_type=page_type,
            authority_level=trust["authority_level"],
            fetch_status=fetch_status,
            last_checked=get_current_ist_time().strftime("%Y-%m-%d %H:%M:%S"),
        )

    @staticmethod
    def extract_opportunities(
        search_item: Dict[str, Any],
        fetch_content: str = "",
        fetch_links: Optional[List[str]] = None,
        agent_data: Any = None,
        method: str = "TinyFish Fetch",
        fetch_status: str = "success",
    ) -> List[ScholarshipOpportunity]:
        """Extract individual, named ScholarshipOpportunity records with field-level evidence.
        
        Returns:
            List[ScholarshipOpportunity].
            Returns [] if the page is a generic portal landing page or directory without
            concrete individual scheme specifications.
        """
        url = search_item.get("url", "").strip()
        trust = classify_domain_trust(url)
        is_official = trust["is_official"]
        page_type = classify_page_type(url, title=search_item.get("title", ""), text=fetch_content)

        # Baseline verification status based on domain authority and fetch status
        if not is_official:
            base_verif = "third_party_unverified"
        elif fetch_status == "proxy_error":
            base_verif = "search_snippet_only"
        elif fetch_status == "success" and len(fetch_content) > 50:
            base_verif = "direct_page_verified"
        else:
            base_verif = "search_snippet_only"

        # Case 1: Agent returned structured JSON scheme
        if isinstance(agent_data, dict) and agent_data.get("scheme_name"):
            name = str(agent_data["scheme_name"]).strip()
            # Ignore if agent accidentally outputted prompt text or generic word
            if len(name) >= 6 and "navigate" not in name.lower() and "find published" not in name.lower():
                opp = ScholarshipExtractor._create_opportunity_from_agent(
                    agent_data=agent_data,
                    url=url,
                    domain_trust=trust,
                    search_item=search_item,
                    base_verif=base_verif,
                )
                return [opp]

        # Case 2: Multi-scheme Directory Page (e.g. scholarships.gov.in/All-Scholarships)
        # Parse distinct scheme blocks from markdown
        if fetch_content and len(fetch_content) > 200:
            blocks = ScholarshipExtractor._split_directory_blocks(fetch_content)
            if len(blocks) >= 1:
                opportunities = []
                for b_title, b_text in blocks:
                    opp = ScholarshipExtractor._build_single_opportunity(
                        scheme_title=b_title,
                        block_text=b_text,
                        url=url,
                        search_item=search_item,
                        domain_trust=trust,
                        fetch_links=fetch_links or [],
                        method=method,
                        base_verif=base_verif,
                    )
                    if opp:
                        opportunities.append(opp)
                if opportunities:
                    return opportunities

        # Case 3: If it's a generic portal homepage with NO specific scheme, do NOT manufacture one!
        if page_type == "Portal Homepage":
            return []

        # If it's an AICTE directory or portal directory without discrete scheme records, do NOT manufacture one!
        if page_type == "Scholarship Directory" and not fetch_content:
            return []

        # Case 4: Single scheme announcement page or specific search snippet
        raw_title = search_item.get("title", "")
        snippet = search_item.get("snippet", "")
        single_name = ScholarshipExtractor._extract_scheme_name(fetch_content, raw_title, search_item.get("site_name", ""), trust["domain"])
        
        # Check if single_name is genuinely an individual scheme or just the portal name
        if ScholarshipExtractor._is_generic_portal_title(single_name, trust["domain"]):
            # Generic portal landing: reject as individual opportunity
            return []

        corpus = f"{raw_title}\n\n{snippet}\n\n{fetch_content}".strip()
        opp = ScholarshipExtractor._build_single_opportunity(
            scheme_title=single_name,
            block_text=corpus,
            url=url,
            search_item=search_item,
            domain_trust=trust,
            fetch_links=fetch_links or [],
            method="TinyFish Search" if fetch_status == "proxy_error" else method,
            base_verif=base_verif,
        )
        return [opp] if opp else []

    @staticmethod
    def _is_generic_portal_title(name: str, domain: str) -> bool:
        """Check if title represents the whole portal rather than an individual scheme."""
        n_lower = name.lower()
        generic_markers = [
            "national scholarship portal",
            "state scholarship portal",
            "karnataka ssp",
            "aicte scholarship portal",
            "home page",
            "login portal",
            "official portal",
            "welcome to",
        ]
        for marker in generic_markers:
            if n_lower == marker or n_lower.startswith(marker + " home"):
                return True
        return False

    @staticmethod
    def _split_directory_blocks(content: str) -> List[Tuple[str, str]]:
        """Split a directory page markdown into individual scheme title + details blocks."""
        # Check headings like ###### Scheme Name or ### Scheme Name
        pattern = r"(?:^|\n)(?:######|#####|####|###)\s*([^\n]+)(.*?)(?=(?:\n(?:######|#####|####|###)\s*[^\n]+)|\Z)"
        matches = re.findall(pattern, content, re.DOTALL)
        blocks = []
        for raw_title, raw_body in matches:
            t = re.sub(r"^#+\s*", "", raw_title).strip()
            # Filter out non-scheme structural headings
            if len(t) < 8 or t.lower() in ("schemes", "schemes on nsp", "specifications", "faq", "guidelines", "home"):
                continue
            if any(term in t.lower() for term in ["scheme", "scholarship", "pragati", "saksham", "swanath", "fellowship", "concession", "grant"]):
                blocks.append((t, raw_body.strip()))
        return blocks

    @staticmethod
    def _build_single_opportunity(
        scheme_title: str,
        block_text: str,
        url: str,
        search_item: Dict[str, Any],
        domain_trust: Dict[str, Any],
        fetch_links: List[str],
        method: str,
        base_verif: str,
    ) -> Optional[ScholarshipOpportunity]:
        """Construct a validated ScholarshipOpportunity with field-level evidence provenance."""
        evidence: Dict[str, Any] = {}
        now_str = get_current_ist_time().strftime("%Y-%m-%d %H:%M")

        # 1. Scheme Name
        evidence["scheme_name"] = {
            "value": scheme_title,
            "evidence_snippet": f"Identified official scheme title: {scheme_title}",
            "evidence_url": url,
            "extraction_method": method,
            "verification_status": base_verif,
        }

        # 2. Provider / Department
        provider, prov_snippet = ScholarshipExtractor._extract_provider_with_evidence(block_text, domain_trust["domain"])
        evidence["provider"] = {
            "value": provider,
            "evidence_snippet": prov_snippet or (f"Inferred authority for domain {domain_trust['domain']}" if provider else None),
            "evidence_url": url,
            "extraction_method": method,
            "verification_status": base_verif if provider else "unverified",
        }

        # 3. Description
        description = ScholarshipExtractor._extract_description(block_text, search_item.get("snippet", ""))

        # 4. Eligibility Text
        elig_text = ScholarshipExtractor._extract_eligibility_text(block_text)
        evidence["eligibility"] = {
            "value": elig_text,
            "evidence_snippet": elig_text[:200] if elig_text else None,
            "evidence_url": url,
            "extraction_method": method,
            "verification_status": base_verif if elig_text else "unverified",
        }

        # 5. Eligible Courses
        courses, c_snippet = ScholarshipExtractor._extract_courses(block_text)
        evidence["eligible_courses"] = {
            "value": courses,
            "evidence_snippet": c_snippet,
            "evidence_url": url,
            "extraction_method": method,
            "verification_status": base_verif if courses else "unverified",
        }

        # 6. Eligible Academic Years
        years, y_snippet = ScholarshipExtractor._extract_years(block_text)
        evidence["eligible_years"] = {
            "value": years,
            "evidence_snippet": y_snippet,
            "evidence_url": url,
            "extraction_method": method,
            "verification_status": base_verif if years else "unverified",
        }

        # 7. Eligible States
        states, s_snippet = ScholarshipExtractor._extract_states(block_text, domain_trust["domain"], scheme_title)
        evidence["eligible_states"] = {
            "value": states,
            "evidence_snippet": s_snippet,
            "evidence_url": url,
            "extraction_method": method,
            "verification_status": base_verif if states else "unverified",
        }

        # 8. Eligible Categories
        categories, cat_snippet = ScholarshipExtractor._extract_categories(block_text, scheme_title)
        evidence["eligible_categories"] = {
            "value": categories,
            "evidence_snippet": cat_snippet,
            "evidence_url": url,
            "extraction_method": method,
            "verification_status": base_verif if categories else "unverified",
        }

        # 9. Maximum Income Limit (Never invent if unknown!)
        max_income, inc_snippet = ScholarshipExtractor._extract_income_with_evidence(block_text)
        evidence["income_limit"] = {
            "value": max_income,
            "evidence_snippet": inc_snippet,
            "evidence_url": url,
            "extraction_method": method,
            "verification_status": base_verif if max_income is not None else "unverified",
        }

        # 10. Scholarship Amount
        amount, amt_snippet = ScholarshipExtractor._extract_amount_with_evidence(block_text)
        evidence["amount"] = {
            "value": amount,
            "evidence_snippet": amt_snippet,
            "evidence_url": url,
            "extraction_method": method,
            "verification_status": base_verif if amount else "unverified",
        }

        # 11. Application Deadline
        deadline, d_snippet, is_expired = ScholarshipExtractor._extract_deadline_with_evidence(block_text)
        evidence["deadline"] = {
            "value": deadline,
            "evidence_snippet": d_snippet,
            "evidence_url": url,
            "extraction_method": method,
            "verification_status": base_verif if deadline else "unverified",
        }

        # 12. Application Status
        if is_expired:
            app_status = "Closed"
        elif deadline:
            urgency, _ = calculate_deadline_urgency(deadline)
            if urgency in ("Urgent", "Closing soon"):
                app_status = "Closing soon"
            elif urgency == "Closed":
                app_status = "Closed"
            else:
                app_status = "Open"
        else:
            app_status = ScholarshipExtractor._determine_status(block_text, deadline)

        evidence["application_status"] = {
            "value": app_status,
            "evidence_snippet": f"Derived from status text / deadline {deadline or 'none'}",
            "evidence_url": url,
            "extraction_method": method,
            "verification_status": base_verif if deadline else "unverified",
        }

        # 13. Application URL (Must be a safe, valid URL)
        app_url, app_url_snippet = ScholarshipExtractor._extract_application_link(block_text, fetch_links, url)
        evidence["application_url"] = {
            "value": app_url,
            "evidence_snippet": app_url_snippet,
            "evidence_url": url,
            "extraction_method": method,
            "verification_status": "direct_page_verified" if (app_url and is_safe_url(app_url) and domain_trust["is_official"]) else ("third_party_unverified" if app_url else "unverified"),
        }

        scheme_id = f"sch_{abs(hash(scheme_title + url)) % 1000000:06d}"

        return ScholarshipOpportunity(
            scheme_id=scheme_id,
            scheme_name=scheme_title,
            provider=provider,
            description=description,
            eligibility=elig_text,
            eligible_courses=courses,
            eligible_years=years,
            eligible_states=states,
            eligible_categories=categories,
            income_limit=max_income,
            amount=amount,
            deadline=deadline,
            application_status=app_status,
            source_url=url,
            application_url=app_url,
            evidence=evidence,
            verification_status=base_verif,
            last_verified=now_str,
        )

    @staticmethod
    def _create_opportunity_from_agent(
        agent_data: Dict[str, Any],
        url: str,
        domain_trust: Dict[str, Any],
        search_item: Dict[str, Any],
        base_verif: str,
    ) -> ScholarshipOpportunity:
        """Construct ScholarshipOpportunity from validated TinyFish Agent JSON."""
        scheme_name = str(agent_data.get("scheme_name", "Official Scholarship Scheme")).strip()
        provider = agent_data.get("provider")
        description = agent_data.get("description")
        eligibility = agent_data.get("eligibility")
        
        courses = agent_data.get("eligible_courses") or []
        if isinstance(courses, str):
            courses = [c.strip() for c in courses.split(",") if c.strip()]
            
        years = agent_data.get("eligible_academic_years") or []
        if isinstance(years, str):
            years = [y.strip() for y in years.split(",") if y.strip()]

        states = agent_data.get("eligible_states") or []
        if isinstance(states, str):
            states = [s.strip() for s in states.split(",") if s.strip()]

        categories = agent_data.get("eligible_categories") or []
        if isinstance(categories, str):
            categories = [c.strip() for c in categories.split(",") if c.strip()]

        max_income = None
        if agent_data.get("maximum_income") is not None:
            try:
                max_income = float(agent_data["maximum_income"])
            except (ValueError, TypeError):
                pass

        amount = agent_data.get("scholarship_amount")
        deadline = agent_data.get("application_deadline")
        if deadline:
            parsed = parse_date_string(str(deadline))
            if parsed:
                deadline = parsed.strftime("%Y-%m-%d")

        app_url = agent_data.get("application_url")
        if app_url and not is_safe_url(app_url):
            app_url = None

        app_status = agent_data.get("application_status", "Needs verification")
        if deadline:
            urgency, _ = calculate_deadline_urgency(deadline)
            if urgency == "Closed":
                app_status = "Closed"

        evidence = {
            "scheme_name": {"value": scheme_name, "evidence_snippet": "Extracted via TinyFish Agent SSE", "evidence_url": url, "extraction_method": "tinyfish_agent", "verification_status": base_verif},
            "provider": {"value": provider, "evidence_snippet": f"Agent verified: {provider}", "evidence_url": url, "extraction_method": "tinyfish_agent", "verification_status": base_verif if provider else "unverified"},
            "amount": {"value": amount, "evidence_snippet": f"Agent extracted amount: {amount}", "evidence_url": url, "extraction_method": "tinyfish_agent", "verification_status": base_verif if amount else "unverified"},
            "income_limit": {"value": max_income, "evidence_snippet": f"Agent extracted income: {max_income}", "evidence_url": url, "extraction_method": "tinyfish_agent", "verification_status": base_verif if max_income is not None else "unverified"},
            "deadline": {"value": deadline, "evidence_snippet": f"Agent extracted deadline: {deadline}", "evidence_url": url, "extraction_method": "tinyfish_agent", "verification_status": base_verif if deadline else "unverified"},
            "application_url": {"value": app_url, "evidence_snippet": f"Agent extracted application portal: {app_url}", "evidence_url": url, "extraction_method": "tinyfish_agent", "verification_status": base_verif if app_url else "unverified"},
            "application_status": {"value": app_status, "evidence_snippet": f"Status: {app_status}", "evidence_url": url, "extraction_method": "tinyfish_agent", "verification_status": base_verif},
        }

        scheme_id = f"sch_{abs(hash(scheme_name + url)) % 1000000:06d}"

        return ScholarshipOpportunity(
            scheme_id=scheme_id,
            scheme_name=scheme_name,
            provider=provider,
            description=description,
            eligibility=eligibility,
            eligible_courses=courses,
            eligible_years=years,
            eligible_states=states,
            eligible_categories=categories,
            income_limit=max_income,
            amount=amount,
            deadline=deadline,
            application_status=app_status,
            source_url=url,
            application_url=app_url,
            evidence=evidence,
            verification_status=base_verif,
            last_verified=get_current_ist_time().strftime("%Y-%m-%d %H:%M"),
        )

    # -------------------------------------------------------------------------
    # Helper extraction methods with provenance snippets
    # -------------------------------------------------------------------------

    @staticmethod
    def _extract_scheme_name(content: str, raw_title: str, site_name: str, domain: str) -> str:
        """Extract clean scheme name without generic boilerplate."""
        # Check markdown heading
        h1_match = re.search(r"^#+\s+(.+)$", content, re.MULTILINE)
        if h1_match:
            t = h1_match.group(1).strip()
            if 10 < len(t) < 130 and "home" not in t.lower() and "login" not in t.lower() and "404" not in t:
                return t

        if raw_title and len(raw_title) > 6:
            cleaned = re.sub(r"\s*[-|–—:]\s*(?:Home|Login|Official Portal|Govt of India|NIC).*$", "", raw_title, flags=re.IGNORECASE)
            cleaned = re.sub(r"\(.*?\)", "", cleaned).strip()
            if len(cleaned) > 8:
                return cleaned

        if site_name and len(site_name) > 3:
            return f"{site_name} Scheme"

        return f"{domain.capitalize()} Scholarship"

    @staticmethod
    def _extract_provider_with_evidence(text: str, domain: str) -> Tuple[Optional[str], Optional[str]]:
        dept_match = re.search(
            r"((?:Department of|Ministry of|Directorate of|Council of)\s+[A-Za-z\s&]{4,45}?)(?:\s+(?:Scheme|Portal|Govt|Government|is|was|\.|\:|\-|$))",
            text,
            re.IGNORECASE,
        )
        if dept_match:
            prov = dept_match.group(1).strip()
            return prov, dept_match.group(0).strip()

        if "karnataka.gov.in" in domain:
            return "Government of Karnataka", "Extracted from official karnataka.gov.in portal domain"
        elif "scholarships.gov.in" in domain:
            return "Ministry of Electronics & Information Technology / Central Ministries", "Official NSP Portal Provider"
        elif "aicte" in domain:
            return "All India Council for Technical Education (AICTE)", "Official AICTE Authority"
        elif "ugc" in domain:
            return "University Grants Commission (UGC)", "Official UGC Authority"
        return None, None

    @staticmethod
    def _extract_description(content: str, snippet: str) -> Optional[str]:
        if content:
            paras = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 60]
            for p in paras:
                if not p.startswith("#") and not p.startswith("[") and "cookie" not in p.lower():
                    return p[:280] + ("..." if len(p) > 280 else "")
        if snippet and len(snippet) > 40:
            return snippet[:280] + ("..." if len(snippet) > 280 else "")
        return None

    @staticmethod
    def _extract_eligibility_text(text: str) -> Optional[str]:
        match = re.search(r"(?:eligibility|who can apply|criteria)[\s:]*\n?([^\n\.]{30,250}\.)", text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None

    @staticmethod
    def _extract_courses(text: str) -> Tuple[List[str], Optional[str]]:
        found = []
        snippet = None
        c_lower = text.lower()
        candidates = ["B.Tech", "B.E.", "BCA", "B.Sc", "M.Tech", "MCA", "M.Sc", "Diploma", "MBBS", "B.Com", "BA", "Engineering", "Technical"]
        for c in candidates:
            m = re.search(rf"\b{re.escape(c.lower())}\b", c_lower)
            if m:
                found.append(c)
                if not snippet:
                    start = max(0, m.start() - 20)
                    end = min(len(text), m.end() + 40)
                    snippet = text[start:end].strip()
        return found, snippet

    @staticmethod
    def _extract_years(text: str) -> Tuple[List[str], Optional[str]]:
        found = []
        snippet = None
        t = text.lower()
        if "1st year" in t or "first year" in t or "fresher" in t:
            found.append("1st Year")
            snippet = "1st Year / Fresher mentioned in criteria"
        if "2nd year" in t or "second year" in t:
            found.append("2nd Year")
            snippet = "2nd Year mentioned in criteria"
        if "3rd year" in t or "third year" in t:
            found.append("3rd Year")
        if "4th year" in t or "final year" in t:
            found.append("4th Year")
        if "renewal" in t and not found:
            found.extend(["2nd Year", "3rd Year", "4th Year"])
            snippet = "Renewal students criteria"
        if not found and ("post-matric" in t or "undergraduate" in t or "degree" in t):
            found.extend(["1st Year", "2nd Year", "3rd Year", "4th Year"])
            snippet = "Post-Matric / Undergraduate degree level"
        return found, snippet

    @staticmethod
    def _extract_states(text: str, domain: str, title: str) -> Tuple[List[str], Optional[str]]:
        found = []
        snippet = None
        combined = (title + " " + text).lower()
        all_states = [
            "Karnataka", "Maharashtra", "Tamil Nadu", "Telangana", "Andhra Pradesh",
            "Uttar Pradesh", "Delhi", "Kerala", "Gujarat", "West Bengal", "Rajasthan",
            "Madhya Pradesh", "Bihar", "Punjab", "Haryana", "Odisha", "Assam"
        ]
        for st in all_states:
            m = re.search(rf"\b{re.escape(st.lower())}\b", combined)
            if m:
                found.append(st)
                if not snippet:
                    snippet = f"State explicitly referenced: {st}"

        if "karnataka" in domain and "Karnataka" not in found:
            found.append("Karnataka")
            snippet = "Karnataka State portal domain authority"

        if "scholarships.gov.in" in domain or "all india" in combined or "central" in combined or not found:
            if "All India / Central" not in found:
                found.append("All India / Central")
                if not snippet:
                    snippet = "Central / National portal scheme open across all states"

        return found, snippet

    @staticmethod
    def _extract_categories(text: str, title: str) -> Tuple[List[str], Optional[str]]:
        found = []
        snippet = None
        combined = (title + " " + text).lower()
        if re.search(r"\b(sc|scheduled caste)\b", combined):
            found.append("SC")
            snippet = "Scheduled Caste criteria detected"
        if re.search(r"\b(st|scheduled tribe)\b", combined):
            found.append("ST")
            snippet = "Scheduled Tribe criteria detected"
        if re.search(r"\b(obc|backward classes?|category 1|category 2a|category 3a)\b", combined):
            found.append("OBC")
            snippet = "OBC / Backward Classes criteria detected"
        if re.search(r"\b(ews|economically weaker)\b", combined):
            found.append("EWS")
            snippet = "EWS criteria detected"
        if re.search(r"\b(pwd|physically disabled|specially abled|saksham)\b", combined):
            found.append("PWD / Specially Abled")
            snippet = "Specially abled (PWD) reservation detected"
        if re.search(r"\b(girls?|women|pragati)\b", combined):
            found.append("Girl Students")
            snippet = "Girl students quota/scheme detected"
        if re.search(r"\b(general|open category)\b", combined) or not found:
            found.append("General")
            if not snippet:
                snippet = "Open to general category or universal allocation"
        return found, snippet

    @staticmethod
    def _extract_income_with_evidence(text: str) -> Tuple[Optional[float], Optional[str]]:
        max_income = extract_income_ceiling(text)
        if max_income:
            # Locate snippet
            m = re.search(rf"(\S+\s+){{0,3}}(?:income|ceiling|not exceeding|up to)[^\.\n]{{5,60}}(\S+\s+){{0,3}}", text, re.IGNORECASE)
            snippet = m.group(0).strip() if m else f"Income limit: ₹{max_income:,.0f}"
            return max_income, snippet
        return None, None

    @staticmethod
    def _extract_amount_with_evidence(text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract scholarship award/grant amount while guarding against income ceilings and clause numbers."""
        # 1. Check for explicit scholarship award / financial assistance phrases
        award_match = re.search(
            r"(?:scholarship|assistance|grant|stipend|award|allowance|maintenance allowance)[\s\w:]*?(?:of|is|worth|upto|up to)?\s*(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?(?:\s*(?:lakh|lakhs|thousand))?(?:\s*(?:per annum|per month|p\.m\.|p\.a\.|\/year|\/month))?)",
            text,
            re.IGNORECASE
        )
        if award_match:
            val = f"₹{award_match.group(1).strip()}"
            return val, award_match.group(0).strip()

        # 2. General rupee amounts (require 4+ digits e.g. ₹5,000 to avoid matching clause numbers or income fractions)
        amt_match = re.search(r"(?:₹|rs\.?|inr)\s*([\d,]{4,}(?:\.\d+)?(?:\s*(?:per annum|per year|\/year|p\.a\.))?)", text, re.IGNORECASE)
        if amt_match:
            val = f"₹{amt_match.group(1).strip()}"
            snippet = amt_match.group(0).strip()
            return val, snippet

        lakh_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lakhs)\s*(?:per year|p\.a\.|\/year|scholarship|grant)", text, re.IGNORECASE)
        if lakh_match:
            val = f"₹{lakh_match.group(1)} Lakhs"
            snippet = lakh_match.group(0).strip()
            return val, snippet

        if "tuition fee waiver" in text.lower() or "fee concession" in text.lower():
            return "Tuition Fee Concession", "Tuition fee waiver / concession mentioned"

        return None, None

    @staticmethod
    def _extract_deadline_with_evidence(text: str) -> Tuple[Optional[str], Optional[str], bool]:
        """Extract application closing date and check if it is already expired."""
        deadline = None
        snippet = None
        is_expired = False
        today_ist = get_current_ist_time().date()

        # Look for explicit closing dates like "Student Application Open till : 31-10-2026" or "Last date: 31/10/2026"
        date_pattern = r"(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{4}|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2})"
        deadline_match = re.search(rf"(?:open till|last date|closing date|deadline|end date)[\s\w:]*?{date_pattern}", text, re.IGNORECASE)
        if deadline_match:
            raw_d = deadline_match.group(1).strip()
            parsed_dt = parse_date_string(raw_d)
            if parsed_dt:
                deadline = parsed_dt.strftime("%Y-%m-%d")
                snippet = deadline_match.group(0).strip()
                if parsed_dt.date() < today_ist:
                    is_expired = True

        # Text date fallback (e.g. 31st October 2026)
        if not deadline:
            text_date_match = re.search(r"(?:open till|last date|closing date|deadline)[\s\w:]*?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})", text, re.IGNORECASE)
            if text_date_match:
                parsed_dt = parse_date_string(text_date_match.group(1))
                if parsed_dt:
                    deadline = parsed_dt.strftime("%Y-%m-%d")
                    snippet = text_date_match.group(0).strip()
                    if parsed_dt.date() < today_ist:
                        is_expired = True

        return deadline, snippet, is_expired

    @staticmethod
    def _extract_application_link(
        content: str,
        links: List[str],
        current_url: str,
    ) -> Tuple[Optional[str], Optional[str]]:
        """Identify genuine application destination, prioritizing official portals."""
        # 1. Search in links
        for l in links:
            l_str = l.strip() if isinstance(l, str) else ""
            if not is_safe_url(l_str):
                continue
            lower = l_str.lower()
            if any(term in lower for term in ["registration", "login", "apply", "postmatric", "student_login"]):
                return l_str, f"Outbound portal link: {l_str}"

        # 2. Search markdown links e.g. [Apply Online](https://...)
        md_match = re.search(r"\[(?:apply online|apply now|portal link|official link|registration)\]\((https?:\/\/[^\s\)]+)\)", content, re.IGNORECASE)
        if md_match:
            cand = md_match.group(1).strip()
            if is_safe_url(cand):
                return cand, f"Markdown apply link: {cand}"

        # 3. If current URL is already a specific portal apply/login URL
        if any(p in current_url.lower() for p in ["postmatric", "login", "registration", "apply"]):
            return current_url, f"Direct application page: {current_url}"

        # If it's a directory or general source page without a confirmed apply portal, return None
        return None, None

    @staticmethod
    def _determine_status(text: str, deadline: Optional[str]) -> str:
        t = text.lower()
        if "applications are open" in t or "portal open" in t or "receiving fresh applications" in t:
            return "Open"
        if "applications closed" in t or "portal closed" in t or "last date has expired" in t:
            return "Closed"
        if deadline:
            parsed = parse_date_string(deadline)
            if parsed:
                if parsed.date() < get_current_ist_time().date():
                    return "Closed"
                else:
                    return "Open"
        return "Needs verification"

    # Backward compatibility method
    @staticmethod
    def extract_scholarship(
        search_item: Dict[str, Any],
        fetch_content: str = "",
        fetch_links: Optional[List[str]] = None,
        agent_data: Any = None,
        method: str = "TinyFish Fetch",
    ) -> ScholarshipOpportunity:
        """Backward-compatible extraction method returning a single ScholarshipOpportunity."""
        opps = ScholarshipExtractor.extract_opportunities(
            search_item=search_item,
            fetch_content=fetch_content,
            fetch_links=fetch_links,
            agent_data=agent_data,
            method=method,
        )
        if opps:
            return opps[0]

        # Fallback if no specific scheme was found
        url = search_item.get("url", "")
        trust = classify_domain_trust(url)
        return ScholarshipOpportunity(
            scheme_id=f"sch_{abs(hash(url)) % 1000000:06d}",
            scheme_name=search_item.get("title") or f"{trust['domain']} Scholarship",
            provider=trust.get("tier", "Official Authority"),
            source_url=url,
            application_status="Needs verification",
            verification_status="unverified",
        )
