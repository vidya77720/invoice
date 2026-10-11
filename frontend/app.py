import streamlit as st
import requests
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import plotly.express as px
import plotly.graph_objects as go

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")

EXPENSE_CATEGORIES = [
    "Software & Technology",
    "Office Supplies",
    "Travel",
    "Marketing",
    "Professional Services",
    "Utilities",
    "Equipment",
    "Logistics",
    "Other"
]

class Settings:
    EXPENSE_CATEGORIES = EXPENSE_CATEGORIES

settings = Settings()

def safe_float(val, default: float = 0.0) -> float:
    if val is None or val == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

# Page config
st.set_page_config(
    page_title="FinPulse AI | Enterprise Invoice Intelligence",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ultra-Premium Light SaaS Theme — Zero-Gap Sidebar Edition
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    *, *::before, *::after {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        box-sizing: border-box;
    }

    /* ─── MAIN CANVAS ─────────────────────────────── */
    .stApp {
        background: linear-gradient(135deg, #F0F4FF 0%, #F8FAFC 40%, #F0FBF7 100%) !important;
        color: #0F172A;
    }

    /* ─── ZERO-GAP SIDEBAR ────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #FAFBFF 100%) !important;
        border-right: 1px solid rgba(99,102,241,0.12) !important;
        box-shadow: 4px 0 24px rgba(99,102,241,0.06) !important;
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    /* Remove all inner padding/gap at top of sidebar */
    section[data-testid="stSidebar"] > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    section[data-testid="stSidebar"] > div > div:first-child {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
        padding-top: 0 !important;
    }
    /* Collapse Streamlit's internal top block in sidebar */
    section[data-testid="stSidebar"] > div {
        padding-top: 0 !important;
    }
    div[data-testid="collapsedControl"] {
        display: none !important;
    }

    /* ─── SIDEBAR RADIO BUTTONS (NAV ITEMS) ──────── */
    section[data-testid="stSidebar"] .stRadio > div {
        gap: 0.18rem !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        display: flex !important;
        align-items: center !important;
        color: #475569 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        padding: 0.62rem 1rem !important;
        border-radius: 10px !important;
        transition: all 0.18s cubic-bezier(0.16,1,0.3,1) !important;
        cursor: pointer !important;
        margin: 0 0.5rem !important;
        border: 1px solid transparent !important;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        background: linear-gradient(90deg, #EEF2FF 0%, #F0F7FF 100%) !important;
        color: #4F46E5 !important;
        border-color: #C7D2FE !important;
        padding-left: 1.2rem !important;
    }
    /* Active selected nav item */
    section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input:checked),
    section[data-testid="stSidebar"] .stRadio [aria-checked="true"] ~ div,
    section[data-testid="stSidebar"] .stRadio label:has(input[type="radio"]:checked) {
        background: linear-gradient(90deg, #EEF2FF 0%, #E0E7FF 100%) !important;
        color: #4338CA !important;
        font-weight: 700 !important;
        border-color: #A5B4FC !important;
    }
    /* Hide the radio circle */
    section[data-testid="stSidebar"] .stRadio input[type="radio"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] > div:first-child {
        display: none !important;
    }

    /* ─── PAGE HEADER ─────────────────────────────── */
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.04em;
        margin-bottom: 0.25rem;
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .hero-subtitle {
        color: #64748B;
        font-size: 0.95rem;
        font-weight: 400;
        margin-bottom: 1.8rem;
        max-width: 680px;
        line-height: 1.6;
    }

    /* ─── KPI CARDS ───────────────────────────────── */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 1.1rem;
        margin-bottom: 1.8rem;
    }
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid rgba(99,102,241,0.1);
        border-radius: 20px;
        padding: 1.4rem 1.5rem;
        box-shadow: 0 4px 24px -4px rgba(99,102,241,0.08), 0 1px 4px rgba(15,23,42,0.04);
        transition: all 0.28s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 3px;
        background: linear-gradient(90deg, #4F46E5, #06B6D4);
        border-radius: 20px 20px 0 0;
        opacity: 0;
        transition: opacity 0.25s ease;
    }
    .kpi-card:hover::before { opacity: 1; }
    .kpi-card:hover {
        transform: translateY(-4px) scale(1.01);
        box-shadow: 0 16px 40px -6px rgba(99,102,241,0.18), 0 4px 12px rgba(15,23,42,0.06);
        border-color: rgba(99,102,241,0.25);
    }
    .kpi-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.6rem;
    }
    .kpi-title {
        color: #94A3B8;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .kpi-icon-bubble {
        width: 38px;
        height: 38px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    .kpi-value {
        color: #0F172A;
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1;
    }
    .kpi-badge {
        display: inline-flex;
        align-items: center;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 0.2rem 0.6rem;
        border-radius: 8px;
        margin-top: 0.6rem;
        letter-spacing: 0.02em;
    }
    .badge-blue { background: #EEF2FF; color: #4338CA; border: 1px solid #C7D2FE; }
    .badge-green { background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
    .badge-amber { background: #FFFBEB; color: #92400E; border: 1px solid #FDE68A; }
    .badge-rose { background: #FFF1F2; color: #9F1239; border: 1px solid #FECDD3; }

    /* ─── SURFACE CARD ────────────────────────────── */
    .surface-card {
        background: #FFFFFF;
        border: 1px solid rgba(99,102,241,0.08);
        border-radius: 18px;
        padding: 1.5rem;
        box-shadow: 0 4px 24px rgba(15,23,42,0.04), 0 1px 6px rgba(99,102,241,0.04);
        margin-bottom: 1.2rem;
        transition: box-shadow 0.2s ease;
    }
    .surface-card:hover {
        box-shadow: 0 8px 32px rgba(99,102,241,0.08), 0 2px 8px rgba(15,23,42,0.04);
    }

    /* ─── EXPANDERS ───────────────────────────────── */
    div[data-testid="stExpander"] {
        background: #FFFFFF !important;
        border: 1px solid #E8EDFF !important;
        border-radius: 14px !important;
        margin-bottom: 0.7rem;
        box-shadow: 0 2px 10px rgba(99,102,241,0.04);
        transition: all 0.18s ease;
    }
    div[data-testid="stExpander"]:hover {
        border-color: #C7D2FE !important;
        box-shadow: 0 4px 16px rgba(99,102,241,0.08) !important;
    }
    div[data-testid="stExpander"] summary {
        font-weight: 600 !important;
        color: #1E293B !important;
        font-size: 0.93rem !important;
    }

    /* ─── BUTTONS ─────────────────────────────────── */
    div.stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 50%, #818CF8 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.22s cubic-bezier(0.16,1,0.3,1) !important;
        box-shadow: 0 4px 14px rgba(79,70,229,0.3) !important;
        letter-spacing: 0.01em !important;
        font-size: 0.9rem !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(79,70,229,0.42) !important;
        filter: brightness(1.05) !important;
    }
    div.stButton > button:active {
        transform: translateY(0px) !important;
    }

    /* ─── INPUTS ──────────────────────────────────── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input {
        background: #FAFBFF !important;
        color: #0F172A !important;
        border: 1.5px solid #E2E8F0 !important;
        border-radius: 11px !important;
        padding: 0.6rem 0.9rem !important;
        font-size: 0.9rem !important;
        transition: all 0.18s ease !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.12) !important;
        background: #FFFFFF !important;
    }
    .stSelectbox > div > div {
        background: #FAFBFF !important;
        border: 1.5px solid #E2E8F0 !important;
        border-radius: 11px !important;
    }

    /* ─── STATUS PILLS ────────────────────────────── */
    .status-pill {
        display: inline-block;
        padding: 0.28rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .pill-approved { background: #ECFDF5; color: #065F46; border: 1.5px solid #6EE7B7; }
    .pill-review { background: #FFFBEB; color: #78350F; border: 1.5px solid #FCD34D; }
    .pill-rejected { background: #FFF1F2; color: #881337; border: 1.5px solid #FDA4AF; }

    /* ─── FILE UPLOADER ───────────────────────────── */
    div[data-testid="stFileUploader"] {
        background: linear-gradient(135deg, #FAFBFF 0%, #F8FAFC 100%);
        border: 2px dashed #A5B4FC;
        border-radius: 18px;
        padding: 1.5rem;
        transition: all 0.22s ease;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #6366F1;
        background: linear-gradient(135deg, #EEF2FF 0%, #F0F7FF 100%);
        box-shadow: 0 4px 20px rgba(99,102,241,0.1);
    }

    /* ─── ALERTS ──────────────────────────────────── */
    .stSuccess { border-radius: 12px !important; }
    .stWarning { border-radius: 12px !important; }
    .stError { border-radius: 12px !important; }
    .stInfo { border-radius: 12px !important; }

    /* ─── SECTION LABEL ───────────────────────────── */
    .section-label {
        font-size: 0.72rem;
        font-weight: 800;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        padding: 0 0.5rem;
        margin: 1rem 0 0.35rem 0;
    }

    /* ─── SCROLLBARS ──────────────────────────────── */
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #F8FAFC; border-radius: 10px; }
    ::-webkit-scrollbar-thumb { background: #C7D2FE; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #818CF8; }

    /* ─── HIDE STREAMLIT CHROME ───────────────────── */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar Branding & Navigation
with st.sidebar:
    # ZERO-GAP brand header flush to top
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 60%, #818CF8 100%);
        margin: -1rem -1rem 0 -1rem;
        padding: 1.4rem 1.2rem 1.1rem 1.2rem;
        display: flex;
        align-items: center;
        gap: 0.85rem;
    ">
        <div style="
            background: rgba(255,255,255,0.22);
            backdrop-filter: blur(8px);
            width: 44px; height: 44px;
            border-radius: 13px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.45rem;
            border: 1.5px solid rgba(255,255,255,0.4);
            box-shadow: 0 4px 14px rgba(0,0,0,0.12);
            flex-shrink: 0;
        ">⚡</div>
        <div>
            <div style="font-weight: 800; font-size: 1.18rem; color: #FFFFFF; letter-spacing: -0.02em; line-height: 1.2;">FinPulse AI</div>
            <div style="font-size: 0.65rem; color: rgba(255,255,255,0.8); font-weight: 700; letter-spacing: 0.1em; margin-top: 0.1rem;">ENTERPRISE EDITION</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height: 0.9rem;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">MAIN MENU</div>', unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "📤 Upload Invoice",
            "📑 Invoices",
            "⏳ Review Queue",
            "🏢 Vendors",
            "📈 Analytics",
            "💬 AI Assistant",
            "📑 Reports"
        ],
        label_visibility="collapsed",
        key="main_navigation_light"
    )

    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    st.divider()

    # System Health Badge
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #F0FDF4 0%, #ECFDF5 100%); border: 1px solid #86EFAC; border-radius: 12px; padding: 0.75rem 1rem; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 8px rgba(5,150,105,0.08);">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <div style="width: 9px; height: 9px; border-radius: 50%; background: #16A34A; box-shadow: 0 0 8px rgba(22,163,74,0.6); animation: pulse 2s infinite;"></div>
                    <span style="font-size: 0.78rem; font-weight: 700; color: #15803D;">Core Engine Live</span>
                </div>
                <span style="font-size: 0.68rem; background: #DCFCE7; color: #166534; font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 6px; border: 1px solid #86EFAC;">v1.0</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Engine Error")
    except:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #FFF1F2 0%, #FFF5F5 100%); border: 1px solid #FDA4AF; border-radius: 12px; padding: 0.75rem 1rem; display: flex; align-items: center; gap: 0.55rem; box-shadow: 0 2px 8px rgba(225,29,72,0.08);">
            <div style="width: 9px; height: 9px; border-radius: 50%; background: #E11D48;"></div>
            <span style="font-size: 0.78rem; font-weight: 700; color: #BE123C;">API Offline — Start Backend</span>
        </div>
        """, unsafe_allow_html=True)

# Helper function to style Plotly charts — premium indigo palette
def format_chart(fig):
    fig.update_layout(
        template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#475569', family='Plus Jakarta Sans', size=12),
        margin=dict(l=20, r=20, t=45, b=20),
        legend=dict(font=dict(color='#334155'), bgcolor='rgba(255,255,255,0.8)', bordercolor='#E2E8F0', borderwidth=1),
        xaxis=dict(gridcolor='#F1F5F9', zerolinecolor='#E2E8F0', linecolor='#E2E8F0', tickfont=dict(color='#64748B')),
        yaxis=dict(gridcolor='#F1F5F9', zerolinecolor='#E2E8F0', linecolor='#E2E8F0', tickfont=dict(color='#64748B')),
        title_font=dict(size=14, color='#1E293B', family='Plus Jakarta Sans')
    )
    return fig

selected_page = page.split(" ", 1)[-1]

# ==========================================
# 1. DASHBOARD PAGE
# ==========================================
if selected_page == "Dashboard":
    st.markdown('<div class="hero-title">Financial Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Real-time artificial intelligence invoice audit, spending velocity, and anomaly detection.</div>', unsafe_allow_html=True)

    # Fetch data
    invoices = []
    analytics = {}
    try:
        inv_res = requests.get(f"{API_URL}/api/invoices", timeout=2)
        ana_res = requests.get(f"{API_URL}/api/analytics/summary", timeout=2)
        if inv_res.status_code == 200:
            invoices = inv_res.json()
        if ana_res.status_code == 200:
            analytics = ana_res.json()
    except Exception:
        pass

    total_invoices = len(invoices)
    total_expenses = sum(safe_float(inv.get("total_amount")) for inv in invoices)
    pending_reviews = len([inv for inv in invoices if inv.get("status") == "review_required"])
    potential_anomalies = len([inv for inv in invoices if inv.get("anomaly_flags")])
    potential_duplicates = analytics.get("duplicates", 0)
    total_issues = potential_anomalies + potential_duplicates

    # Premium Light KPI Cards
    kpi_html = f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Total Invoices</span>
                <div class="kpi-icon-bubble" style="background: #EEF2FF; color: #4F46E5;">📑</div>
            </div>
            <div class="kpi-value">{total_invoices}</div>
            <div class="kpi-badge badge-blue">⚡ Active Portfolio</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Total Spending</span>
                <div class="kpi-icon-bubble" style="background: #ECFDF5; color: #059669;">💳</div>
            </div>
            <div class="kpi-value">₹{total_expenses:,.2f}</div>
            <div class="kpi-badge badge-green">✔ Reconciled Ledger</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Pending Review</span>
                <div class="kpi-icon-bubble" style="background: #FFFBEB; color: #D97706;">⏳</div>
            </div>
            <div class="kpi-value">{pending_reviews}</div>
            <div class="kpi-badge badge-amber">{pending_reviews} Awaiting Action</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-header">
                <span class="kpi-title">Audit Flags</span>
                <div class="kpi-icon-bubble" style="background: #FFF1F2; color: #E11D48;">🛡️</div>
            </div>
            <div class="kpi-value">{total_issues}</div>
            <div class="kpi-badge badge-rose">{potential_anomalies} Anomalies • {potential_duplicates} Dups</div>
        </div>
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)

    # Charts Section
    if total_invoices > 0:
        monthly_totals = defaultdict(float)
        for inv in invoices:
            dt = inv.get("invoice_date")
            amt = safe_float(inv.get("total_amount"))
            if dt and len(dt) >= 7:
                monthly_totals[dt[:7]] += amt
            else:
                monthly_totals["Unspecified"] += amt

        col_trend, col_cat = st.columns([1.6, 1.4])
        with col_trend:
            st.markdown('<div class="surface-card">', unsafe_allow_html=True)
            sorted_months = sorted(monthly_totals.keys())
            month_amounts = [monthly_totals[m] for m in sorted_months]
            fig_bar = px.bar(
                x=sorted_months,
                y=month_amounts,
                labels={"x": "Month", "y": "Expense (₹)"},
                title="<b>Monthly Spending Velocity</b>",
                color_discrete_sequence=['#4F46E5']
            )
            fig_bar.update_traces(marker_line_color='#3730A3', marker_line_width=1, opacity=0.9, marker_cornerradius=6)
            st.plotly_chart(format_chart(fig_bar), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_cat:
            st.markdown('<div class="surface-card">', unsafe_allow_html=True)
            cat_data = analytics.get("categories", {}).get("categories", {})
            if cat_data:
                fig_pie = px.pie(
                    values=list(cat_data.values()),
                    names=list(cat_data.keys()),
                    title="<b>Category Allocation</b>",
                    hole=0.6,
                    color_discrete_sequence=['#4F46E5', '#06B6D4', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#3B82F6']
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent')
                st.plotly_chart(format_chart(fig_pie), use_container_width=True)
            else:
                st.info("No category analytics available.")
            st.markdown('</div>', unsafe_allow_html=True)

    # Recent Invoices Feed
    st.markdown("<div style='font-size: 1.25rem; font-weight: 700; color: #0F172A; margin: 1.5rem 0 0.8rem 0;'>⚡ Recent Stream Invoices</div>", unsafe_allow_html=True)
    if invoices:
        for invoice in invoices[-5:]:
            status = invoice.get('status', 'pending')
            status_class = "pill-approved" if status == "approved" else ("pill-rejected" if status == "rejected" else "pill-review")
            
            with st.expander(f"🔹 {invoice.get('vendor_name') or 'Unnamed Vendor'}  —  ₹{safe_float(invoice.get('total_amount')):,.2f}  |  #{invoice.get('invoice_number') or 'N/A'}"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.write(f"**Invoice ID:** `{invoice.get('id')}`")
                    st.write(f"**Vendor:** {invoice.get('vendor_name')}")
                    st.write(f"**Date:** {invoice.get('invoice_date') or 'N/A'}")
                with c2:
                    st.write(f"**Category:** `{invoice.get('category') or 'Other'}`")
                    st.write(f"**AI Confidence:** {invoice.get('confidence_score', 0):.1%}")
                    st.write(f"**Duplicate Status:** `{invoice.get('duplicate_status')}`")
                with c3:
                    st.markdown(f"**Status:** <span class='status-pill {status_class}'>{status}</span>", unsafe_allow_html=True)
                    if invoice.get('anomaly_flags'):
                        st.warning(f"⚠️ {len(invoice['anomaly_flags'])} Anomalies Flagged")
    else:
        st.markdown("""
        <div style="background: #FFFFFF; border: 1.5px dashed #CBD5E1; border-radius: 16px; padding: 2.8rem; text-align: center; box-shadow: 0 4px 14px rgba(15, 23, 42, 0.02);">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📥</div>
            <div style="font-weight: 700; color: #0F172A; font-size: 1.15rem;">No Invoices Processed Yet</div>
            <div style="color: #64748B; font-size: 0.9rem; margin-top: 0.3rem;">Upload your first PDF or image invoice to activate automated extraction and intelligence.</div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 2. UPLOAD INVOICE PAGE
# ==========================================
elif selected_page == "Upload Invoice":
    st.markdown('<div class="hero-title">Ingest Invoice Document</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Upload digital PDFs or receipts. The engine executes text extraction, OCR fallback, Pydantic validation, and categorization.</div>', unsafe_allow_html=True)

    c_upload, c_info = st.columns([1.3, 0.7])
    with c_upload:
        st.markdown('<div class="surface-card">', unsafe_allow_html=True)
        uploaded_file = st.file_uploader(
            "Upload your invoice file",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            help="Supported: PDF, PNG, JPG, JPEG (Up to 10MB)",
            key="upload_invoice_light"
        )

        if uploaded_file:
            st.markdown(f"""
            <div style="background: #EEF2FF; border: 1px solid #C7D2FE; border-radius: 12px; padding: 1rem; margin: 1rem 0;">
                <div style="font-weight: 700; color: #3730A3;">📁 {uploaded_file.name}</div>
                <div style="color: #6366F1; font-size: 0.85rem; margin-top: 0.2rem;">Size: {uploaded_file.size / 1024:.1f} KB | Type: {uploaded_file.type}</div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("🚀 Process with AI Intelligence", type="primary", key="btn_run_process_light"):
                with st.spinner("Extracting text, validating with Pydantic, checking anomalies..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                        res = requests.post(f"{API_URL}/api/invoices/upload", files=files)
                        if res.status_code == 200:
                            data = res.json()
                            if data.get("warning"):
                                st.warning(f"⚠️ {data['warning']}")
                            else:
                                st.success("🎉 Invoice processed and recorded successfully!")
                            st.json(data.get("invoice", {}))
                        else:
                            st.error(f"Upload failed: {res.text}")
                    except Exception as err:
                        st.error(f"Error connecting to backend: {str(err)}")
        st.markdown('</div>', unsafe_allow_html=True)

    with c_info:
        st.markdown("""
        <div class="surface-card">
            <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; margin-bottom: 0.8rem;">⚡ Automated Pipeline</div>
            <div style="color: #475569; font-size: 0.88rem; line-height: 1.7;">
                ✔ <b>Document Sanitization</b> & SHA-256 Hashing<br>
                ✔ <b>Dual Extraction:</b> PyMuPDF Native + Tesseract OCR<br>
                ✔ <b>AI LLM / Heuristic Engine</b> structured JSON output<br>
                ✔ <b>Pydantic Strict Schema</b> + GSTIN Format Validation<br>
                ✔ <b>Cross-checking:</b> Subtotal + Tax vs Total calculation<br>
                ✔ <b>Duplicate & Statistical Anomaly</b> tagging
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# 3. INVOICES DIRECTORY PAGE
# ==========================================
elif selected_page == "Invoices":
    st.markdown('<div class="hero-title">Invoices Repository</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Comprehensive ledger of all uploaded invoices, line items, and audit data.</div>', unsafe_allow_html=True)

    try:
        inv_res = requests.get(f"{API_URL}/api/invoices", timeout=3)
        if inv_res.status_code == 200:
            invoices = inv_res.json()
            if invoices:
                col_search, col_clean = st.columns([0.7, 0.3])
                with col_search:
                    search_query = st.text_input("🔍 Search by Vendor or Invoice Number", placeholder="e.g. Acme, INV-1002")
                with col_clean:
                    st.markdown("<div style='height: 1.7rem;'></div>", unsafe_allow_html=True)
                    unnamed_count = len([inv for inv in invoices if not inv.get("vendor_name") and not inv.get("total_amount")])
                    if unnamed_count > 0:
                        if st.button(f"🧹 Delete {unnamed_count} Empty Invoices", key="btn_clean_empty", help="Remove invoices that failed extraction"):
                            deleted_count = 0
                            for inv in invoices:
                                if not inv.get("vendor_name") and not inv.get("total_amount"):
                                    requests.delete(f"{API_URL}/api/invoices/{inv.get('id')}")
                                    deleted_count += 1
                            st.success(f"Deleted {deleted_count} empty records!")
                            st.rerun()

                filtered = [
                    inv for inv in invoices 
                    if not search_query or search_query.lower() in (inv.get("vendor_name") or "").lower() or search_query.lower() in (inv.get("invoice_number") or "").lower()
                ]

                st.caption(f"Showing {len(filtered)} of {len(invoices)} total invoices")

                for inv in filtered:
                    status = inv.get('status', 'pending')
                    status_class = "pill-approved" if status == "approved" else ("pill-rejected" if status == "rejected" else "pill-review")
                    
                    with st.expander(f"📑 {inv.get('vendor_name') or 'Unnamed'} — ₹{safe_float(inv.get('total_amount')):,.2f} (#{inv.get('invoice_number') or 'N/A'})"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Invoice ID:** `{inv.get('id')}`")
                            st.write(f"**Vendor Name:** {inv.get('vendor_name') or 'N/A'}")
                            st.write(f"**GSTIN:** `{inv.get('gstin') or 'N/A'}`")
                            st.write(f"**Date:** {inv.get('invoice_date') or 'N/A'}")
                            st.write(f"**Subtotal:** ₹{safe_float(inv.get('subtotal')):,.2f}")
                            st.write(f"**Tax Amount:** ₹{safe_float(inv.get('tax_amount')):,.2f}")
                            st.write(f"**Total Amount:** ₹{safe_float(inv.get('total_amount')):,.2f}")

                        with col2:
                            st.markdown(f"**Status:** <span class='status-pill {status_class}'>{status}</span>", unsafe_allow_html=True)
                            st.write(f"**Category:** `{inv.get('category') or 'Other'}`")
                            st.write(f"**Confidence:** {inv.get('confidence_score', 0):.1%}")
                            st.write(f"**Duplicate Check:** `{inv.get('duplicate_status')}`")
                            if inv.get('anomaly_flags'):
                                for a in inv['anomaly_flags']:
                                    st.warning(f"⚠️ {a}")
                        
                        # Actions: Quick Edit + Delete
                        col_edit, col_del = st.columns([0.8, 0.2])
                        with col_edit:
                            with st.expander("✏️ Quick Modify Invoice"):
                                e1, e2 = st.columns(2)
                                with e1:
                                    edit_ven = st.text_input("Vendor", inv.get('vendor_name') or '', key=f"inv_ven_{inv.get('id')}")
                                    edit_amt = st.number_input("Amount (₹)", value=safe_float(inv.get('total_amount')), key=f"inv_amt_{inv.get('id')}")
                                with e2:
                                    current_cat = inv.get('category') or 'Other'
                                    c_idx = settings.EXPENSE_CATEGORIES.index(current_cat) if current_cat in settings.EXPENSE_CATEGORIES else 0
                                    edit_cat = st.selectbox("Category", settings.EXPENSE_CATEGORIES, index=c_idx, key=f"inv_cat_{inv.get('id')}")
                                
                                if st.button("Save Changes", key=f"inv_save_{inv.get('id')}"):
                                    try:
                                        up_res = requests.put(f"{API_URL}/api/invoices/{inv.get('id')}", json={
                                            "vendor_name": edit_ven,
                                            "total_amount": edit_amt,
                                            "category": edit_cat
                                        })
                                        if up_res.status_code == 200:
                                            st.success("Updated!")
                                            st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        with col_del:
                            if st.button("🗑️ Delete", key=f"inv_del_{inv.get('id')}", help="Permanently delete this invoice"):
                                try:
                                    del_res = requests.delete(f"{API_URL}/api/invoices/{inv.get('id')}")
                                    if del_res.status_code == 200:
                                        st.success("Invoice deleted!")
                                        st.rerun()
                                    else:
                                        st.error("Delete failed")
                                except Exception as e:
                                    st.error(f"Error: {e}")
            else:
                st.info("No invoices found in storage.")
    except Exception as e:
        st.error(f"Could not load invoices: {e}")

# ==========================================
# 4. REVIEW QUEUE PAGE
# ==========================================
elif selected_page == "Review Queue":
    st.markdown('<div class="hero-title">Invoice Review Queue</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Audit desk for invoices requiring human approval due to anomaly flags or low confidence scores.</div>', unsafe_allow_html=True)

    try:
        inv_res = requests.get(f"{API_URL}/api/invoices", timeout=3)
        if inv_res.status_code == 200:
            invoices = inv_res.json()
            needs_review = [
                inv for inv in invoices 
                if inv.get("status") == "review_required" or inv.get("anomaly_flags") or (inv.get("confidence_score", 1.0) < 0.8)
            ]

            if needs_review:
                st.markdown(f"""
                <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 12px; padding: 1rem; margin-bottom: 1.5rem;">
                    <span style="font-weight: 700; color: #B45309;">⚠️ {len(needs_review)} Invoices Require Manual Review</span>
                </div>
                """, unsafe_allow_html=True)

                for inv in needs_review:
                    with st.expander(f"⚠️ {inv.get('vendor_name') or 'Unknown'} — ₹{safe_float(inv.get('total_amount')):,.2f} (#{inv.get('invoice_number') or 'N/A'})"):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.write(f"**Invoice ID:** `{inv.get('id')}`")
                            st.write(f"**Vendor Name:** {inv.get('vendor_name')}")
                            st.write(f"**Amount:** ₹{safe_float(inv.get('total_amount')):,.2f}")
                            st.write(f"**Date:** {inv.get('invoice_date') or 'N/A'}")
                        with c2:
                            st.write(f"**Confidence Score:** {inv.get('confidence_score', 0):.1%}")
                            if inv.get('confidence_score', 0) < 0.8:
                                st.warning("⚠ Low Confidence Detection")
                            if inv.get('anomaly_flags'):
                                for an in inv['anomaly_flags']:
                                    st.error(f"🛡️ Flag: {an}")

                        # Inline editing
                        with st.expander("✏️ Edit Extracted Details Before Decision"):
                            ec1, ec2 = st.columns(2)
                            with ec1:
                                rv_vendor = st.text_input("Vendor Name", inv.get('vendor_name') or '', key=f"q_v_{inv.get('id')}")
                                rv_inv_num = st.text_input("Invoice Number", inv.get('invoice_number') or '', key=f"q_num_{inv.get('id')}")
                                rv_date = st.text_input("Invoice Date", inv.get('invoice_date') or '', key=f"q_dt_{inv.get('id')}")
                            with ec2:
                                rv_amt = st.number_input("Total Amount (₹)", value=safe_float(inv.get('total_amount')), key=f"q_amt_{inv.get('id')}")
                                rv_tax = st.number_input("Tax Amount (₹)", value=safe_float(inv.get('tax_amount')), key=f"q_tax_{inv.get('id')}")
                                curr_cat = inv.get('category') or 'Other'
                                c_index = settings.EXPENSE_CATEGORIES.index(curr_cat) if curr_cat in settings.EXPENSE_CATEGORIES else 0
                                rv_cat = st.selectbox("Category", settings.EXPENSE_CATEGORIES, index=c_index, key=f"q_cat_{inv.get('id')}")

                            if st.button("💾 Save Updates", key=f"q_save_{inv.get('id')}"):
                                try:
                                    payload = {
                                        "vendor_name": rv_vendor,
                                        "invoice_number": rv_inv_num,
                                        "invoice_date": rv_date,
                                        "total_amount": rv_amt,
                                        "tax_amount": rv_tax,
                                        "category": rv_cat
                                    }
                                    up = requests.put(f"{API_URL}/api/invoices/{inv.get('id')}", json=payload)
                                    if up.status_code == 200:
                                        st.success("Details updated!")
                                        st.rerun()
                                except Exception as ex:
                                    st.error(f"Error: {ex}")

                        # Actions
                        b1, b2, b3 = st.columns(3)
                        with b1:
                            if st.button(f"✅ Approve", key=f"app_{inv.get('id')}", type="primary", use_container_width=True):
                                requests.post(f"{API_URL}/api/invoices/{inv.get('id')}/approve")
                                st.rerun()
                        with b2:
                            if st.button(f"❌ Reject", key=f"rej_{inv.get('id')}", use_container_width=True):
                                requests.post(f"{API_URL}/api/invoices/{inv.get('id')}/reject")
                                st.rerun()
                        with b3:
                            if st.button(f"🗑️ Delete", key=f"q_del_{inv.get('id')}", use_container_width=True):
                                requests.delete(f"{API_URL}/api/invoices/{inv.get('id')}")
                                st.rerun()
            else:
                st.markdown("""
                <div style="background: #F0FDF4; border: 1px solid #BBF7D0; border-radius: 14px; padding: 2.5rem; text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 0.3rem;">🎉</div>
                    <div style="font-weight: 700; color: #15803D; font-size: 1.15rem;">Review Queue is Empty</div>
                    <div style="color: #64748B; font-size: 0.9rem;">All invoices are approved or processed without pending issues.</div>
                </div>
                """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error fetching review queue: {e}")

# ==========================================
# 5. VENDOR INTELLIGENCE PAGE
# ==========================================
elif selected_page == "Vendors":
    st.markdown('<div class="hero-title">Vendor Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Supplier relationships, spending history, risk profiling, and category concentration.</div>', unsafe_allow_html=True)

    try:
        ven_res = requests.get(f"{API_URL}/api/vendors", timeout=3)
        if ven_res.status_code == 200:
            vendors = ven_res.json()
            if vendors:
                v_total_spent = sum(safe_float(v.get("total_spending")) for v in vendors)
                v_total_invoices = sum(int(v.get("total_invoices", 0) or 0) for v in vendors)

                st.markdown(f"""
                <div class="kpi-container" style="grid-template-columns: repeat(3, 1fr);">
                    <div class="kpi-card">
                        <div class="kpi-header"><span class="kpi-title">Active Vendors</span><div class="kpi-icon-bubble" style="background: #EEF2FF; color: #4F46E5;">🏢</div></div>
                        <div class="kpi-value">{len(vendors)}</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-header"><span class="kpi-title">Total Disbursals</span><div class="kpi-icon-bubble" style="background: #ECFDF5; color: #059669;">💳</div></div>
                        <div class="kpi-value">₹{v_total_spent:,.2f}</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-header"><span class="kpi-title">Invoices Processed</span><div class="kpi-icon-bubble" style="background: #EFF6FF; color: #2563EB;">📑</div></div>
                        <div class="kpi-value">{v_total_invoices}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                for v in vendors:
                    with st.expander(f"🏢 {v.get('name', 'Unknown')} — Total: ₹{safe_float(v.get('total_spending')):,.2f} ({v.get('total_invoices', 0)} Invoices)"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Total Invoices:** {v.get('total_invoices', 0)}")
                            st.write(f"**Average Ticket Size:** ₹{safe_float(v.get('average_invoice')):,.2f}")
                            st.write(f"**First Transaction:** {v.get('first_invoice') or 'N/A'}")
                            st.write(f"**Latest Transaction:** {v.get('last_invoice') or 'N/A'}")
                        with col2:
                            st.write(f"**Category Breakdown:** {', '.join(v.get('categories', [])) or 'General'}")

                        try:
                            t_res = requests.get(f"{API_URL}/api/vendors/{v.get('name')}/trends", timeout=2)
                            if t_res.status_code == 200:
                                t_data = t_res.json().get("monthly_spending", {})
                                if t_data:
                                    fig_v = px.line(
                                        x=list(t_data.keys()),
                                        y=list(t_data.values()),
                                        title=f"Monthly Spend with {v.get('name')}",
                                        markers=True,
                                        color_discrete_sequence=['#4F46E5']
                                    )
                                    st.plotly_chart(format_chart(fig_v), use_container_width=True)
                        except Exception:
                            pass
            else:
                st.info("No vendor profiles generated yet. Upload invoices to build vendor intelligence.")
    except Exception as e:
        st.error(f"Error fetching vendors: {e}")

# ==========================================
# 6. ANALYTICS PAGE
# ==========================================
elif selected_page == "Analytics":
    st.markdown('<div class="hero-title">Spend Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Deep financial breakdowns, anomaly patterns, and vendor concentration distributions.</div>', unsafe_allow_html=True)

    try:
        ana_res = requests.get(f"{API_URL}/api/analytics/summary", timeout=3)
        cat_res = requests.get(f"{API_URL}/api/analytics/categories", timeout=3)
        
        category_data = cat_res.json() if cat_res.status_code == 200 else {}

        if category_data.get("summary"):
            top_cats = category_data.get("top_categories", [])

            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="surface-card">', unsafe_allow_html=True)
                if top_cats:
                    fig_top = px.bar(
                        x=[c["category"] for c in top_cats],
                        y=[c["total_amount"] for c in top_cats],
                        labels={"x": "Category", "y": "Amount (₹)"},
                        title="<b>Top Spending Categories</b>",
                        color_discrete_sequence=['#4F46E5']
                    )
                    st.plotly_chart(format_chart(fig_top), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            with c2:
                st.markdown('<div class="surface-card">', unsafe_allow_html=True)
                try:
                    ven_top = requests.get(f"{API_URL}/api/vendors/top?limit=5", timeout=2)
                    if ven_top.status_code == 200:
                        v_list = ven_top.json()
                        if v_list:
                            fig_vtop = px.bar(
                                x=[v.get("name", "Unknown") for v in v_list],
                                y=[v.get("total_spending", 0) for v in v_list],
                                labels={"x": "Vendor", "y": "Spend (₹)"},
                                title="<b>Top 5 Vendors by Spend Volume</b>",
                                color_discrete_sequence=['#059669']
                            )
                            st.plotly_chart(format_chart(fig_vtop), use_container_width=True)
                except:
                    pass
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No analytics available. Ingest invoices to generate charts.")
    except Exception as e:
        st.error(f"Error loading analytics: {e}")

# ==========================================
# 7. AI ASSISTANT PAGE
# ==========================================
elif selected_page == "AI Assistant":
    st.markdown('<div class="hero-title">Financial AI Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Ask questions in natural language. Powered by deterministic Python queries over JSON records to guarantee 0% financial hallucination.</div>', unsafe_allow_html=True)

    if "ai_assistant_query" not in st.session_state:
        st.session_state["ai_assistant_query"] = ""

    st.markdown('<div class="surface-card">', unsafe_allow_html=True)
    st.markdown("<div style='font-size: 0.85rem; font-weight: 700; color: #4F46E5; margin-bottom: 0.6rem;'>💡 QUICK PROMPT SUGGESTIONS</div>", unsafe_allow_html=True)
    sample_queries = [
        "How much did we spend on software this month?",
        "Which vendor received the highest payment?",
        "Show invoices above ₹1 lakh",
        "What are our travel expenses?",
        "Which invoices need review?"
    ]

    cols = st.columns(len(sample_queries))
    triggered_query = None
    for idx, prompt_text in enumerate(sample_queries):
        with cols[idx]:
            if st.button(prompt_text, key=f"chip_light_{idx}", use_container_width=True):
                triggered_query = prompt_text
                st.session_state["ai_assistant_query"] = prompt_text

    query_input = st.text_input(
        "Ask anything about your expenses...",
        value=st.session_state.get("ai_assistant_query", ""),
        placeholder="e.g. How much did we spend on software this month? Or Which vendor received highest payment?",
        key="ai_assistant_input_text"
    )

    col_btn, _ = st.columns([0.3, 0.7])
    with col_btn:
        run_query_btn = st.button("⚡ Query AI Engine", type="primary", key="btn_run_ai_light", use_container_width=True)

    active_query = triggered_query or (query_input if run_query_btn else None)

    if active_query:
        st.session_state["ai_assistant_query"] = active_query
        with st.spinner("Classifying intent & calculating exact ledger amounts..."):
            try:
                res = requests.post(f"{API_URL}/api/assistant/query", json={"query": active_query}, timeout=10)
                if res.status_code == 200:
                    out = res.json()
                    st.session_state["ai_assistant_last_result"] = out
                else:
                    st.error("Failed to query AI assistant.")
            except Exception as ex:
                st.error(f"Error connecting to backend: {ex}")

    # Display result if available in session state
    if "ai_assistant_last_result" in st.session_state:
        out = st.session_state["ai_assistant_last_result"]
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #F8FAFC 0%, #EEF2FF 100%); border: 1.5px solid #C7D2FE; border-radius: 14px; padding: 1.4rem; margin-top: 1.4rem; box-shadow: 0 4px 16px rgba(99,102,241,0.06);">
            <div style="font-size: 0.78rem; font-weight: 700; color: #4F46E5; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem;">
                🎯 Intent Identified: <span style="background: #E0E7FF; padding: 0.15rem 0.5rem; border-radius: 6px;">{out.get('intent')}</span>
            </div>
            <div style="font-size: 1.15rem; color: #0F172A; font-weight: 700; line-height: 1.5; margin-top: 0.3rem;">
                💬 {out.get('response')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if out.get("result"):
            with st.expander("🔍 View Raw Calculated Ledger Data"):
                st.json(out["result"])

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 8. REPORTS PAGE
# ==========================================
elif selected_page == "Reports":
    st.markdown('<div class="hero-title">Report Center & Exports</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Generate audit-ready PDF dossiers, comprehensive multi-tab Excel sheets, and CSV dumps.</div>', unsafe_allow_html=True)

    r_col1, r_col2 = st.columns(2)
    with r_col1:
        st.markdown("""
        <div class="surface-card">
            <div style="font-weight: 700; font-size: 1.15rem; color: #0F172A;">📑 Monthly Audit Dossier (PDF & Excel)</div>
            <div style="color: #64748B; font-size: 0.88rem; margin-top: 0.2rem; margin-bottom: 1.2rem;">Includes summary, itemized invoices, category concentration, vendor spending, anomalies, and duplicates.</div>
        """, unsafe_allow_html=True)

        month_filter = st.text_input("Month Target (YYYY-MM)", value="", placeholder="Leave empty for current month", key="target_report_month_light")
        if st.button("Generate Monthly Report Pack", key="btn_gen_monthly_pack_light"):
            with st.spinner("Generating ReportLab PDF & openpyxl Multi-Tab Excel..."):
                try:
                    params = {"month": month_filter} if month_filter else {}
                    r_res = requests.post(f"{API_URL}/api/reports/monthly", params=params, timeout=30)
                    if r_res.status_code == 200:
                        r_data = r_res.json()
                        st.success(f"Generated successfully for {r_data['month']}!")
                        
                        pdf_path = Path(r_data['pdf_path'])
                        if pdf_path.exists():
                            with open(pdf_path, "rb") as f:
                                st.download_button(
                                    label="📥 Download PDF Audit Report",
                                    data=f.read(),
                                    file_name=pdf_path.name,
                                    mime="application/pdf",
                                    key="pdf_dl_pack_light"
                                )
                        
                        excel_path = Path(r_data['excel_path'])
                        if excel_path.exists():
                            with open(excel_path, "rb") as f:
                                st.download_button(
                                    label="📊 Download Excel Spreadsheet (.xlsx)",
                                    data=f.read(),
                                    file_name=excel_path.name,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key="excel_dl_pack_light"
                                )
                except Exception as ex:
                    st.error(f"Error: {ex}")
        st.markdown("</div>", unsafe_allow_html=True)

    with r_col2:
        st.markdown("""
        <div class="surface-card">
            <div style="font-weight: 700; font-size: 1.15rem; color: #0F172A;">📊 Raw Invoices CSV Dump</div>
            <div style="color: #64748B; font-size: 0.88rem; margin-top: 0.2rem; margin-bottom: 1.2rem;">Export complete data table with all metadata, confidence scores, and statuses for external tools.</div>
        """, unsafe_allow_html=True)

        if st.button("Generate Invoices CSV", key="btn_gen_csv_dump_light"):
            with st.spinner("Generating CSV table..."):
                try:
                    c_res = requests.get(f"{API_URL}/api/reports/csv", timeout=20)
                    if c_res.status_code == 200:
                        c_path = Path(c_res.json()['csv_path'])
                        if c_path.exists():
                            with open(c_path, "rb") as f:
                                st.download_button(
                                    label="📥 Download CSV File (.csv)",
                                    data=f.read(),
                                    file_name=c_path.name,
                                    mime="text/csv",
                                    key="csv_dl_dump_light"
                                )
                except Exception as ex:
                    st.error(f"Error: {ex}")
        st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)
st.markdown("""
<div style="
    border-top: 1px solid rgba(99,102,241,0.12);
    padding: 1.2rem 0 0.5rem 0;
    display: flex; justify-content: space-between; align-items: center;
    flex-wrap: wrap; gap: 0.8rem;
">
    <div style="display: flex; align-items: center; gap: 0.6rem;">
        <div style="background: linear-gradient(135deg, #4F46E5, #6366F1); width: 22px; height: 22px; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 0.75rem;">⚡</div>
        <span style="font-weight: 700; color: #475569; font-size: 0.8rem;">FinPulse AI</span>
        <span style="color: #CBD5E1; font-size: 0.8rem;">•</span>
        <span style="color: #94A3B8; font-size: 0.78rem;">Enterprise Invoice Intelligence</span>
    </div>
    <div style="display: flex; gap: 0.45rem; flex-wrap: wrap; align-items: center;">
        <span style="background: #EEF2FF; color: #4338CA; font-size: 0.68rem; font-weight: 700; padding: 0.2rem 0.55rem; border-radius: 6px; border: 1px solid #C7D2FE;">FastAPI</span>
        <span style="background: #EEF2FF; color: #4338CA; font-size: 0.68rem; font-weight: 700; padding: 0.2rem 0.55rem; border-radius: 6px; border: 1px solid #C7D2FE;">Streamlit</span>
        <span style="background: #F0FDF4; color: #166534; font-size: 0.68rem; font-weight: 700; padding: 0.2rem 0.55rem; border-radius: 6px; border: 1px solid #BBF7D0;">ReportLab</span>
        <span style="background: #FFFBEB; color: #92400E; font-size: 0.68rem; font-weight: 700; padding: 0.2rem 0.55rem; border-radius: 6px; border: 1px solid #FDE68A;">Zero DB JSON</span>
    </div>
</div>
""", unsafe_allow_html=True)

