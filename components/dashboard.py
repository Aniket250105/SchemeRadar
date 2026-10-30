import streamlit as st
from typing import List, Optional
from core.models import MatchResult, SourcePage, TinyFishLogEntry
from components.scholarship_card import render_scholarship_card
from utils.helpers import render_html

def render_dashboard(
    matches: List[MatchResult],
    metrics: dict,
    profile_state: str = "Karnataka",
    source_pages: Optional[List[SourcePage]] = None,
    activity_log: Optional[List[TinyFishLogEntry]] = None,
):
    """Render the official TinyFish-branded Swiss editorial dashboard."""

    # 1. Editorial Header
    profile = st.session_state.get("student_profile")
    course_str = f"{profile.course} ({profile.academic_year})" if profile else "Undergraduate"
    cat_str = f"{profile.category} Category" if profile else "General"
    income_str = profile.family_income_band if profile else "Standard Band"

    header_col1, header_col2 = st.columns([3, 1])
    with header_col1:
        header_html = f"""
        <div style="margin-bottom: 1.5rem;">
            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; color: #FF6700; font-weight: 700; margin-bottom: 0.4rem;">
                Official Scholarship &amp; Scheme Intelligence
            </div>
            <h1 style="font-family: 'Inter', -apple-system, sans-serif; font-size: 2.2rem; font-weight: 900; color: #171717; letter-spacing: -0.03em; margin: 0 0 0.4rem 0; line-height: 1.15;">
                Find funding for your next step.
            </h1>
            <p style="font-size: 1rem; color: #444440; margin: 0; line-height: 1.5; max-width: 720px;">
                Discover verified scholarships and state schemes matched against your academic profile. Powered by autonomous TinyFish web agents.
            </p>
            <div style="display: flex; gap: 1.2rem; align-items: center; margin-top: 0.9rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.74rem; color: #666660;">
                <span>DOMICILE: <strong style="color: #171717;">{profile_state}</strong></span>
                <span>&middot;</span>
                <span>ACADEMIC: <strong style="color: #171717;">{course_str}</strong></span>
                <span>&middot;</span>
                <span>CRITERIA: <strong style="color: #171717;">{cat_str} ({income_str})</strong></span>
            </div>
        </div>
        """
        render_html(header_html)
    with header_col2:
        st.markdown("<div style='height: 1.4rem;'></div>", unsafe_allow_html=True)
        if st.button("Find scholarships →", type="primary", use_container_width=True):
            st.session_state.current_page = "Find Scholarships"
            st.rerun()

    # 2. Horizontal Metrics with Fine Dividers (Swiss Layout)
    m_sources = metrics.get('total_sources', 0)
    m_extracted = metrics.get('total_extracted', 0)
    m_verified = metrics.get('verified_open', 0)
    m_closing = metrics.get('closing_soon', 0)

    metrics_html = f"""
    <div style="background: #FFFFFF; border: 1px solid #DADACF; border-radius: 6px; padding: 1.2rem 1.5rem; margin-bottom: 2rem; display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem;">
        <div style="border-right: 1px solid #DADACF; padding-right: 1rem;">
            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: #777770; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;">
                01 &mdash; Sources Discovered
            </div>
            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 2.2rem; font-weight: 800; color: #171717; margin-top: 0.2rem; line-height: 1.1;">
                {m_sources}
            </div>
            <div style="font-size: 0.74rem; color: #666660; margin-top: 0.3rem;">
                Official state &amp; central portals
            </div>
        </div>
        <div style="border-right: 1px solid #DADACF; padding-right: 1rem;">
            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: #777770; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;">
                02 &mdash; Schemes Extracted
            </div>
            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 2.2rem; font-weight: 800; color: #171717; margin-top: 0.2rem; line-height: 1.1;">
                {m_extracted}
            </div>
            <div style="font-size: 0.74rem; color: #666660; margin-top: 0.3rem;">
                Discrete opportunities parsed
            </div>
        </div>
        <div style="border-right: 1px solid #DADACF; padding-right: 1rem;">
            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: #777770; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;">
                03 &mdash; Verified Open
            </div>
            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 2.2rem; font-weight: 800; color: #1B7064; margin-top: 0.2rem; line-height: 1.1;">
                {m_verified}
            </div>
            <div style="font-size: 0.74rem; color: #1B7064; margin-top: 0.3rem; font-weight: 600;">
                Active application windows
            </div>
        </div>
        <div>
            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: #777770; text-transform: uppercase; letter-spacing: 0.08em; font-weight: 600;">
                04 &mdash; Closing Soon
            </div>
            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 2.2rem; font-weight: 800; color: #FF6700; margin-top: 0.2rem; line-height: 1.1;">
                {m_closing}
            </div>
            <div style="font-size: 0.74rem; color: #FF6700; margin-top: 0.3rem; font-weight: 600;">
                Action recommended
            </div>
        </div>
    </div>
    """
    render_html(metrics_html)

    # 3. Featured Opportunity Section
    if matches:
        top_match = matches[0]
        top_sch = top_match.scholarship
        amount_disp = top_sch.amount or "Norm-based award"
        deadline_disp = top_sch.deadline or "Check official notice"
        
        featured_html = f"""
        <div style="background: #FFFFFF; border: 1px solid #DADACF; border-top: 3px solid #FF6700; border-radius: 6px; padding: 1.4rem 1.6rem; margin-bottom: 2rem;">
            <div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 0.8rem; margin-bottom: 0.6rem;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="background: #E7FF84; color: #171717; font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; font-weight: 800; padding: 2px 8px; border-radius: 3px; text-transform: uppercase; letter-spacing: 0.06em;">
                        Top Match &middot; {int(top_match.relevance_score)}% Compatibility
                    </span>
                    <span style="font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; color: #1B7064; font-weight: 700;">
                        [{top_match.eligibility_status.upper()}]
                    </span>
                </div>
                <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem; color: #555550;">
                    Deadline: <strong style="color: #171717;">{deadline_disp}</strong>
                </div>
            </div>
            <h3 style="font-family: 'Inter', -apple-system, sans-serif; font-size: 1.25rem; font-weight: 800; color: #171717; margin: 0 0 0.3rem 0; line-height: 1.3;">
                {top_sch.scheme_name}
            </h3>
            <div style="font-size: 0.82rem; color: #666660; margin-bottom: 0.8rem;">
                {top_sch.provider or 'National Scholarship Authority'}
            </div>
            <div style="display: flex; align-items: baseline; gap: 1.5rem; background: #F8F8F2; border: 1px solid #DADACF; border-radius: 4px; padding: 0.75rem 1rem; margin-bottom: 1rem;">
                <div>
                    <span style="font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; text-transform: uppercase; color: #777770; display: block;">Scholarship Award</span>
                    <span style="font-family: 'IBM Plex Mono', monospace; font-size: 1.15rem; font-weight: 800; color: #1B7064;">{amount_disp}</span>
                </div>
                <div style="border-left: 1px solid #DADACF; padding-left: 1.2rem;">
                    <span style="font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; text-transform: uppercase; color: #777770; display: block;">Eligibility Basis</span>
                    <span style="font-size: 0.82rem; color: #171717; font-weight: 600;">{top_match.why_this_matches_you[:95]}...</span>
                </div>
            </div>
        </div>
        """
        render_html(featured_html)

    # 4. Discovered Sources & Portals (Clean Editorial Expandable Table)
    if source_pages:
        with st.expander(f"Discovered Portals &amp; Source Directories ({len(source_pages)})", expanded=False):
            st.caption("Individual schemes are extracted from official directories and validated separately.")
            for sp in source_pages:
                status_color = "#1B7064" if sp.fetch_status == "success" else ("#FF6700" if sp.fetch_status == "proxy_error" else "#777770")
                source_row_html = f"""
                <div style="background: #FFFFFF; border: 1px solid #DADACF; border-radius: 4px; padding: 0.8rem 1rem; margin-bottom: 0.45rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                    <div>
                        <strong style="color: #171717; font-size: 0.88rem;">{sp.website_name}</strong> &nbsp;
                        <span style="font-family: 'IBM Plex Mono', monospace; font-size: 0.68rem; color: #666660; background: #F8F8F2; border: 1px solid #DADACF; padding: 1px 6px; border-radius: 3px;">
                            {sp.authority_level}
                        </span>
                        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #777770; margin-top: 2px;">
                            URL: <a href="{sp.source_url}" target="_blank" style="color: #FF6700; text-decoration: none;">{sp.source_url}</a>
                        </div>
                    </div>
                    <div style="text-align: right; font-family: 'IBM Plex Mono', monospace; font-size: 0.74rem;">
                        <span style="color: {status_color}; font-weight: 700; text-transform: uppercase;">{sp.fetch_status}</span>
                        <div style="color: #888880; font-size: 0.68rem;">Checked: {sp.last_checked}</div>
                    </div>
                </div>
                """
                render_html(source_row_html)

    # 5. TinyFish Live Activity Log
    if activity_log:
        with st.expander(f"TinyFish Execution Audit Trail ({len(activity_log)} events)", expanded=False):
            st.caption("Verifiable record of Search, Fetch, and Agent SSE operations executed against TinyFish endpoints:")
            for entry in reversed(activity_log):
                op_color = "#1B7064" if entry.operation == "FETCH" else ("#FF6700" if entry.operation == "AGENT" else "#00343B")
                st_color = "#1B7064" if entry.status in ("SUCCESS", "COMPLETED") else ("#FF6700" if "ERROR" in entry.status or "FAIL" in entry.status else "#777770")
                
                log_row_html = f"""
                <div style="background: #FFFFFF; border: 1px solid #DADACF; border-left: 3px solid {op_color}; border-radius: 4px; padding: 0.55rem 0.85rem; margin-bottom: 0.4rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.78rem;">
                    <span style="font-weight: 800; color: {op_color}; margin-right: 8px;">{entry.operation}</span>
                    <span style="color: #888880;">[{entry.timestamp}]</span>
                    <span style="font-weight: 700; color: {st_color}; margin: 0 8px;">{entry.status}</span>
                    <span style="color: #171717;">{entry.target[:60]}</span>
                    <div style="color: #666660; font-size: 0.72rem; margin-top: 2px;">
                        &rsaquo; {entry.details}
                    </div>
                </div>
                """
                render_html(log_row_html)

    if not matches:
        empty_html = """
        <div style="background: #FFFFFF; border: 1px dashed #DADACF; border-radius: 6px; padding: 3rem 2rem; text-align: center; margin: 2rem 0;">
            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.08em; color: #777770; margin-bottom: 0.5rem;">
                No Scholarship Records in Local Workspace
            </div>
            <h3 style="font-family: 'Inter', sans-serif; font-size: 1.35rem; font-weight: 800; color: #171717; margin: 0 0 0.5rem 0;">
                Begin your personalized discovery
            </h3>
            <p style="font-size: 0.92rem; color: #666660; max-width: 500px; margin: 0 auto 1.5rem auto; line-height: 1.5;">
                Configure your academic degree, year, and domicile to scan official Indian central and state government scholarship portals.
            </p>
        </div>
        """
        render_html(empty_html)
        if st.button("Configure Profile & Discover Schemes →", type="primary", use_container_width=True):
            st.session_state.current_page = "Find Scholarships"
            st.rerun()
        return

    # 6. Filter & Sort Control Bar
    with st.container(border=True):
        fc1, fc2, fc3, fc4 = st.columns([2, 2, 2, 2])
        with fc1:
            status_filter = st.selectbox(
                "Application Status",
                options=["All Statuses", "Open", "Closing soon", "Needs verification", "Closed"],
                index=0
            )
        with fc2:
            elig_filter = st.selectbox(
                "Eligibility Filter",
                options=["All Matches", "Eligible Only", "Potential Matches", "Ineligible"],
                index=0
            )
        with fc3:
            sort_by = st.selectbox(
                "Sort Results",
                options=["Highest match", "Deadline approaching", "Highest scholarship amount"],
                index=0
            )
        with fc4:
            only_official = st.checkbox(
                "Strictly Official (.gov/.nic)",
                value=False,
                help="Filter only domains ending with .gov.in, .nic.in, or .ac.in"
            )

    # Apply Filters
    filtered = []
    for m in matches:
        if status_filter != "All Statuses" and m.scholarship.application_status != status_filter:
            continue
        if elig_filter == "Eligible Only" and m.eligibility_status != "Eligible":
            continue
        if elig_filter == "Potential Matches" and m.eligibility_status != "Potential match":
            continue
        if elig_filter == "Ineligible" and m.eligibility_status != "Ineligible":
            continue
        if only_official:
            domain = (m.scholarship.source_domain or "").lower()
            if not any(d in domain for d in [".gov.in", ".nic.in", ".ac.in", ".edu.in"]):
                continue
        filtered.append(m)

    count_html = f"""
    <div style="display: flex; justify-content: space-between; align-items: baseline; margin: 1.5rem 0 1rem 0; padding-bottom: 0.5rem; border-bottom: 1px solid #DADACF;">
        <span style="font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; text-transform: uppercase; color: #777770; letter-spacing: 0.08em; font-weight: 700;">
            Evaluated Opportunities ({len(filtered)})
        </span>
        <span style="font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #888880;">
            Ranked by {sort_by}
        </span>
    </div>
    """
    render_html(count_html)

    # Render Scholarship Listings
    for idx, match in enumerate(filtered):
        render_scholarship_card(match, index=idx)
