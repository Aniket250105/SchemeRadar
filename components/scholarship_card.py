import streamlit as st
from core.models import MatchResult
from utils.helpers import classify_domain_trust, render_html

def render_scholarship_card(match: MatchResult, index: int = 0):
    """Render an editorial-style, Swiss typography scholarship listing item in the official TinyFish palette."""
    sch = match.scholarship
    relevance = int(match.relevance_score)
    confidence = int(match.eligibility_confidence * 100)
    trust = classify_domain_trust(sch.source_url)

    # 1. Status Labels (Typographic, No Emojis)
    elig_status = match.eligibility_status.upper()
    if elig_status == "ELIGIBLE":
        elig_badge = '<span style="font-family: \'IBM Plex Mono\', monospace; font-size: 0.65rem; font-weight: 700; color: #1B7064; background: rgba(27, 112, 100, 0.1); border: 1px solid #1B7064; padding: 2px 7px; border-radius: 3px; letter-spacing: 0.06em;">ELIGIBLE</span>'
    elif elig_status == "INELIGIBLE":
        elig_badge = '<span style="font-family: \'IBM Plex Mono\', monospace; font-size: 0.65rem; font-weight: 700; color: #FF6700; background: rgba(255, 103, 0, 0.1); border: 1px solid #FF6700; padding: 2px 7px; border-radius: 3px; letter-spacing: 0.06em;">INELIGIBLE</span>'
    else:
        elig_badge = '<span style="font-family: \'IBM Plex Mono\', monospace; font-size: 0.65rem; font-weight: 700; color: #171717; background: #E9E9DC; border: 1px solid #DADACF; padding: 2px 7px; border-radius: 3px; letter-spacing: 0.06em;">POTENTIAL MATCH</span>'

    app_status = sch.application_status.upper()
    if app_status in ("OPEN", "ACTIVE"):
        app_badge = '<span style="font-family: \'IBM Plex Mono\', monospace; font-size: 0.65rem; font-weight: 700; color: #1B7064; background: rgba(27, 112, 100, 0.1); padding: 2px 7px; border-radius: 3px; letter-spacing: 0.06em;">OPEN</span>'
    elif app_status == "CLOSING SOON":
        app_badge = '<span style="font-family: \'IBM Plex Mono\', monospace; font-size: 0.65rem; font-weight: 700; color: #171717; background: #FECB8B; padding: 2px 7px; border-radius: 3px; letter-spacing: 0.06em;">CLOSING SOON</span>'
    elif app_status == "CLOSED":
        app_badge = '<span style="font-family: \'IBM Plex Mono\', monospace; font-size: 0.65rem; font-weight: 700; color: #888880; background: #E9E9DC; padding: 2px 7px; border-radius: 3px; letter-spacing: 0.06em;">CLOSED</span>'
    else:
        app_badge = '<span style="font-family: \'IBM Plex Mono\', monospace; font-size: 0.65rem; font-weight: 700; color: #666660; background: #E9E9DC; padding: 2px 7px; border-radius: 3px; letter-spacing: 0.06em;">NEEDS VERIFICATION</span>'

    urgency_badge = ""
    if match.urgency == "Urgent":
        urgency_badge = '<span style="font-family: \'IBM Plex Mono\', monospace; font-size: 0.65rem; font-weight: 700; color: #FFFFFF; background: #FF6700; padding: 2px 7px; border-radius: 3px; letter-spacing: 0.06em;">&lt; 7 DAYS REMAINING</span>'

    authority_badge = f'<span style="font-family: \'IBM Plex Mono\', monospace; font-size: 0.65rem; font-weight: 600; color: #444440; background: #F8F8F2; border: 1px solid #DADACF; padding: 2px 7px; border-radius: 3px;">{trust["authority_level"]}</span>'

    deadline_text = sch.deadline or "Date not published on circular"
    amount_text = sch.amount or "Norm-based award"
    provider_text = sch.provider or "Official Scholarship Authority"

    # 2. Main Listing Surface
    card_html = f"""
    <div style="background: #FFFFFF; border: 1px solid #DADACF; border-radius: 6px; padding: 1.4rem 1.6rem; margin-bottom: 1.4rem;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.8rem; margin-bottom: 0.8rem;">
            <div style="flex: 1; min-width: 280px;">
                <div style="display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 0.5rem;">
                    {elig_badge}
                    {app_badge}
                    {urgency_badge}
                    {authority_badge}
                    <span style="font-family: \'IBM Plex Mono\', monospace; font-size: 0.65rem; color: #888880;">via {sch.extraction_method}</span>
                </div>
                <h3 style="font-family: 'Inter', -apple-system, sans-serif; font-size: 1.25rem; font-weight: 800; color: #171717; margin: 0 0 0.25rem 0; line-height: 1.35; letter-spacing: -0.02em;">
                    {sch.scheme_name}
                </h3>
                <div style="font-size: 0.84rem; color: #666660;">
                    {provider_text}
                </div>
            </div>
            
            <div style="text-align: right; background: #F8F8F2; border: 1px solid #DADACF; border-radius: 4px; padding: 0.5rem 0.9rem; min-width: 100px;">
                <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; font-weight: 700; color: #777770; text-transform: uppercase; letter-spacing: 0.08em;">Compatibility</div>
                <div style="font-family: 'IBM Plex Mono', monospace; font-size: 1.45rem; font-weight: 800; color: #171717; line-height: 1.1;">{relevance}%</div>
                <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: #1B7064; font-weight: 600;">{confidence}% verified</div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; background: #F8F8F2; border: 1px solid #DADACF; padding: 0.85rem 1.1rem; border-radius: 4px; margin: 1rem 0; font-size: 0.85rem;">
            <div>
                <span style="font-family: 'IBM Plex Mono', monospace; color: #777770; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; display: block; margin-bottom: 2px;">Scholarship Award</span>
                <strong style="font-family: 'IBM Plex Mono', monospace; color: #1B7064; font-size: 0.95rem;">{amount_text}</strong>
            </div>
            <div>
                <span style="font-family: 'IBM Plex Mono', monospace; color: #777770; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; display: block; margin-bottom: 2px;">Deadline</span>
                <strong style="font-family: 'IBM Plex Mono', monospace; color: #171717; font-size: 0.95rem;">{deadline_text}</strong>
            </div>
            <div>
                <span style="font-family: 'IBM Plex Mono', monospace; color: #777770; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; display: block; margin-bottom: 2px;">Eligible Domicile</span>
                <strong style="color: #171717;">{', '.join(sch.eligible_states) if sch.eligible_states else 'All India / Central'}</strong>
            </div>
            <div>
                <span style="font-family: 'IBM Plex Mono', monospace; color: #777770; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; display: block; margin-bottom: 2px;">Social Category</span>
                <strong style="color: #171717;">{', '.join(sch.eligible_categories) if sch.eligible_categories else 'Open to all'}</strong>
            </div>
        </div>

        <div style="border-left: 3px solid #1B7064; background: #F8F8F2; padding: 0.7rem 0.9rem; border-radius: 0 4px 4px 0; margin: 0.85rem 0; font-size: 0.85rem; color: #333330; line-height: 1.45;">
            <strong style="font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; text-transform: uppercase; color: #1B7064; letter-spacing: 0.05em; display: inline-block; margin-right: 6px;">Evaluation:</strong> {match.why_this_matches_you}
        </div>
    </div>
    """
    render_html(card_html)

    # Missing Criteria Note
    if match.missing_criteria:
        missing_html = f"""
        <div style="background: rgba(254, 203, 139, 0.2); border-left: 3px solid #FF6700; padding: 0.6rem 0.85rem; border-radius: 0 4px 4px 0; margin-bottom: 0.75rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.74rem; color: #171717;">
            <strong>UNVERIFIED FIELDS ON NOTICE:</strong> {'; '.join(match.missing_criteria)}
        </div>
        """
        render_html(missing_html)

    # Expandable Provenance Audit
    with st.expander(f"Review eligibility provenance &amp; verification audit ({sch.scheme_name[:35]}...)", expanded=False):
        c_left, c_right = st.columns([1, 1])
        with c_left:
            st.markdown("**Eligibility Criteria Summary**")
            st.write(sch.eligibility or sch.description or "Standard official guidelines apply. Student must be enrolled in recognized degree program.")
            
            if sch.eligible_courses:
                st.markdown(f"**Eligible Degrees:** `{', '.join(sch.eligible_courses)}`")
            if sch.income_limit is not None:
                st.markdown(f"**Max Family Income:** `₹{sch.income_limit:,.0f} per annum`")
            else:
                st.markdown("**Max Family Income:** *Not published on this notice (needs verification)*")

        with c_right:
            st.markdown("**Match Scoring Breakdown**")
            for factor, pts in match.score_breakdown.items():
                st.caption(f"• {factor}: **{pts} pts**")
                
            if match.rejection_reasons:
                st.markdown("**Ineligibility Conflict:**")
                for r in match.rejection_reasons:
                    st.caption(f"&times; {r}")

        # Field-Level Provenance Table
        if sch.evidence:
            st.markdown("##### Field-Level Provenance Tracking")
            for f_name, ev in sch.evidence.items():
                if isinstance(ev, dict):
                    v_val = ev.get("value")
                    v_status = ev.get("verification_status", "unverified")
                    v_snip = ev.get("evidence_snippet") or "No direct snippet"
                    
                    status_color = "#1B7064" if v_status == "direct_page_verified" else ("#171717" if v_status == "search_snippet_only" else "#FF6700")

                    provenance_row_html = f"""
                    <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.74rem; border-bottom: 1px solid #DADACF; padding: 4px 0; display: flex; align-items: baseline; flex-wrap: wrap; gap: 8px;">
                        <span style="color: #171717; font-weight: 700; min-width: 130px;">{f_name.replace('_', ' ').title()}:</span>
                        <code style="background: #F8F8F2; color: #171717; padding: 1px 4px; border-radius: 3px; border: 1px solid #DADACF;">{str(v_val)[:35]}</code>
                        <span style="color: {status_color}; font-weight: 700; font-size: 0.68rem;">[{v_status}]</span>
                        <span style="color: #666660; font-size: 0.72rem;">&mdash; {v_snip[:75]}</span>
                    </div>
                    """
                    render_html(provenance_row_html)

            source_meta_html = f"""
            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; color: #777770; margin-top: 0.8rem;">
                Source URL: <a href="{sch.source_url}" target="_blank" style="color: #FF6700;">{sch.source_url}</a> &nbsp;|&nbsp; Last Verified: {sch.last_verified}
            </div>
            """
            render_html(source_meta_html)

    # Action Buttons: Distinguish Confirmed Application Portals vs Directory Sources
    b_col1, b_col2, b_col3 = st.columns([2, 2, 3])
    with b_col1:
        if sch.application_url and sch.application_url != sch.source_url:
            st.link_button(
                "Apply on official portal →",
                url=sch.application_url,
                use_container_width=True,
                type="primary",
                help=f"Direct official portal: {sch.application_url}"
            )
        else:
            st.link_button(
                "Visit official source notice →",
                url=sch.source_url,
                use_container_width=True,
                type="primary",
                help="Opens official portal notice or scholarship directory."
            )
    with b_col2:
        st.link_button(
            "Source Web Page",
            url=sch.source_url,
            use_container_width=True,
            help="Visit original webpage discovered by TinyFish."
        )
    with b_col3:
        if st.button("Audit in Scam Checker", key=f"verify_btn_{sch.scheme_id}_{index}"):
            st.session_state["scam_input_preset"] = f"{sch.scheme_name}\nApplication Portal: {sch.application_url or sch.source_url}"
            st.session_state["current_page"] = "Is This Real?"
            st.rerun()

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
