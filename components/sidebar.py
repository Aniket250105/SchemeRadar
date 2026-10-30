import streamlit as st
from utils.helpers import render_html

def render_sidebar():
    """Render the official TinyFish-branded editorial sidebar navigation in Lagoon (#00343B)."""
    with st.sidebar:
        brand_header_html = """
        <div style="padding: 1.2rem 0 1rem 0; border-bottom: 1px solid rgba(218, 218, 207, 0.18); margin-bottom: 1.4rem;">
            <div style="display: flex; align-items: baseline; gap: 6px;">
                <span style="font-family: 'Inter', -apple-system, sans-serif; font-size: 1.35rem; font-weight: 900; color: #F8F8F2; letter-spacing: -0.03em;">SCHEME<span style="color: #FF6700;">RADAR</span></span>
                <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #FF6700;"></span>
            </div>
            <div style="font-family: 'IBM Plex Mono', monospace, monospace; font-size: 0.65rem; color: #E9E9DC; opacity: 0.75; letter-spacing: 0.08em; text-transform: uppercase; margin-top: 4px;">
                Scholarship Discovery &amp; Provenance
            </div>
        </div>
        """
        render_html(brand_header_html)

        # Navigation menu
        pages = [
            ("Dashboard", "Dashboard"),
            ("Find Scholarships", "Find Scholarships"),
            ("My Matches", "My Matches"),
            ("Scam Checker", "Is This Real?"),
            ("About SchemeRadar", "About SchemeRadar"),
        ]

        if "current_page" not in st.session_state:
            st.session_state.current_page = "Dashboard"

        nav_title_html = """
        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; text-transform: uppercase; color: #E9E9DC; opacity: 0.65; letter-spacing: 0.1em; margin-bottom: 0.5rem; padding-left: 2px;">
            Workspace
        </div>
        """
        render_html(nav_title_html)
        
        for label, page_key in pages:
            is_active = st.session_state.current_page == page_key
            if st.button(
                label,
                key=f"nav_{page_key}",
                use_container_width=True,
                type="primary" if is_active else "secondary"
            ):
                st.session_state.current_page = page_key
                st.rerun()

        # Student Profile Snapshot Card in Sidebar
        profile = st.session_state.get("student_profile")
        if profile:
            profile_snapshot_html = f"""
            <div style="background: rgba(0, 0, 0, 0.22); border: 1px solid rgba(218, 218, 207, 0.15); border-radius: 6px; padding: 0.85rem; margin-top: 1.8rem;">
                <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; text-transform: uppercase; color: #FECB8B; letter-spacing: 0.08em; font-weight: 600;">
                    Active Student Profile
                </div>
                <div style="color: #F8F8F2; font-size: 0.88rem; font-weight: 700; margin-top: 4px;">
                    {profile.course} &middot; {profile.academic_year}
                </div>
                <div style="color: #E9E9DC; font-size: 0.76rem; opacity: 0.85; margin-top: 2px;">
                    {profile.state_of_domicile} &middot; {profile.category}
                </div>
                <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; color: #E7FF84; margin-top: 4px;">
                    {profile.family_income_band}
                </div>
            </div>
            """
            render_html(profile_snapshot_html)

        # TinyFish Engine Indicator
        client = st.session_state.get("tinyfish_client")
        is_active = bool(client and client.is_configured)
        status_dot = "#1B7064" if is_active else "#FF6700"
        status_label = "Online & Connected" if is_active else "Configure API Key"

        tf_indicator_html = f"""
        <div style="margin-top: 1.5rem; padding-top: 1.2rem; border-top: 1px solid rgba(218, 218, 207, 0.15);">
            <div style="display: flex; align-items: center; justify-content: space-between;">
                <span style="font-family: 'IBM Plex Mono', monospace; font-size: 0.62rem; text-transform: uppercase; letter-spacing: 0.08em; color: #E9E9DC; opacity: 0.7;">
                    POWERED BY TINYFISH
                </span>
                <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: {status_dot};"></span>
            </div>
            <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; color: #F8F8F2; margin-top: 3px;">
                {status_label}
            </div>
        </div>
        """
        render_html(tf_indicator_html)

    return st.session_state.current_page
