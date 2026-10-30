# SchemeRadar
### *Find schemes. Check eligibility. Apply confidently.*

SchemeRadar is an AI-powered scholarship and government scheme discovery platform engineered for Indian undergraduate, technical, and college students. 

By integrating the **TinyFish Web Intelligence Platform (Search, Fetch, and Agent APIs)**, SchemeRadar dynamically queries authoritative state and national portals (such as the National Scholarship Portal and Karnataka SSP), extracts structured scholarship data with field-level provenance evidence, evaluates transparent multi-tier eligibility, and protects students from scholarship scams.

---

## 📌 Problem Statement

Each year, Indian college students miss out on hundreds of crores in financial assistance and scholarships due to:
- **Scattered Information:** Schemes are spread across dozens of central ministries, state scholarship portals (e.g., Karnataka SSP, MahaDBT), AICTE, UGC, and university circular boards.
- **Dynamic & Fragile Portals:** Government portals frequently alter layouts, embed notices in complex PDF circulars, or require multi-step navigation behind ASP.NET / JavaScript accordions.
- **Complex & Opaque Eligibility:** Students struggle to parse complicated combinations of domicile state, academic degree, social reservation categories, and annual family income ceilings.
- **Unreliable Deadlines & Broken Links:** Expired schemes are frequently presented as active by third-party aggregators, leading to missed application windows.
- **Phishing & Fraud:** WhatsApp forwards and fake lookalike portals demand "registration fees" or steal Aadhaar OTPs and banking credentials from vulnerable students.

---

## 💡 Our Solution

SchemeRadar automates scholarship discovery, verification, and eligibility checking using real-time web intelligence:
1. **Dynamic Web Discovery:** Formulates targeted search queries to locate official announcements without static hardcoding.
2. **Deep Content & PDF Extraction:** Fetches clean, LLM-ready markdown from official tables and circulars, parsing directories into discrete opportunities while recording source homepages separately.
3. **Autonomous Browser Navigation:** Deploys TinyFish Agent SSE to interact with complex portals and expand dynamic circulars.
4. **Explainable 3-State Eligibility:** Distinguishes verified matches from missing criteria, calculating transparent compatibility without assuming unknown conditions.
5. **Field-Level Provenance & Scam Protection:** Tracks every amount, deadline, and rule back to its source snippet, classifying domain trust and flagging fraudulent fee or OTP requests.

---

## ✨ Features

- **Personalized Scholarship Discovery:** Tailors search queries using academic degree, year, domicile, and category.
- **TinyFish Search Integration:** Discovers official central and state portals in real-time.
- **TinyFish Fetch Integration:** Extracts ad-free markdown, outbound application links, and table data.
- **TinyFish Agent Integration:** Autonomously navigates dynamic, JavaScript-heavy portals via Server-Sent Events (SSE).
- **Multi-Tier Eligibility Filtering:** Classifies opportunities into three explicit states (`Eligible`, `Potential match`, `Ineligible`).
- **Personalized Match Scoring:** Separates relevance alignment (0–100%) from evidence confidence (0–100%).
- **Asia/Kolkata (IST) Deadline Tracking:** Parses multiple Indian date formats and flags urgency (<7 days, closing soon, expired).
- **Source Verification & Provenance:** Prioritizes official `.gov.in`, `.nic.in`, and `.ac.in` domains, tracking exact text quotes for all key fields.
- **Evidence-Based Scam Checker:** Detects credential theft, fee requests, and typosquatted domains with live corroboration.

---

## 🛠️ Technology Stack

- **Programming Language:** Python 3.10+
- **Frontend / UI:** Streamlit (Swiss editorial aesthetic with the official TinyFish brand palette)
- **Web Intelligence:** TinyFish Search, Fetch, and Agent SSE APIs
- **HTTP & Streaming:** Requests
- **Data Validation & Schemas:** Pydantic
- **Data Processing:** Pandas
- **Date & Timezone Processing:** Python `datetime` (Asia/Kolkata IST)
- **Environment Management:** python-dotenv

---

## 🏗️ Architecture & Workflow

```
┌─────────────────────────────────┐
│     Student Profile Form        │ (Course, Year, State, Category, Income)
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│       TinyFish Search API       │ (Personalized queries across .gov.in ecosystems)
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│       TinyFish Fetch API        │ (Clean Markdown & link extraction from directories)
└────────────────┬────────────────┘
                 │
                 ├─ [Dynamic / Expandable Portal?] ──► ┌───────────────────────────┐
                 │                                     │   TinyFish Agent API      │
                 │                                     │  (Autonomous browser SSE) │
                 │                                     └─────────────┬─────────────┘
                 ▼                                                   │
┌─────────────────────────────────┐                                  │
│   Structured Data Extraction    │ ◄────────────────────────────────┘
│   & Field-Level Provenance      │ (SourcePage vs ScholarshipOpportunity models)
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│     Eligibility Matcher         │ (3-state: Eligible, Potential match, Ineligible)
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│    SchemeRadar Dashboard        │ (Filtered cards, official links, TinyFish logs)
└─────────────────────────────────┘
```

---

## 📦 Installation & Setup

### 1. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/Aniket250105/SchemeRadar.git
cd SchemeRadar

python -m venv .venv
```

### 2. Activate Virtual Environment
**Windows (PowerShell):**
```powershell
.venv\Scripts\activate
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and enter your TinyFish API key:
```env
TINYFISH_API_KEY=your_api_key_here
```

### 5. Run SchemeRadar
```bash
streamlit run app.py
```
Open your browser at **http://localhost:8501**.

---

## 🧪 Testing & Verification

SchemeRadar includes automated verification scripts with real TinyFish API calls:

- **Run Phase 2 Acceptance Test Suite (10/10 Verification Criteria):**
  ```bash
  python test_phase2_acceptance.py
  ```

- **Run Live Hackathon Demonstration (Karnataka B.Tech OBC Profile):**
  ```bash
  python demo_karnataka_btech.py
  ```

---

## ⚠️ Known Limitations & Real-World Considerations

1. **State Portal Firewall Geo-Blocking (`proxy_error`):**
   - Certain Indian state portals (such as `ssp.karnataka.gov.in`) implement cloud IP firewalls that block direct cloud scraping (`proxy_error`).
   - *Mitigation:* SchemeRadar records `SourcePage.fetch_status = "proxy_error"`, alerts the student honestly, and relies on verified search snippets rather than manufacturing false data.
2. **Unpublished Income Limits:**
   - Some merit scholarships do not specify an explicit family income ceiling on their public circular.
   - *Mitigation:* Classified strictly as a **Potential match** with an explicit unverified criteria warning.
3. **Application URL Integrity:**
   - General portal homepages and announcement directories are never presented as direct application submission links. When direct portal logins (`nsp.gov.in`) are confirmed, SchemeRadar distinguishes them from general source circulars.
