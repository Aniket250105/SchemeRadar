import os
import streamlit as st
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="SchemeRadar | Official Scholarship & Scheme Intelligence",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded",
)

try:
    from utils.helpers import render_html
except ImportError:
    try:
        from utils import render_html
    except ImportError:
        def render_html(html_str: str):
            if hasattr(st, "html"):
                st.html(html_str)
            else:
                clean_lines = [line.strip() for line in html_str.splitlines() if line.strip()]
                clean_html = " ".join(clean_lines)
                st.markdown(clean_html, unsafe_allow_html=True)

# Official TinyFish Brand Palette & Swiss Editorial CSS
# Brand Variables:
#   --tf-orange: #FF6700; (Orange Burst - Primary CTA, active nav, fine accents)
#   --tf-peach: #FECB8B;  (Peachy Tan - Deadline urgency, secondary warnings)
#   --tf-yellow: #E7FF84; (Mellow Yellow - High compatibility highlights)
#   --tf-emerald: #1B7064;(Emerald - Verified sources, eligible state, success)
#   --tf-lagoon: #00343B; (Lagoon - Sidebar, high-contrast panels, headers)
#   --tf-warm-grey: #E9E9DC; (Warm Grey - Primary canvas background)
# Supporting UI Neutrals:
#   --ink: #171717;       (Tiny Black - Body text, strong headlines)
#   --paper: #F8F8F2;     (Off-white card surface)
#   --surface: #FFFFFF;   (Pure white container surface)
#   --border: #DADACF;    (1px hairline borders)
global_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');

:root {
  --tf-orange: #FF6700;
  --tf-peach: #FECB8B;
  --tf-yellow: #E7FF84;
  --tf-emerald: #1B7064;
  --tf-lagoon: #00343B;
  --tf-warm-grey: #E9E9DC;

  --ink: #171717;
  --paper: #F8F8F2;
  --surface: #FFFFFF;
  --border: #DADACF;
}

/* Global Background & Typography */
.stApp {
    background-color: #E9E9DC !important;
    color: #171717 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}

/* Container Spacing */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 3.5rem !important;
    max-width: 1180px !important;
}

/* Sidebar Styling in Lagoon (#00343B) */
section[data-testid="stSidebar"] {
    background-color: #00343B !important;
    border-right: 1px solid rgba(218, 218, 207, 0.2) !important;
}

section[data-testid="stSidebar"] > div {
    background-color: #00343B !important;
}

/* Sidebar Buttons & Nav */
section[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #F8F8F2 !important;
    border: 1px solid transparent !important;
    text-align: left !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0.5rem 0.85rem !important;
    border-radius: 4px !important;
    transition: all 0.15s ease !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255, 255, 255, 0.08) !important;
    color: #FFFFFF !important;
    border-color: rgba(255, 255, 255, 0.15) !important;
}

/* Active Nav Button */
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: rgba(255, 103, 0, 0.15) !important;
    color: #FF6700 !important;
    border-left: 3px solid #FF6700 !important;
    border-top: 1px solid rgba(255, 103, 0, 0.25) !important;
    border-right: 1px solid rgba(255, 103, 0, 0.25) !important;
    border-bottom: 1px solid rgba(255, 103, 0, 0.25) !important;
    font-weight: 700 !important;
}

/* Main Area Primary Buttons (Orange Burst #FF6700) */
.stButton > button[kind="primary"] {
    background: #FF6700 !important;
    color: #FFFFFF !important;
    border: 1px solid #FF6700 !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    padding: 0.55rem 1.2rem !important;
    box-shadow: none !important;
    transition: background 0.15s ease !important;
}

.stButton > button[kind="primary"]:hover {
    background: #E65C00 !important;
    border-color: #E65C00 !important;
    color: #FFFFFF !important;
}

/* Main Area Secondary Buttons */
.stButton > button {
    background: #FFFFFF !important;
    color: #171717 !important;
    border: 1px solid #DADACF !important;
    border-radius: 4px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
}

.stButton > button:hover {
    border-color: #FF6700 !important;
    color: #FF6700 !important;
    background: #FFFFFF !important;
}

/* Link Buttons */
.stLinkButton > a {
    border-radius: 4px !important;
    font-weight: 700 !important;
    font-size: 0.86rem !important;
    box-shadow: none !important;
    transition: all 0.15s ease !important;
}

.stLinkButton > a[kind="primary"] {
    background: #FF6700 !important;
    color: #FFFFFF !important;
    border: 1px solid #FF6700 !important;
}

.stLinkButton > a[kind="primary"]:hover {
    background: #E65C00 !important;
    border-color: #E65C00 !important;
}

/* Inputs & Form Fields */
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {
    background-color: #FFFFFF !important;
    border: 1px solid #DADACF !important;
    color: #171717 !important;
    border-radius: 4px !important;
}

div[data-baseweb="select"] > div:hover,
div[data-baseweb="input"] > div:hover,
div[data-baseweb="textarea"] > div:hover {
    border-color: #FF6700 !important;
}

div[data-baseweb="menu"] {
    background-color: #FFFFFF !important;
    border: 1px solid #DADACF !important;
    color: #171717 !important;
    border-radius: 4px !important;
}

li[data-baseweb="menu-item"] {
    color: #171717 !important;
}

li[data-baseweb="menu-item"]:hover {
    background-color: #F8F8F2 !important;
    color: #FF6700 !important;
}

/* Expanders */
.streamlit-expanderHeader {
    background-color: #FFFFFF !important;
    border: 1px solid #DADACF !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    font-size: 0.88rem !important;
    color: #171717 !important;
}

div[data-testid="stExpander"] {
    border: none !important;
}

/* Progress bar */
.stProgress > div > div > div > div {
    background: #FF6700 !important;
}

/* Monospace Helpers */
.mono {
    font-family: 'IBM Plex Mono', monospace !important;
}
</style>
"""
render_html(global_css)

# Load configuration and services
from config.settings import TINYFISH_API_KEY
from services.tinyfish_client import TinyFishClient
from services.discovery import DiscoveryService
from core.models import StudentProfile
from core.scam_checker import ScamChecker
from components.sidebar import render_sidebar
from components.profile_form import render_profile_form
from components.dashboard import render_dashboard
from components.scholarship_card import render_scholarship_card

# Initialize session state variables
if "tinyfish_client" not in st.session_state:
    st.session_state.tinyfish_client = TinyFishClient()
if "discovery_service" not in st.session_state:
    st.session_state.discovery_service = DiscoveryService(st.session_state.tinyfish_client)
if "scam_checker" not in st.session_state:
    st.session_state.scam_checker = ScamChecker(st.session_state.tinyfish_client)
if "matches" not in st.session_state:
    st.session_state.matches = []
if "source_pages" not in st.session_state:
    st.session_state.source_pages = []
if "activity_log" not in st.session_state:
    st.session_state.activity_log = []
if "metrics" not in st.session_state:
    st.session_state.metrics = {
        "total_sources": 0,
        "total_extracted": 0,
        "verified_open": 0,
        "potential_matches": 0,
        "requiring_verification": 0,
        "total_discovered": 0,
        "closing_soon": 0,
    }
if "student_profile" not in st.session_state:
    # Default Karnataka B.Tech 2nd Year OBC profile
    st.session_state.student_profile = StudentProfile(
        course="B.Tech",
        academic_year="2nd Year",
        college_name="BMS College of Engineering",
        academic_performance="8.5 CGPA",
        state_of_domicile="Karnataka",
        category="OBC",
        family_income_band="₹1–2.5 lakh",
        interests=["Engineering", "Computer Science", "Technology"],
    )

# Render Sidebar Navigation
current_page = render_sidebar()

# -------------------------------------------------------------
# PAGE 1: DASHBOARD
# -------------------------------------------------------------
if current_page == "Dashboard":
    render_dashboard(
        st.session_state.matches,
        st.session_state.metrics,
        profile_state=st.session_state.student_profile.state_of_domicile,
        source_pages=st.session_state.source_pages,
        activity_log=st.session_state.activity_log or st.session_state.tinyfish_client.activity_log,
    )

# -------------------------------------------------------------
# PAGE 2: FIND SCHOLARSHIPS
# -------------------------------------------------------------
elif current_page == "Find Scholarships":
    find_banner_html = """
    <div style="background: #FFFFFF; border: 1px solid #DADACF; border-left: 4px solid #FF6700; border-radius: 6px; padding: 1.4rem 1.6rem; margin-bottom: 1.5rem;">
        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; color: #FF6700; font-weight: 700; margin-bottom: 0.2rem;">
            Web Intelligence Discovery
        </div>
        <h2 style="font-family: 'Inter', sans-serif; color: #171717; margin: 0; font-size: 1.6rem; font-weight: 900; letter-spacing: -0.02em;">
            Find Scholarships
        </h2>
        <p style="color: #555550; margin: 0.3rem 0 0 0; font-size: 0.95rem; line-height: 1.5;">
            Configure your parameters below. TinyFish Search queries state and central government portals, while Fetch and Agent APIs extract individual criteria.
        </p>
    </div>
    """
    render_html(find_banner_html)

    profile = render_profile_form()
    st.session_state.student_profile = profile

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    with st.container(border=True):
        c_btn, c_opt = st.columns([2, 1])
        with c_opt:
            max_sources = st.slider(
                "Sources to Deep-Process via TinyFish",
                min_value=2,
                max_value=6,
                value=3,
                help="Controls how many discovered URLs undergo full Markdown Fetch and Agent navigation."
            )
            enable_agent = st.checkbox(
                "Deploy TinyFish Agent SSE",
                value=True,
                help="Autonomously navigates dynamic government portals to extract structured schemas."
            )
            
        with c_btn:
            find_btn = st.button("Find scholarships →", type="primary", use_container_width=True)

    if find_btn:
        # Editorial 7-Step Live Execution Interface
        timeline_container = st.container(border=True)
        
        stages = [
            ("01", "Searching the web"),
            ("02", "Discovering official sources"),
            ("03", "Fetching website content"),
            ("04", "Navigating complex portals"),
            ("05", "Extracting scholarship information"),
            ("06", "Checking eligibility"),
            ("07", "Preparing matches"),
        ]

        progress_bar = st.progress(0)
        status_box = st.empty()

        def render_live_timeline(active_step_idx: int, current_message: str):
            timeline_items = []
            for idx, (num, name) in enumerate(stages):
                if idx < active_step_idx:
                    # Completed: Emerald
                    step_html = f"""
                    <div style="display: flex; align-items: center; gap: 8px; font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #1B7064; font-weight: 700; margin-bottom: 4px;">
                        <span style="color: #1B7064;">&check; {num}</span>
                        <span>{name}</span>
                    </div>
                    """
                elif idx == active_step_idx:
                    # Active: Orange Burst
                    step_html = f"""
                    <div style="display: flex; align-items: center; gap: 8px; font-family: 'IBM Plex Mono', monospace; font-size: 0.76rem; color: #FF6700; font-weight: 800; background: rgba(255, 103, 0, 0.08); padding: 4px 8px; border-radius: 4px; margin-bottom: 4px;">
                        <span>&rsaquo; {num}</span>
                        <span>{name}</span>
                        <span style="font-size: 0.68rem; opacity: 0.8;">&mdash; {current_message}</span>
                    </div>
                    """
                else:
                    # Pending: Muted Grey
                    step_html = f"""
                    <div style="display: flex; align-items: center; gap: 8px; font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #999990; margin-bottom: 4px;">
                        <span>&middot; {num}</span>
                        <span>{name}</span>
                    </div>
                    """
                timeline_items.append(step_html)

            live_panel_html = f"""
            <div style="background: #FFFFFF; padding: 1.2rem; border-radius: 4px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem; padding-bottom: 0.5rem; border-bottom: 1px solid #DADACF;">
                    <span style="font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: #FF6700; letter-spacing: 0.08em;">
                        TINYFISH EXECUTION IN PROGRESS
                    </span>
                    <span style="font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; color: #666660;">
                        TinySearch &middot; TinyFetch &middot; TinyAgent SSE
                    </span>
                </div>
                {''.join(timeline_items)}
            </div>
            """
            render_html(live_panel_html)

        def on_progress(message: str, pct: int):
            progress_bar.progress(pct)
            # Map pct to stage
            if pct <= 15:
                step_idx = 0
            elif pct <= 35:
                step_idx = 1
            elif pct <= 55:
                step_idx = 2
            elif pct <= 70:
                step_idx = 3
            elif pct <= 85:
                step_idx = 4
            elif pct < 100:
                step_idx = 5
            else:
                step_idx = 6

            with status_box:
                render_live_timeline(step_idx, message)

        with st.spinner("Executing TinyFish Web Discovery..."):
            result = st.session_state.discovery_service.discover(
                profile=profile,
                progress_callback=on_progress,
                max_sources_to_process=max_sources,
                enable_agent=enable_agent,
            )

        st.session_state.matches = result["matches"]
        st.session_state.source_pages = result.get("source_pages", [])
        st.session_state.metrics = result["metrics"]
        st.session_state.activity_log = result.get("activity_log", [])
        st.session_state.last_search_time = datetime.now().strftime("%I:%M %p")

        st.success(f"Discovered {result['metrics']['total_sources']} source portals and extracted {len(result['matches'])} validated scholarship opportunities.")
        
        # Display Matches
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        st.subheader("Discovered Opportunities")
        for idx, match in enumerate(result["matches"]):
            render_scholarship_card(match, index=idx)

# -------------------------------------------------------------
# PAGE 3: MY MATCHES
# -------------------------------------------------------------
elif current_page == "My Matches":
    my_matches_header = """
    <div style="background: #FFFFFF; border: 1px solid #DADACF; border-left: 4px solid #1B7064; border-radius: 6px; padding: 1.4rem 1.6rem; margin-bottom: 1.5rem;">
        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; color: #1B7064; font-weight: 700; margin-bottom: 0.2rem;">
            Verified Compatibility
        </div>
        <h2 style="font-family: 'Inter', sans-serif; color: #171717; margin: 0; font-size: 1.6rem; font-weight: 900; letter-spacing: -0.02em;">
            My High-Confidence Matches
        </h2>
        <p style="color: #555550; margin: 0.3rem 0 0 0; font-size: 0.95rem; line-height: 1.5;">
            Opportunities where your academic degree, year, social category, state domicile, and household income satisfy published eligibility criteria.
        </p>
    </div>
    """
    render_html(my_matches_header)

    eligible_matches = [m for m in st.session_state.matches if m.is_potential_match and m.relevance_score >= 45]

    if not eligible_matches:
        st.info("No matching records found in the current workspace. Configure your student profile under 'Find Scholarships' to initiate live discovery.")
        if st.button("Go to Find Scholarships →", type="primary"):
            st.session_state.current_page = "Find Scholarships"
            st.rerun()
    else:
        for idx, match in enumerate(eligible_matches):
            render_scholarship_card(match, index=idx)

# -------------------------------------------------------------
# PAGE 4: IS THIS REAL? (SCAM CHECKER)
# -------------------------------------------------------------
elif current_page == "Is This Real?":
    scam_banner_html = """
    <div style="background: #FFFFFF; border: 1px solid #DADACF; border-left: 4px solid #FF6700; border-radius: 6px; padding: 1.4rem 1.6rem; margin-bottom: 1.5rem;">
        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; color: #FF6700; font-weight: 700; margin-bottom: 0.2rem;">
            Authenticity &amp; Fraud Investigation
        </div>
        <h2 style="font-family: 'Inter', sans-serif; color: #171717; margin: 0; font-size: 1.6rem; font-weight: 900; letter-spacing: -0.02em;">
            Not sure whether a scholarship is genuine?
        </h2>
        <p style="color: #555550; margin: 0.3rem 0 0 0; font-size: 0.95rem; line-height: 1.5;">
            Check suspicious scholarship links and messages before sharing your information. We evaluate domain trust, fee solicitations, and cross-reference official portals.
        </p>
    </div>
    """
    render_html(scam_banner_html)

    # Scenarios Bar
    with st.expander("Try Pre-Configured Test Scenarios", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("WhatsApp Fee Scam Forward", use_container_width=True):
                st.session_state["scam_input_text"] = (
                    "CONGRATULATIONS! You have been selected for PM National Student Scholarship 2026. "
                    "Amount: Rs. 75,000. To activate your scholarship, pay a refundable processing fee of ₹499 "
                    "via UPI and share your Aadhaar number & OTP on https://pm-scholarship-portal.xyz/pay"
                )
                st.rerun()

        with c2:
            if st.button("Genuine Karnataka SSP Notice", use_container_width=True):
                st.session_state["scam_input_text"] = (
                    "Karnataka State Scholarship Portal (SSP) Post-Matric Scholarship for SC/ST/OBC/General students. "
                    "Official application link: https://ssp.postmatric.karnataka.gov.in. No fee required."
                )
                st.rerun()

        with c3:
            if st.button("Third-Party Unverified Circular", use_container_width=True):
                st.session_state["scam_input_text"] = (
                    "Global Tech Education Grant for Indian College Students. Up to 1 Lakh assistance. "
                    "Apply at https://www.tech-grant-india.info/apply-now"
                )
                st.rerun()

    preset_val = st.session_state.get("scam_input_preset", "")
    default_text = preset_val if preset_val else st.session_state.get("scam_input_text", "")

    with st.container(border=True):
        user_input = st.text_area(
            "Enter circular message text, email notice, or suspicious application URL:",
            value=default_text,
            height=120,
            placeholder="Paste scholarship circular text, WhatsApp forward, or application URL here..."
        )

        check_btn = st.button("Check authenticity →", type="primary", use_container_width=True)

    if check_btn:
        if not user_input.strip():
            st.warning("Please enter scholarship text or a portal URL to analyze.")
        else:
            with st.spinner("Analyzing domain trust, cross-referencing official portals with TinyFish..."):
                result = st.session_state.scam_checker.investigate(user_input)

            # Investigation Report Output
            v = result.verdict
            if v == "Likely legitimate":
                v_border = "#1B7064"
                v_color = "#1B7064"
                v_bg = "rgba(27, 112, 100, 0.08)"
                risk_label = "LOW RISK &middot; OFFICIAL DOMAIN CORROBORATED"
            elif v == "Suspicious":
                v_border = "#FF6700"
                v_color = "#FF6700"
                v_bg = "rgba(255, 103, 0, 0.08)"
                risk_label = "HIGH RISK &middot; RED FLAGS DETECTED"
            else:
                v_border = "#777770"
                v_color = "#171717"
                v_bg = "#F8F8F2"
                risk_label = "MODERATE RISK &middot; VERIFICATION REQUIRED"

            report_header_html = f"""
            <div style="background: {v_bg}; border: 1px solid {v_border}; border-top: 3px solid {v_border}; border-radius: 4px; padding: 1.2rem 1.4rem; margin: 1.5rem 0;">
                <div style="display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: 0.6rem;">
                    <div>
                        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; font-weight: 700; color: {v_color}; text-transform: uppercase; letter-spacing: 0.08em;">
                            INVESTIGATION REPORT &middot; {risk_label}
                        </div>
                        <div style="font-family: 'Inter', sans-serif; font-size: 1.6rem; font-weight: 900; color: #171717; margin-top: 0.2rem;">
                            Verdict: {v.upper()}
                        </div>
                    </div>
                    <div style="text-align: right; font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem; color: #171717;">
                        Confidence: <strong style="color: {v_color};">{int(result.confidence * 100)}%</strong>
                    </div>
                </div>
            </div>
            """
            render_html(report_header_html)

            c_eval1, c_eval2 = st.columns(2)
            with c_eval1:
                st.markdown("##### Suspicious Indicators &amp; Red Flags")
                if result.red_flags:
                    for flag in result.red_flags:
                        st.markdown(f"&times; <strong style='color: #FF6700;'>{flag}</strong>", unsafe_allow_html=True)
                else:
                    st.caption("No critical security hazards (credential sharing or fee demands) detected.")

                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                st.markdown("##### Evidence Links &amp; Audit Trail")
                for ev in result.evidence:
                    st.markdown(f"&bull; <span style='font-family: \"IBM Plex Mono\", monospace; font-size: 0.78rem;'>{ev}</span>", unsafe_allow_html=True)

            with c_eval2:
                st.markdown("##### Legitimate Corroborating Signals")
                if result.legitimate_indicators:
                    for sig in result.legitimate_indicators:
                        st.markdown(f"&check; <span style='color: #1B7064; font-weight: 600;'>{sig}</span>", unsafe_allow_html=True)
                else:
                    st.caption("No official government corroboration was found on authorized domains.")

                st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
                st.markdown("##### Suggested Action")
                for rec in result.recommendations:
                    st.markdown(f"&rsaquo; {rec}")

# -------------------------------------------------------------
# PAGE 5: ABOUT SCHEMERADAR
# -------------------------------------------------------------
elif current_page == "About SchemeRadar":
    about_card_html = """
    <div style="background: #FFFFFF; border: 1px solid #DADACF; border-radius: 6px; padding: 2rem; margin-bottom: 2rem;">
        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; color: #FF6700; font-weight: 700; margin-bottom: 0.3rem;">
            System Architecture
        </div>
        <h2 style="font-family: 'Inter', sans-serif; color: #171717; font-size: 1.8rem; font-weight: 900; margin: 0 0 0.5rem 0; letter-spacing: -0.02em;">
            About SchemeRadar
        </h2>
        <p style="font-size: 1rem; color: #444440; line-height: 1.6; margin: 0; max-width: 800px;">
            SchemeRadar is an autonomous scholarship &amp; government scheme discovery engine engineered to resolve the information deficit faced by Indian undergraduate and technical students.
        </p>
        
        <hr style="border: none; border-top: 1px solid #DADACF; margin: 1.8rem 0;">
        
        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; color: #171717; font-weight: 700; margin-bottom: 0.8rem;">
            POWERED BY TINYFISH &mdash; Core Web Intelligence Pillars
        </div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
            <div style="background: #F8F8F2; border: 1px solid #DADACF; padding: 1.2rem; border-radius: 4px;">
                <div style="font-family: 'IBM Plex Mono', monospace; font-weight: 800; color: #1B7064; font-size: 0.82rem; margin-bottom: 0.3rem;">
                    TinySearch
                </div>
                <p style="color: #555550; font-size: 0.82rem; margin: 0; line-height: 1.5;">
                    Dynamically queries national and state scholarship ecosystems using candidate criteria (State, Course, Category, Academic Year).
                </p>
            </div>
            <div style="background: #F8F8F2; border: 1px solid #DADACF; padding: 1.2rem; border-radius: 4px;">
                <div style="font-family: 'IBM Plex Mono', monospace; font-weight: 800; color: #1B7064; font-size: 0.82rem; margin-bottom: 0.3rem;">
                    TinyFetch
                </div>
                <p style="color: #555550; font-size: 0.82rem; margin: 0; line-height: 1.5;">
                    Retrieves clean, LLM-ready markdown from verified government directories, extracting individual scheme headings and tables without ad noise.
                </p>
            </div>
            <div style="background: #F8F8F2; border: 1px solid #DADACF; padding: 1.2rem; border-radius: 4px;">
                <div style="font-family: 'IBM Plex Mono', monospace; font-weight: 800; color: #FF6700; font-size: 0.82rem; margin-bottom: 0.3rem;">
                    TinyAgent SSE
                </div>
                <p style="color: #555550; font-size: 0.82rem; margin: 0; line-height: 1.5;">
                    Executes autonomous browser navigation across dynamic, JavaScript-heavy government portals, expanding circular accordions and extracting structured schemas.
                </p>
            </div>
        </div>

        <hr style="border: none; border-top: 1px solid #DADACF; margin: 1.8rem 0;">

        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; color: #171717; font-weight: 700; margin-bottom: 0.8rem;">
            Responsible Engineering &amp; Verification Protocol
        </div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
            <div style="border-left: 2px solid #DADACF; padding-left: 0.85rem;">
                <strong style="font-size: 0.85rem; color: #171717;">Zero Sensitive PII</strong>
                <p style="color: #666660; font-size: 0.78rem; margin: 0.2rem 0 0 0; line-height: 1.45;">No Aadhaar numbers, bank account credentials, or passwords are ever requested or stored.</p>
            </div>
            <div style="border-left: 2px solid #DADACF; padding-left: 0.85rem;">
                <strong style="font-size: 0.85rem; color: #171717;">Explainable Matching</strong>
                <p style="color: #666660; font-size: 0.78rem; margin: 0.2rem 0 0 0; line-height: 1.45;">Every compatibility score explicitly distinguishes verified criteria from unconfirmed notice fields.</p>
            </div>
            <div style="border-left: 2px solid #DADACF; padding-left: 0.85rem;">
                <strong style="font-size: 0.85rem; color: #171717;">Source Provenance</strong>
                <p style="color: #666660; font-size: 0.78rem; margin: 0.2rem 0 0 0; line-height: 1.45;">Every deadline and amount links back to exact quote snippets and verified .gov.in domains.</p>
            </div>
        </div>
    </div>
    """
    render_html(about_card_html)
