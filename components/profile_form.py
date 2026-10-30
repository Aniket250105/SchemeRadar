import streamlit as st
from core.models import StudentProfile
from config.settings import COURSES, ACADEMIC_YEARS, INDIAN_STATES, CATEGORIES, INCOME_BANDS, INTERESTS
from utils.helpers import render_html

def render_profile_form() -> StudentProfile:
    """Render the student profile input form in Swiss editorial style."""
    header_html = """
    <div style="margin-bottom: 1.5rem;">
        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; color: #FF6700; font-weight: 700; margin-bottom: 0.4rem;">
            Candidate Parameters
        </div>
        <h2 style="font-family: 'Inter', -apple-system, sans-serif; color: #171717; font-size: 1.8rem; font-weight: 900; margin: 0 0 0.3rem 0; letter-spacing: -0.02em;">
            Student Profile &amp; Eligibility Setup
        </h2>
        <p style="color: #555550; font-size: 0.95rem; margin: 0; line-height: 1.5;">
            Define your degree, domicile, and income band. TinyFish Search and Fetch agents use these parameters to discover matching schemes.
        </p>
    </div>
    """
    render_html(header_html)

    # Quick Presets (Editorial Buttons)
    with st.expander("Load Verified Profile Presets", expanded=False):
        st.caption("Select a standard candidate template to pre-fill test criteria:")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Karnataka B.Tech 2nd Year (OBC)", use_container_width=True):
                st.session_state["p_course"] = "B.Tech"
                st.session_state["p_year"] = "2nd Year"
                st.session_state["p_state"] = "Karnataka"
                st.session_state["p_cat"] = "OBC"
                st.session_state["p_income"] = "₹1–2.5 lakh"
                st.session_state["p_interests"] = ["Engineering", "Computer Science", "Technology"]
                st.session_state["p_college"] = "BMS College of Engineering"
                st.rerun()
        with c2:
            if st.button("All-India STEM Women (EWS)", use_container_width=True):
                st.session_state["p_course"] = "B.Tech"
                st.session_state["p_year"] = "1st Year"
                st.session_state["p_state"] = "Maharashtra"
                st.session_state["p_cat"] = "EWS"
                st.session_state["p_income"] = "Below ₹1 lakh"
                st.session_state["p_interests"] = ["Women in STEM", "Engineering", "Artificial Intelligence"]
                st.session_state["p_college"] = "COEP Technological University"
                st.rerun()
        with c3:
            if st.button("Post-Graduate Research (SC/ST)", use_container_width=True):
                st.session_state["p_course"] = "M.Tech"
                st.session_state["p_year"] = "1st Year"
                st.session_state["p_state"] = "Delhi"
                st.session_state["p_cat"] = "SC"
                st.session_state["p_income"] = "₹2.5–5 lakh"
                st.session_state["p_interests"] = ["Research", "Innovation", "Technology"]
                st.session_state["p_college"] = "Delhi Technological University"
                st.rerun()

    # Form Container
    with st.container(border=True):
        sec1_html = """
        <div style="font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #171717; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.8rem;">
            01 &mdash; Academic Background
        </div>
        """
        render_html(sec1_html)

        col1, col2 = st.columns(2)
        with col1:
            course_idx = COURSES.index(st.session_state.get("p_course", "B.Tech")) if st.session_state.get("p_course", "B.Tech") in COURSES else 0
            course = st.selectbox(
                "Degree Program",
                options=COURSES,
                index=course_idx,
                help="Select your enrolled degree program."
            )
            college = st.text_input(
                "College or University Name",
                value=st.session_state.get("p_college", ""),
                placeholder="e.g. BMS College of Engineering, VTU, NITK"
            )
        with col2:
            year_idx = ACADEMIC_YEARS.index(st.session_state.get("p_year", "2nd Year")) if st.session_state.get("p_year", "2nd Year") in ACADEMIC_YEARS else 1
            academic_year = st.selectbox(
                "Current Academic Year",
                options=ACADEMIC_YEARS,
                index=year_idx,
                help="Year of study currently underway."
            )
            marks = st.text_input(
                "Academic Performance / Score",
                value=st.session_state.get("p_marks", "8.5 CGPA / 85%"),
                placeholder="e.g. 8.5 CGPA or 82%"
            )

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        sec2_html = """
        <div style="padding-top: 1rem; border-top: 1px solid #DADACF; font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #171717; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.8rem;">
            02 &mdash; Personal Eligibility
        </div>
        """
        render_html(sec2_html)

        col3, col4, col5 = st.columns(3)
        with col3:
            state_idx = INDIAN_STATES.index(st.session_state.get("p_state", "Karnataka")) if st.session_state.get("p_state", "Karnataka") in INDIAN_STATES else 0
            state = st.selectbox(
                "State of Domicile",
                options=INDIAN_STATES,
                index=state_idx,
                help="Permanent residential state where domicile certificate was issued."
            )
        with col4:
            cat_idx = CATEGORIES.index(st.session_state.get("p_cat", "OBC")) if st.session_state.get("p_cat", "OBC") in CATEGORIES else 1
            category = st.selectbox(
                "Social Category",
                options=CATEGORIES,
                index=cat_idx,
                help="Category for statutory reservations and fee waivers."
            )
        with col5:
            inc_idx = INCOME_BANDS.index(st.session_state.get("p_income", "₹1–2.5 lakh")) if st.session_state.get("p_income", "₹1–2.5 lakh") in INCOME_BANDS else 1
            income = st.selectbox(
                "Annual Household Income Band",
                options=INCOME_BANDS,
                index=inc_idx,
                help="Annual household income documented in official revenue certificate."
            )

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        sec3_html = """
        <div style="padding-top: 1rem; border-top: 1px solid #DADACF; font-family: 'IBM Plex Mono', monospace; font-size: 0.72rem; color: #171717; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.8rem;">
            03 &mdash; Interests &amp; Disciplines
        </div>
        """
        render_html(sec3_html)

        default_interests = st.session_state.get("p_interests", ["Engineering", "Computer Science", "Technology"])
        interests = st.multiselect(
            "Relevant Academic Disciplines & Scheme Types",
            options=INTERESTS,
            default=default_interests,
            help="Choose specializations to match specialized departmental scholarships."
        )

        privacy_html = """
        <div style="margin-top: 1.2rem; padding: 0.75rem 1rem; background: #F8F8F2; border-left: 3px solid #1B7064; font-size: 0.82rem; color: #444440; line-height: 1.5;">
            <strong style="color: #171717; font-weight: 700;">Privacy Assurance:</strong> SchemeRadar does not store sensitive PII, Aadhaar numbers, or passwords. Data is used strictly within this session to evaluate eligibility.
        </div>
        """
        render_html(privacy_html)

    return StudentProfile(
        course=course,
        academic_year=academic_year,
        college_name=college if college else None,
        academic_performance=marks if marks else None,
        state_of_domicile=state,
        category=category,
        family_income_band=income,
        interests=interests,
    )
