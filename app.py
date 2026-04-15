import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="AI Loan Approval Dashboard",
    page_icon="🏦",
    layout="wide"
)

# ---------------- CUSTOM STYLING ----------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #f0f4f8;
}
h1, h2, h3 {
    font-family: 'DM Serif Display', serif;
    color: #0a2540;
}
.stButton>button {
    background: linear-gradient(135deg, #0a2540 0%, #1a5276 100%);
    color: white;
    font-size: 16px;
    font-weight: 600;
    border-radius: 10px;
    height: 3em;
    width: 100%;
    border: none;
    letter-spacing: 0.5px;
    transition: all 0.3s ease;
}
.stButton>button:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}
.metric-card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    text-align: center;
}
.score-band {
    padding: 6px 14px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 14px;
    display: inline-block;
    margin-top: 6px;
}
.section-header {
    font-size: 22px;
    font-weight: 600;
    color: #0a2540;
    border-left: 4px solid #1a5276;
    padding-left: 12px;
    margin: 20px 0 10px 0;
}
</style>
""", unsafe_allow_html=True)

# ================================================
# HELPER: Credit Score Band
# ================================================
def get_credit_band(score):
    if score >= 800:
        return "Exceptional", "#1a7a4a", "#e6f9ef"
    elif score >= 740:
        return "Very Good", "#2471a3", "#e8f4fd"
    elif score >= 670:
        return "Good", "#d4ac0d", "#fef9e7"
    elif score >= 580:
        return "Fair", "#ca6f1e", "#fdf2e9"
    else:
        return "Poor", "#cb4335", "#fdedec"

# ================================================
# HELPER: Gauge Chart
# ================================================
def draw_gauge(score, title="Credit Score"):
    fig, ax = plt.subplots(figsize=(5, 3), subplot_kw={'projection': 'polar'})
    ax.set_theta_offset(np.pi)
    ax.set_theta_direction(-1)

    bands = [
        (300, 580, '#e74c3c'),
        (580, 670, '#e67e22'),
        (670, 740, '#f1c40f'),
        (740, 800, '#2ecc71'),
        (800, 850, '#1abc9c'),
    ]

    for low, high, color in bands:
        start_angle = (low - 300) / 550 * np.pi
        end_angle   = (high - 300) / 550 * np.pi
        ax.barh(1, end_angle - start_angle, left=start_angle,
                height=0.5, color=color, edgecolor='white', linewidth=1.5)

    needle_angle = (score - 300) / 550 * np.pi
    ax.annotate('', xy=(needle_angle, 1), xytext=(needle_angle, 0),
                arrowprops=dict(arrowstyle='->', color='#0a2540', lw=2.5))

    ax.set_ylim(0, 1.8)
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.spines['polar'].set_visible(False)
    ax.grid(False)
    ax.set_title(f"{title}\n{score} / 850", fontsize=13, fontweight='bold', color='#0a2540', pad=10)
    return fig

# ================================================
# HELPER: Credit Score Calculator
# ================================================
def calculate_credit_score(payment_history_pct, credit_utilization, credit_age_years,
                            num_accounts, num_inquiries, total_debt, annual_income):
    # Payment history (35%)
    ph_score = (payment_history_pct / 100) * 35

    # Credit utilization (30%) — lower is better, ideal < 30%
    if credit_utilization <= 10:
        util_score = 30
    elif credit_utilization <= 30:
        util_score = 25
    elif credit_utilization <= 50:
        util_score = 15
    elif credit_utilization <= 75:
        util_score = 7
    else:
        util_score = 2

    # Length of credit history (15%)
    age_score = min(credit_age_years / 20, 1) * 15

    # Credit mix / number of accounts (10%)
    mix_score = min(num_accounts / 10, 1) * 10

    # New inquiries (10%) — fewer is better
    if num_inquiries == 0:
        inq_score = 10
    elif num_inquiries <= 2:
        inq_score = 7
    elif num_inquiries <= 5:
        inq_score = 4
    else:
        inq_score = 1

    # Debt-to-income bonus/penalty (extra modifier)
    dti = (total_debt / annual_income * 100) if annual_income > 0 else 100
    if dti < 20:
        dti_modifier = 10
    elif dti < 36:
        dti_modifier = 5
    elif dti < 50:
        dti_modifier = 0
    else:
        dti_modifier = -10

    raw = ph_score + util_score + age_score + mix_score + inq_score + dti_modifier
    # Scale raw (0-110) → 300-850
    credit_score = int(300 + (raw / 110) * 550)
    credit_score = max(300, min(850, credit_score))

    breakdown = {
        "Payment History (35%)": round(ph_score, 1),
        "Credit Utilization (30%)": round(util_score, 1),
        "Credit Age (15%)": round(age_score, 1),
        "Credit Mix (10%)": round(mix_score, 1),
        "Recent Inquiries (10%)": round(inq_score, 1),
        "Debt-to-Income Bonus": round(dti_modifier, 1),
    }
    return credit_score, breakdown

# ================================================
# SIDEBAR — APPLICANT PROFILE
# ================================================
st.sidebar.header("📋 Applicant Profile")

with st.sidebar.expander("👤 Personal Details", expanded=True):
    gender          = st.selectbox("Gender", ["Male", "Female"])
    married         = st.selectbox("Married", ["Yes", "No"])
    dependents      = st.selectbox("Dependents", [0, 1, 2, 3])
    education       = st.selectbox("Education", ["Graduate", "Not Graduate"])
    self_employed   = st.selectbox("Self Employed", ["Yes", "No"])
    property_area   = st.selectbox("Property Area", ["Urban", "Semiurban", "Rural"])

with st.sidebar.expander("💰 Financial Details", expanded=True):
    app_income      = st.number_input("Applicant Income (₹)", min_value=0, value=50000)
    coapp_income    = st.number_input("Coapplicant Income (₹)", min_value=0, value=0)
    loan_amount     = st.number_input("Loan Amount (₹ thousands)", min_value=0, value=150)
    loan_term       = st.number_input("Loan Term (months)", min_value=0, value=360)
    credit_history  = st.selectbox("Past Loan Repayment Record", [1, 0],
                                   format_func=lambda x: "Clear" if x == 1 else "Issues")

with st.sidebar.expander("📊 Credit Score Inputs", expanded=True):
    st.caption("Used to calculate your FICO-style credit score")
    payment_history_pct = st.slider("On-Time Payments (%)", 0, 100, 85)
    credit_utilization  = st.slider("Credit Utilization (%)", 0, 100, 30)
    credit_age_years    = st.slider("Length of Credit History (yrs)", 0, 30, 5)
    num_accounts        = st.slider("Number of Credit Accounts", 0, 20, 4)
    num_inquiries       = st.slider("Recent Credit Inquiries (last 2 yrs)", 0, 15, 1)
    total_debt          = st.number_input("Total Outstanding Debt (₹)", min_value=0, value=200000)

# ================================================
# ENCODING
# ================================================
gender_val      = 1 if gender == "Male" else 0
married_val     = 1 if married == "Yes" else 0
education_val   = 0 if education == "Graduate" else 1
self_emp_val    = 1 if self_employed == "Yes" else 0
property_val    = {"Urban": 2, "Semiurban": 1, "Rural": 0}[property_area]
annual_income   = (app_income + coapp_income) * 12

# ================================================
# HEADER
# ================================================
st.title("🏦 AI Smart Loan Approval System")
st.markdown("#### Intelligent Banking Analytics & Decision Support Dashboard")
st.markdown("---")

# ================================================
# PREDICT BUTTON
# ================================================
if st.button("🔍 Predict Loan Approval & Calculate Credit Score"):

    # --- Credit Score ---
    credit_score, cs_breakdown = calculate_credit_score(
        payment_history_pct, credit_utilization, credit_age_years,
        num_accounts, num_inquiries, total_debt, annual_income
    )
    band_label, band_text_color, band_bg_color = get_credit_band(credit_score)

    # --- Loan Approval Score ---
    cs_factor = (credit_score - 300) / 550   # 0 to 1
    approval_score = (
        credit_history * 40 +
        cs_factor * 30 +
        (app_income / 1000) * 3 +
        (coapp_income / 1000) * 1.5 -
        (loan_amount / 100) * 1.2
    )

    approved = approval_score > 30
    prediction = "Approved ✅" if approved else "Rejected ❌"
    confidence = min(round(abs(approval_score), 1), 98) if approved else max(round(abs(approval_score), 1), 45)
    risk_level = "Low" if approved and cs_factor > 0.5 else ("Medium" if approved else "High")

    # ================================================
    # SECTION 1: TOP METRICS
    # ================================================
    st.markdown('<div class="section-header">📌 Decision Summary</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Loan Status", prediction)
    col2.metric("Confidence Score", f"{confidence}%")
    col3.metric("Risk Level", risk_level)
    col4.metric("Credit Score", f"{credit_score} / 850")

    st.markdown("---")

    # ================================================
    # SECTION 2: CREDIT SCORE DEEP DIVE
    # ================================================
    st.markdown('<div class="section-header">📊 Credit Score Analysis</div>', unsafe_allow_html=True)

    cs_col1, cs_col2 = st.columns([1, 1])

    with cs_col1:
        gauge_fig = draw_gauge(credit_score)
        st.pyplot(gauge_fig)

        st.markdown(
            f'<div style="text-align:center;">'
            f'<span class="score-band" style="color:{band_text_color};background:{band_bg_color};">'
            f'⬤ {band_label}</span></div>',
            unsafe_allow_html=True
        )
        st.caption("Score ranges: Poor 300–579 | Fair 580–669 | Good 670–739 | Very Good 740–799 | Exceptional 800–850")

    with cs_col2:
        st.markdown("**Score Factor Breakdown**")
        max_weights = {
            "Payment History (35%)": 35,
            "Credit Utilization (30%)": 30,
            "Credit Age (15%)": 15,
            "Credit Mix (10%)": 10,
            "Recent Inquiries (10%)": 10,
            "Debt-to-Income Bonus": 10,
        }
        breakdown_df = pd.DataFrame({
            "Factor": list(cs_breakdown.keys()),
            "Your Score": list(cs_breakdown.values()),
            "Max Score": [max_weights[k] for k in cs_breakdown.keys()]
        })

        fig_bar, ax_bar = plt.subplots(figsize=(6, 4))
        x = np.arange(len(breakdown_df))
        bars_max = ax_bar.bar(x, breakdown_df["Max Score"], color="#d5e8f5", label="Max", width=0.5)
        bars_you = ax_bar.bar(x, breakdown_df["Your Score"], color="#1a5276", label="Yours", width=0.5)
        ax_bar.set_xticks(x)
        ax_bar.set_xticklabels(breakdown_df["Factor"], rotation=30, ha='right', fontsize=8)
        ax_bar.set_title("Your Score vs Maximum", fontsize=11, fontweight='bold')
        ax_bar.legend(fontsize=9)
        ax_bar.spines[['top', 'right']].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig_bar)

    st.markdown("---")

    # ================================================
    # SECTION 3: APPLICANT SUMMARY
    # ================================================
    st.markdown('<div class="section-header">👤 Applicant Summary</div>', unsafe_allow_html=True)

    summary_df = pd.DataFrame({
        "Field": [
            "Gender", "Married", "Dependents", "Education",
            "Self Employed", "Property Area",
            "Applicant Income", "Coapplicant Income",
            "Loan Amount", "Loan Term", "Repayment Record"
        ],
        "Value": [
            gender, married, dependents, education,
            self_employed, property_area,
            f"₹{app_income:,}", f"₹{coapp_income:,}",
            f"₹{loan_amount:,}K", f"{loan_term} months",
            "Clear" if credit_history == 1 else "Issues"
        ]
    })
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ================================================
    # SECTION 4: FINANCIAL ANALYTICS
    # ================================================
    st.markdown('<div class="section-header">📈 Financial Analytics</div>', unsafe_allow_html=True)

    col4, col5 = st.columns(2)

    with col4:
        fig1, ax1 = plt.subplots(figsize=(5, 4))
        labels = ['Approval Probability', 'Remaining Risk']
        values = [confidence, 100 - confidence]
        colors = ['#1a5276', '#d5e8f5']
        ax1.pie(values, labels=labels, autopct='%1.1f%%', colors=colors,
                wedgeprops=dict(width=0.55), startangle=90)
        ax1.set_title("Approval Probability", fontweight='bold')
        st.pyplot(fig1)

    with col5:
        fig2, ax2 = plt.subplots(figsize=(5, 4))
        categories = ['App. Income', 'Coapp. Income', 'Loan Amount']
        values_bar = [app_income, coapp_income, loan_amount * 1000]
        bar_colors = ['#1a5276', '#2471a3', '#85c1e9']
        ax2.bar(categories, values_bar, color=bar_colors)
        ax2.set_title("Financial Comparison (₹)", fontweight='bold')
        ax2.set_ylabel("Amount (₹)")
        ax2.spines[['top', 'right']].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig2)

    st.markdown("---")

    # ================================================
    # SECTION 5: INCOME TREND & LOAN DISTRIBUTION
    # ================================================
    st.markdown('<div class="section-header">📉 Trend & Distribution</div>', unsafe_allow_html=True)

    col6, col7 = st.columns(2)

    with col6:
        fig3, ax3 = plt.subplots(figsize=(5, 4))
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May']
        income_trend = [app_income * m for m in [0.8, 0.9, 1.0, 1.05, 1.1]]
        ax3.plot(months, income_trend, marker='o', color='#1a5276', linewidth=2.5)
        ax3.fill_between(months, income_trend, alpha=0.1, color='#1a5276')
        ax3.set_title("Income Growth Trend", fontweight='bold')
        ax3.set_ylabel("Income (₹)")
        ax3.spines[['top', 'right']].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig3)

    with col7:
        fig4, ax4 = plt.subplots(figsize=(5, 4))
        sample_loans = [loan_amount * m for m in [0.7, 0.85, 1.0, 1.15, 1.3]]
        ax4.hist(sample_loans, bins=5, color='#2471a3', edgecolor='white')
        ax4.set_title("Loan Amount Distribution", fontweight='bold')
        ax4.set_xlabel("Loan Amount (₹K)")
        ax4.set_ylabel("Frequency")
        ax4.spines[['top', 'right']].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig4)

    st.markdown("---")

    # ================================================
    # SECTION 6: CREDIT SCORE IMPROVEMENT TIPS
    # ================================================
    st.markdown('<div class="section-header">💡 Credit Score Improvement Tips</div>', unsafe_allow_html=True)

    tips = []
    if payment_history_pct < 95:
        tips.append("✅ **Improve payment history** — Always pay bills on time. Even one missed payment can hurt significantly.")
    if credit_utilization > 30:
        tips.append("✅ **Lower credit utilization** — Try to keep usage below 30% of your total credit limit.")
    if credit_age_years < 5:
        tips.append("✅ **Build credit history** — Avoid closing old accounts; a longer history boosts your score.")
    if num_inquiries > 2:
        tips.append("✅ **Limit new credit applications** — Multiple hard inquiries in a short period lower your score.")
    if num_accounts < 3:
        tips.append("✅ **Diversify credit mix** — Having a mix of credit cards, loans, and lines of credit helps.")
    if total_debt / max(annual_income, 1) > 0.36:
        tips.append("✅ **Reduce debt-to-income ratio** — Pay down existing debt before taking new loans.")

    if not tips:
        st.success("🎉 Excellent credit profile! You're in great shape for loan approval.")
    else:
        for tip in tips:
            st.info(tip)

# ================================================
# FOOTER
# ================================================
st.markdown("---")
st.caption("AI Smart Loan Approval System | Credit Score Engine included | Developed as Premium Internship Project")
