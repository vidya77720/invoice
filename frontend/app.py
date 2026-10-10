import streamlit as st
import requests
import os
from pathlib import Path
import sys

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

try:
    from app.core.config import settings
except:
    # Fallback if config import fails
    class Settings:
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
    settings = Settings()

# Page config
st.set_page_config(
    page_title="AI Invoice Intelligence",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("📄 Invoice Intelligence")
    
    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Upload Invoice",
            "Invoices",
            "Review Queue",
            "Vendors",
            "Analytics",
            "AI Assistant",
            "Reports"
        ],
        key="main_navigation"
    )
    
    st.divider()
    
    # API Status
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        if response.status_code == 200:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Error")
    except:
        st.warning("⚠️ API Not Connected")

# Dashboard Page
if page == "Dashboard":
    st.markdown('<h1 class="main-header">Dashboard</h1>', unsafe_allow_html=True)
    
    # Fetch data
    try:
        invoices_response = requests.get(f"{API_URL}/api/invoices", timeout=2)
        analytics_response = requests.get(f"{API_URL}/api/analytics/summary", timeout=2)
        
        if invoices_response.status_code == 200:
            invoices = invoices_response.json()
        else:
            invoices = []
        
        if analytics_response.status_code == 200:
            analytics = analytics_response.json()
        else:
            analytics = {}
    except:
        invoices = []
        analytics = {}
    
    # Calculate metrics
    total_invoices = len(invoices)
    total_expenses = sum(inv.get("total_amount", 0) or 0 for inv in invoices)
    pending_reviews = len([inv for inv in invoices if inv.get("status") == "review_required"])
    potential_anomalies = len([inv for inv in invoices if inv.get("anomaly_flags")])
    potential_duplicates = analytics.get("duplicates", 0)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Invoices", total_invoices)
    
    with col2:
        st.metric("Total Expenses", f"₹{total_expenses:,.2f}")
    
    with col3:
        st.metric("Pending Reviews", pending_reviews)
    
    with col4:
        st.metric("Issues", potential_anomalies + potential_duplicates)
    
    st.divider()
    
    # Recent Activity
    st.subheader("Recent Invoices")
    if invoices:
        for invoice in invoices[-5:]:  # Show last 5
            with st.expander(f"{invoice.get('vendor_name', 'Unknown')} - ₹{invoice.get('total_amount', 0):,.2f}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Invoice ID:** {invoice.get('id')}")
                    st.write(f"**Invoice Number:** {invoice.get('invoice_number')}")
                    st.write(f"**Date:** {invoice.get('invoice_date')}")
                    st.write(f"**Category:** {invoice.get('category')}")
                
                with col2:
                    st.write(f"**Status:** {invoice.get('status')}")
                    st.write(f"**Confidence:** {invoice.get('confidence_score', 0):.2%}")
                    st.write(f"**Duplicate:** {invoice.get('duplicate_status')}")
                    if invoice.get('anomaly_flags'):
                        st.warning(f"Anomalies: {len(invoice['anomaly_flags'])}")
    else:
        st.info("No invoices yet. Upload your first invoice to get started!")
    
    # Charts
    if total_invoices > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Category Breakdown")
            categories = analytics.get("categories", {}).get("categories", {})
            if categories:
                import plotly.express as px
                fig = px.pie(
                    values=list(categories.values()),
                    names=list(categories.keys()),
                    title="Expenses by Category"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No category data available")
        
        with col2:
            st.subheader("Top Vendors")
            try:
                vendors_response = requests.get(f"{API_URL}/api/vendors/top?limit=5", timeout=2)
                if vendors_response.status_code == 200:
                    vendors = vendors_response.json()
                    if vendors:
                        vendor_names = [v.get("name", "Unknown") for v in vendors]
                        vendor_amounts = [v.get("total_spending", 0) for v in vendors]
                        
                        import plotly.express as px
                        fig = px.bar(
                            x=vendor_names,
                            y=vendor_amounts,
                            title="Top 5 Vendors by Spending"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No vendor data available")
            except:
                st.info("Could not fetch vendor data")

# Upload Invoice Page
elif page == "Upload Invoice":
    st.markdown('<h1 class="main-header">Upload Invoice</h1>', unsafe_allow_html=True)
    
    st.info("Upload PDF or image invoices for automatic processing")
    
    uploaded_file = st.file_uploader(
        "Choose an invoice file",
        type=['pdf', 'png', 'jpg', 'jpeg'],
        help="Supported formats: PDF, PNG, JPG, JPEG",
        key="upload_invoice_file"
    )
    
    if uploaded_file:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Filename:** {uploaded_file.name}")
            st.write(f"**Size:** {uploaded_file.size / 1024:.2f} KB")
            st.write(f"**Type:** {uploaded_file.type}")
        
        with col2:
            if st.button("Process Invoice", type="primary", key="btn_process_invoice"):
                with st.spinner("Processing invoice..."):
                    try:
                        # Upload to API
                        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
                        response = requests.post(f"{API_URL}/api/invoices/upload", files=files)
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success("✅ Invoice uploaded successfully!")
                            st.json(result["invoice"])
                        else:
                            st.error(f"❌ Upload failed: {response.text}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
    
    st.divider()
    st.info("Invoice processing includes: PDF extraction, OCR, AI analysis, validation, and categorization")
    st.success("✅ Upload feature is now available!")

# Invoices Page
elif page == "Invoices":
    st.markdown('<h1 class="main-header">All Invoices</h1>', unsafe_allow_html=True)
    
    try:
        response = requests.get(f"{API_URL}/api/invoices", timeout=2)
        if response.status_code == 200:
            invoices = response.json()
            
            if invoices:
                for invoice in invoices:
                    with st.expander(f"{invoice.get('vendor_name', 'Unknown')} - {invoice.get('invoice_number', 'N/A')}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Invoice ID:** {invoice.get('id')}")
                            st.write(f"**Invoice Number:** {invoice.get('invoice_number')}")
                            st.write(f"**Date:** {invoice.get('invoice_date')}")
                            st.write(f"**Total:** ₹{invoice.get('total_amount', 0):,.2f}")
                        
                        with col2:
                            st.write(f"**Status:** {invoice.get('status')}")
                            st.write(f"**Category:** {invoice.get('category')}")
                            st.write(f"**Confidence:** {invoice.get('confidence_score', 0):.2%}")
                            if invoice.get('confidence_score', 0) < 0.8:
                                st.warning("⚠ Low Confidence")
                        
                        # Edit section
                        with st.expander("Edit Invoice"):
                            edited_vendor = st.text_input("Vendor Name", invoice.get('vendor_name', ''), key=f"vendor_{invoice.get('id')}")
                            edited_amount = st.number_input("Total Amount", value=invoice.get('total_amount', 0) or 0, key=f"amount_{invoice.get('id')}")
                            edited_category = st.selectbox("Category", settings.EXPENSE_CATEGORIES, index=settings.EXPENSE_CATEGORIES.index(invoice.get('category', 'Other')) if invoice.get('category') in settings.EXPENSE_CATEGORIES else 0, key=f"category_{invoice.get('id')}")
                            
                            if st.button("Save Changes", key=f"save_{invoice.get('id')}"):
                                try:
                                    updates = {
                                        "vendor_name": edited_vendor,
                                        "total_amount": edited_amount,
                                        "category": edited_category
                                    }
                                    resp = requests.put(f"{API_URL}/api/invoices/{invoice.get('id')}", json=updates)
                                    if resp.status_code == 200:
                                        st.success("Changes saved!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to save changes")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
            else:
                st.info("No invoices yet. Upload invoices to see them here.")
        else:
            st.error("Failed to fetch invoices")
    except:
        st.warning("API not connected")

# Review Queue Page
elif page == "Review Queue":
    st.markdown('<h1 class="main-header">Review Queue</h1>', unsafe_allow_html=True)
    
    try:
        response = requests.get(f"{API_URL}/api/invoices", timeout=2)
        if response.status_code == 200:
            invoices = response.json()
            
            # Filter invoices needing review
            review_invoices = [
                inv for inv in invoices 
                if inv.get("status") == "review_required" or inv.get("anomaly_flags")
            ]
            
            if review_invoices:
                st.info(f"{len(review_invoices)} invoices require review")
                
                for invoice in review_invoices:
                    with st.expander(f"{invoice.get('vendor_name', 'Unknown')} - {invoice.get('invoice_number', 'N/A')}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**Invoice ID:** {invoice.get('id')}")
                            st.write(f"**Vendor:** {invoice.get('vendor_name')}")
                            st.write(f"**Amount:** ₹{invoice.get('total_amount', 0):,.2f}")
                        
                        with col2:
                            st.write(f"**Confidence:** {invoice.get('confidence_score', 0):.2%}")
                            if invoice.get('confidence_score', 0) < 0.8:
                                st.warning("⚠ Low Confidence")
                            
                            if invoice.get('anomaly_flags'):
                                st.warning(f"⚠ Anomalies: {len(invoice['anomaly_flags'])}")
                                for anomaly in invoice['anomaly_flags']:
                                    st.warning(f"  • {anomaly}")
                        
                        with col3:
                            st.write(f"**Status:** {invoice.get('status')}")
                            st.write(f"**Duplicate:** {invoice.get('duplicate_status')}")
                            
                            # Action buttons
                            col_a, col_b = st.columns(2)
                            with col_a:
                                if st.button(f"Approve {invoice.get('id')}", key=f"approve_{invoice.get('id')}"):
                                    try:
                                        resp = requests.post(f"{API_URL}/api/invoices/{invoice.get('id')}/approve")
                                        if resp.status_code == 200:
                                            st.success("Approved!")
                                            st.rerun()
                                    except:
                                        st.error("Failed to approve")
                            
                            with col_b:
                                if st.button(f"Reject {invoice.get('id')}", key=f"reject_{invoice.get('id')}"):
                                    try:
                                        resp = requests.post(f"{API_URL}/api/invoices/{invoice.get('id')}/reject")
                                        if resp.status_code == 200:
                                            st.success("Rejected!")
                                            st.rerun()
                                    except:
                                        st.error("Failed to reject")
            else:
                st.success("✅ No invoices require review")
        else:
            st.error("Failed to fetch invoices")
    except:
        st.warning("API not connected")

# Vendors Page
elif page == "Vendors":
    st.markdown('<h1 class="main-header">Vendor Intelligence</h1>', unsafe_allow_html=True)
    
    try:
        response = requests.get(f"{API_URL}/api/vendors", timeout=2)
        if response.status_code == 200:
            vendors = response.json()
            
            if vendors:
                st.info(f"Total vendors: {len(vendors)}")
                
                # Vendor metrics
                total_spending = sum(v.get("total_spending", 0) for v in vendors)
                total_invoices = sum(v.get("total_invoices", 0) for v in vendors)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Vendors", len(vendors))
                with col2:
                    st.metric("Total Vendor Spending", f"₹{total_spending:,.2f}")
                with col3:
                    st.metric("Total Invoices", total_invoices)
                
                st.divider()
                
                # Vendor list
                st.subheader("All Vendors")
                for vendor in vendors:
                    with st.expander(f"{vendor.get('name', 'Unknown')} - ₹{vendor.get('total_spending', 0):,.2f}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Total Invoices:** {vendor.get('total_invoices', 0)}")
                            st.write(f"**Average Invoice:** ₹{vendor.get('average_invoice', 0):,.2f}")
                            st.write(f"**First Invoice:** {vendor.get('first_invoice', 'N/A')}")
                        
                        with col2:
                            st.write(f"**Last Invoice:** {vendor.get('last_invoice', 'N/A')}")
                            st.write(f"**Categories:** {', '.join(vendor.get('categories', []))}")
                        
                        # Vendor trends
                        try:
                            trends_resp = requests.get(f"{API_URL}/api/vendors/{vendor.get('name')}/trends", timeout=2)
                            if trends_resp.status_code == 200:
                                trends = trends_resp.json()
                                if trends.get('monthly_spending'):
                                    st.subheader("Spending Trend")
                                    import plotly.express as px
                                    fig = px.line(
                                        x=list(trends['monthly_spending'].keys()),
                                        y=list(trends['monthly_spending'].values()),
                                        title=f"Monthly Spending - {vendor.get('name')}"
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                        except:
                            pass
            else:
                st.info("No vendor data yet. Process invoices to see vendor analytics.")
        else:
            st.error("Failed to fetch vendors")
    except:
        st.warning("API not connected")

# Analytics Page
elif page == "Analytics":
    st.markdown('<h1 class="main-header">Analytics</h1>', unsafe_allow_html=True)
    
    try:
        analytics_response = requests.get(f"{API_URL}/api/analytics/summary", timeout=2)
        category_response = requests.get(f"{API_URL}/api/analytics/categories", timeout=2)
        
        if analytics_response.status_code == 200:
            analytics = analytics_response.json()
        else:
            analytics = {}
        
        if category_response.status_code == 200:
            category_data = category_response.json()
        else:
            category_data = {}
    except:
        analytics = {}
        category_data = {}
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Invoices", analytics.get("anomalies", {}).get("total_invoices", 0))
    
    with col2:
        st.metric("With Anomalies", analytics.get("anomalies", {}).get("invoices_with_anomalies", 0))
    
    with col3:
        st.metric("Total Vendors", analytics.get("total_vendors", 0))
    
    with col4:
        st.metric("Duplicates", analytics.get("duplicates", 0))
    
    st.divider()
    
    # Category analytics
    if category_data.get("summary"):
        st.subheader("Category Summary")
        summary = category_data["summary"]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Total Amount:** ₹{summary.get('total_amount', 0):,.2f}")
            st.write(f"**Total Invoices:** {summary.get('total_invoices', 0)}")
        
        with col2:
            st.write(f"**Categories:** {len(summary.get('categories', {}))}")
        
        # Top categories chart
        if category_data.get("top_categories"):
            st.subheader("Top Spending Categories")
            top_cats = category_data["top_categories"]
            
            cat_names = [c["category"] for c in top_cats]
            cat_amounts = [c["total_amount"] for c in top_cats]
            
            import plotly.express as px
            fig = px.bar(
                x=cat_names,
                y=cat_amounts,
                title="Top Categories by Spending"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Category trends
        if category_data.get("trends"):
            st.subheader("Category Trends")
            trends = category_data["trends"]
            monthly_data = trends.get("monthly_data", {})
            
            if monthly_data:
                import plotly.express as px
                fig = px.line(
                    x=list(monthly_data.keys()),
                    y=list(monthly_data.values()),
                    title=f"Monthly Spending - {trends.get('category', 'All')}"
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No analytics data available. Process invoices first.")

# AI Assistant Page
elif page == "AI Assistant":
    st.markdown('<h1 class="main-header">AI Expense Assistant</h1>', unsafe_allow_html=True)
    
    st.info("Ask questions about your expenses using natural language")
    
    user_query = st.text_input(
        "Ask a question...",
        placeholder="e.g., How much did we spend on software this month?",
        key="ai_query"
    )
    
    if st.button("Ask", type="primary", key="btn_ask_ai"):
        if user_query:
            with st.spinner("Processing your query..."):
                try:
                    response = requests.post(
                        f"{API_URL}/api/assistant/query",
                        json={"query": user_query},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success("Answer:")
                        st.write(result["response"])
                        
                        if result.get("result"):
                            with st.expander("View Details"):
                                st.json(result["result"])
                    else:
                        st.error("Failed to process query")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a question")
    
    st.divider()
    
    st.subheader("Example Questions:")
    example_questions = [
        "How much did we spend on software this month?",
        "Which vendor received the highest payment?",
        "Show invoices above ₹1 lakh",
        "What are our travel expenses?",
        "Which invoices need review?",
        "What is our total spending?",
        "How many invoices do we have?"
    ]
    
    for question in example_questions:
        st.write(f"• {question}")

# Reports Page
elif page == "Reports":
    st.markdown('<h1 class="main-header">Reports</h1>', unsafe_allow_html=True)
    
    st.info("Generate comprehensive reports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("PDF Reports")
        month = st.text_input("Month (YYYY-MM, leave empty for current)", value="", key="report_month")
        if st.button("Generate Monthly PDF Report", key="btn_gen_monthly_pdf"):
            with st.spinner("Generating PDF report..."):
                try:
                    params = {"month": month} if month else {}
                    response = requests.post(
                        f"{API_URL}/api/reports/monthly",
                        params=params,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ PDF report generated: {result['pdf_path']}")
                        st.info(f"Excel report also generated: {result['excel_path']}")
                    else:
                        st.error("Failed to generate report")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col2:
        st.subheader("Excel/CSV Reports")
        if st.button("Export to CSV", key="btn_export_csv"):
            with st.spinner("Generating CSV export..."):
                try:
                    response = requests.get(f"{API_URL}/api/reports/csv", timeout=30)
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ CSV export generated: {result['csv_path']}")
                    else:
                        st.error("Failed to generate CSV")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

# Footer
st.divider()
st.caption("AI Invoice Intelligence System v1.0 - Built with FastAPI & Streamlit")
