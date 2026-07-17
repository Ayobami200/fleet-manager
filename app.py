import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import os
from datetime import date, datetime, timedelta
from database import SessionLocal, init_db, Vehicle, Expense, Income, Driver
import cloudinary
import cloudinary.uploader


# ── Init ──────────────────────────────────────────────────────────────────────
init_db()

cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"],
    secure = True
)

def get_session():
    return SessionLocal()

session = get_session()

st.set_page_config(
    page_title="FleetIQ — Fleet Manager",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

def check_password():
    """Returns True if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["PASSWORD"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🚛 FleetIQ Login")
            st.text_input(
                "Please enter the access password", type="password", on_change=password_entered, key="password"
            )
            if "password_correct" in st.session_state:
                st.error("😕 Password incorrect")
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

# --- Trigger the check ---
if not check_password():
    st.stop()  # Do not run the rest of the app if not authenticated

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500;600&display=swap');

/* Base */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: #F0F4FA !important;
}
#MainMenu, footer, { visibility: hidden; }
header { background-color: rgba(0,0,0,0) !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0A1628 !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] * { color: #fff !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] p {
    color: #93C5FD !important;
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: #0F2044 !important;
    border: 1px solid #1A3A6B !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] * { color: #fff !important; }

/* Inputs */
[data-baseweb="input"] input, [data-baseweb="textarea"] textarea {
    border-radius: 8px !important;
    border: 1.5px solid #E2E8F0 !important;
    background: #fff !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-baseweb="input"] input:focus {
    border-color: #2563EB !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
}
[data-baseweb="select"] > div {
    border-radius: 8px !important;
    border: 1.5px solid #E2E8F0 !important;
    background: #fff !important;
}
.stTextInput label, .stNumberInput label,
.stSelectbox label, .stDateInput label, .stFileUploader label {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    color: #475569 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

/* Buttons */
.stButton > button {
    background: #2563EB !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    padding: 0.55rem 1.5rem !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.25) !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #1d4ed8 !important;
    box-shadow: 0 4px 16px rgba(37,99,235,0.35) !important;
    transform: translateY(-1px) !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: #fff !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important;
    padding: 1.25rem 1.5rem !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #94A3B8 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: #0A1628 !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    border: 1px solid #E2E8F0 !important;
    overflow: hidden !important;
}

/* Divider */
hr { border-top: 1px solid #E2E8F0 !important; margin: 1.5rem 0 !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #fff !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border: 1px solid #E2E8F0 !important;
    gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    color: #64748B !important;
    padding: 0.4rem 1rem !important;
}
.stTabs [aria-selected="true"] {
    background: #2563EB !important;
    color: #fff !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt(n):
    return f"₦{n:,.0f}"

def profit_color(val):
    return "#10B981" if val >= 0 else "#EF4444"

def badge(text, color):
    return f'<span style="background:{color}18;color:{color};padding:2px 10px;border-radius:20px;font-size:0.72rem;font-weight:600;">{text}</span>'

def page_header(title, subtitle=""):
    st.markdown(f"""
    <div style="margin-bottom:1.75rem;padding-bottom:1rem;border-bottom:1px solid #E2E8F0;">
        <h1 style="font-family:'Syne',sans-serif;font-size:1.7rem;font-weight:800;
                   color:#0A1628;margin:0;letter-spacing:-0.03em;">{title}</h1>
        {"" if not subtitle else f'<p style="color:#64748B;font-size:0.9rem;margin:4px 0 0;">{subtitle}</p>'}
    </div>
    """, unsafe_allow_html=True)

def card(content_fn, padding="1.5rem"):
    st.markdown(f"""<div style="background:#fff;border:1px solid #E2E8F0;border-radius:12px;
                    padding:{padding};box-shadow:0 1px 4px rgba(0,0,0,0.05);margin-bottom:1rem;">""",
                unsafe_allow_html=True)
    content_fn()
    st.markdown("</div>", unsafe_allow_html=True)

EXPENSE_CATEGORIES = ["Fuel", "Maintenance", "Repair", "Insurance", "Toll", "Wash", "Salary", "Other"]


# ── Custom Period Helper (20th-to-20th business cycle) ────────────────────────
def get_custom_period_label(d):
    """
    Returns the cycle-start label for the 20th-to-20th business cycle
    that the given date belongs to (used for expense trend chart).
    """
    if d.day >= 20:
        return d.replace(day=20).strftime("%b %d, %Y")
    else:
        first_of_month = d.replace(day=1)
        prev_month_end = first_of_month - timedelta(days=1)
        return prev_month_end.replace(day=20).strftime("%b %d, %Y")

def get_current_cycle_start():
    """Returns the start date of the current 20th-to-20th business cycle."""
    today = date.today()
    if today.day >= 20:
        return today.replace(day=20)
    else:
        first_of_month = today.replace(day=1)
        prev_month_end = first_of_month - timedelta(days=1)
        return prev_month_end.replace(day=20)

def get_cycle_start_for_income(d):
    """
    Income paid ON the 20th belongs to the cycle that is CLOSING,
    not the one opening. So the 20th is treated as the last day of
    the previous cycle for income purposes.

    Examples:
      June 20 (payment day) → belongs to Apr 20 – Jun 20 cycle → returns Apr 20 start
      June 5                → belongs to Apr 20 – Jun 19 cycle  → returns Apr 20 start
      June 21               → belongs to Jun 20 – Jul 20 cycle  → returns Jun 20 start
    """
    if d.day > 20:
        # After payment day — belongs to the cycle that started on the 20th this month
        return d.replace(day=20)
    else:
        # On or before the 20th — belongs to the previous cycle
        first_of_month = d.replace(day=1)
        prev_month_end = first_of_month - timedelta(days=1)
        return prev_month_end.replace(day=20)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:1.75rem 1rem 1.5rem;border-bottom:1px solid #0F2044;margin-bottom:1.25rem;">
        <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;
                    color:#fff;letter-spacing:-0.02em;">🚛 FleetIQ</div>
        <div style="font-size:0.72rem;color:#93C5FD;margin-top:3px;">Fleet Management System</div>
    </div>
    """, unsafe_allow_html=True)

    menu = st.selectbox("Navigation", [
        "📊  Dashboard",
        "🚗  Vehicles",
        "👤  Drivers",
        "💸  Add Expense",
        "💰  Add Income",
        "📋  Records",
        "⚡  Auto Deductions",
    ])

    # Fleet quick stats in sidebar
    vehicles = session.query(Vehicle).all()
    drivers = session.query(Driver).all()
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="padding:1rem;background:#0F2044;border-radius:10px;font-size:0.8rem;">
        <div style="color:#93C5FD;font-size:0.65rem;font-weight:600;
                    letter-spacing:0.08em;text-transform:uppercase;margin-bottom:0.75rem;">
            Fleet Status
        </div>
        <div style="display:flex;justify-content:space-between;margin-bottom:0.4rem;">
            <span style="color:#CBD5E1;">Vehicles</span>
            <span style="color:#fff;font-weight:600;">{len(vehicles)}</span>
        </div>
        <div style="display:flex;justify-content:space-between;">
            <span style="color:#CBD5E1;">Drivers</span>
            <span style="color:#fff;font-weight:600;">{len(drivers)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if menu == "📊  Dashboard":
    page_header("Dashboard", "Fleet-wide performance at a glance")

    vehicles = session.query(Vehicle).all()
    expenses = session.query(Expense).all()
    incomes = session.query(Income).all()

    if not vehicles:
        st.info("No vehicles yet. Add vehicles to see your dashboard.")
        st.stop()

    # ── Date Range Filter ─────────────────────────────────────────────────────
    with st.container():
        col_f1, col_f2, col_f3, col_f4 = st.columns([1, 1, 1, 3])
        with col_f1:
            if st.button("This Month"):
                st.session_state["date_from"] = get_current_cycle_start()
                st.session_state["date_to"] = date.today()
        with col_f2:
            if st.button("Last 3 Months"):
                st.session_state["date_from"] = date.today() - timedelta(days=90)
                st.session_state["date_to"] = date.today()
        with col_f3:
            if st.button("All Time"):
                st.session_state["date_from"] = date(2000, 1, 1)
                st.session_state["date_to"] = date.today()

        date_from = st.session_state.get("date_from", date(2000, 1, 1))
        date_to = st.session_state.get("date_to", date.today())

    # Show the active cycle range so the user always knows what period they're viewing
    st.markdown(
        f'<p style="font-size:0.78rem;color:#64748B;margin-top:0.25rem;">'
        f'📅 Viewing: <strong>{date_from.strftime("%b %d, %Y")}</strong> → '
        f'<strong>{date_to.strftime("%b %d, %Y")}</strong></p>',
        unsafe_allow_html=True
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Business Cycle Selector ───────────────────────────────────────────────
    # Build a list of all 20th-to-20th cycles that have any data
    all_dates = []
    for e in expenses:
        try:
            all_dates.append(datetime.strptime(str(e.date), "%Y-%m-%d").date())
        except:
            pass
    for i in incomes:
        try:
            all_dates.append(datetime.strptime(str(i.date), "%Y-%m-%d").date())
        except:
            pass

    if all_dates:
        # Generate all cycle start dates from earliest record to today
        def get_cycle_start_date(d):
            if d.day >= 20:
                return d.replace(day=20)
            else:
                first = d.replace(day=1)
                prev = first - timedelta(days=1)
                return prev.replace(day=20)

        earliest = min(all_dates)
        cycle_starts = []
        cursor = get_cycle_start_date(earliest)
        today_cycle = get_current_cycle_start()
        while cursor <= today_cycle:
            cycle_starts.append(cursor)
            # Advance to next cycle (add ~30 days then snap to 20th)
            next_month_first = (cursor.replace(day=1) + timedelta(days=32)).replace(day=1)
            cursor = next_month_first.replace(day=20)

        # Build labels like "May 20 – Jun 19, 2025"
        def cycle_label(start):
            # cycle end = day before next cycle start
            next_start_first = (start.replace(day=1) + timedelta(days=32)).replace(day=1)
            end = next_start_first.replace(day=20) - timedelta(days=1)
            return f"{start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}"

        cycle_labels = [cycle_label(s) for s in cycle_starts]
        cycle_map = {cycle_label(s): s for s in cycle_starts}

        st.markdown("""<p style="font-size:0.7rem;font-weight:700;color:#2563EB;
                    letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;">
                    📆 Browse by Business Cycle</p>""", unsafe_allow_html=True)

        selected_cycle_label = st.selectbox(
            "Select a business cycle to view its full summary",
            options=list(reversed(cycle_labels)),  # most recent first
            label_visibility="collapsed"
        )

        selected_cycle_start = cycle_map[selected_cycle_label]
        # Cycle end = day before next cycle's 20th
        next_cs_first = (selected_cycle_start.replace(day=1) + timedelta(days=32)).replace(day=1)
        selected_cycle_end = next_cs_first.replace(day=20) - timedelta(days=1)

        # Filter data for selected cycle
        # Expenses: standard window — 20th up to and including 19th of next month
        def in_cycle_expense(d):
            try:
                parsed = datetime.strptime(str(d), "%Y-%m-%d").date()
                return selected_cycle_start <= parsed <= selected_cycle_end
            except:
                return False

        # Income: payment ON the 20th belongs to the cycle that just CLOSED,
        # not the one that just opened — so we use get_cycle_start_for_income()
        def in_cycle_income(d):
            try:
                parsed = datetime.strptime(str(d), "%Y-%m-%d").date()
                return get_cycle_start_for_income(parsed) == selected_cycle_start
            except:
                return False

        cycle_expenses = [e for e in expenses if in_cycle_expense(e.date)]
        cycle_incomes = [i for i in incomes if in_cycle_income(i.date)]

        cycle_total_expense = sum(e.amount for e in cycle_expenses)
        cycle_total_income = sum(i.amount for i in cycle_incomes)
        cycle_profit = cycle_total_income - cycle_total_expense
        cycle_margin = (cycle_profit / cycle_total_income * 100) if cycle_total_income > 0 else 0

        st.markdown(f"""
        <div style="background:#fff;border:1px solid #E2E8F0;border-radius:12px;
                    padding:1.25rem 1.5rem;margin:0.75rem 0 1.25rem;
                    box-shadow:0 1px 4px rgba(0,0,0,0.05);">
            <p style="font-family:'Syne',sans-serif;font-weight:700;font-size:1rem;
                      color:#0A1628;margin:0 0 0.1rem;">
                📊 Cycle Summary: {selected_cycle_label}
            </p>
            <p style="font-size:0.75rem;color:#94A3B8;margin:0 0 1rem;">
                {selected_cycle_start.strftime('%B %d, %Y')} → {selected_cycle_end.strftime('%B %d, %Y')}
            </p>
        </div>
        """, unsafe_allow_html=True)

        ck1, ck2, ck3, ck4 = st.columns(4)
        ck1.metric("Cycle Income", fmt(cycle_total_income))
        ck2.metric("Cycle Expenses", fmt(cycle_total_expense))
        ck3.metric("Cycle Net Profit", fmt(cycle_profit),
                   delta=f"{cycle_margin:.1f}% margin" if cycle_total_income > 0 else None)
        ck4.metric("Transactions", f"{len(cycle_expenses) + len(cycle_incomes)}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Per-vehicle breakdown for this cycle
        cycle_vehicle_rows = []
        for v in vehicles:
            ve = [e for e in cycle_expenses if e.vehicle_id == v.id]
            vi = [i for i in cycle_incomes if i.vehicle_id == v.id]
            if ve or vi:
                t_e = sum(e.amount for e in ve)
                t_i = sum(i.amount for i in vi)
                cycle_vehicle_rows.append({
                    "Vehicle": v.name,
                    "Driver": v.driver.name if v.driver else "Unassigned",
                    "Income": fmt(t_i),
                    "Expenses": fmt(t_e),
                    "Net Profit": fmt(t_i - t_e),
                    "Status": "🟢 Profit" if (t_i - t_e) >= 0 else "🔴 Loss",
                })

        if cycle_vehicle_rows:
            cc1, cc2 = st.columns([3, 2])
            with cc1:
                st.markdown("""<p style="font-family:'Syne',sans-serif;font-weight:700;
                            font-size:0.9rem;color:#0A1628;margin-bottom:0.5rem;">
                            Per-Vehicle Breakdown</p>""", unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(cycle_vehicle_rows), use_container_width=True, hide_index=True)

            with cc2:
                # Expense by category for this cycle
                cat_totals = {}
                for e in cycle_expenses:
                    cat = e.category or "Other"
                    cat_totals[cat] = cat_totals.get(cat, 0) + e.amount
                if cat_totals:
                    st.markdown("""<p style="font-family:'Syne',sans-serif;font-weight:700;
                                font-size:0.9rem;color:#0A1628;margin-bottom:0.5rem;">
                                Expense by Category</p>""", unsafe_allow_html=True)
                    cat_df = pd.DataFrame(list(cat_totals.items()), columns=["Category", "Amount"])
                    fig_cat = px.pie(cat_df, names="Category", values="Amount",
                                     color_discrete_sequence=px.colors.sequential.Blues_r,
                                     template="plotly_white")
                    fig_cat.update_layout(paper_bgcolor="#fff", font_family="DM Sans",
                                          margin=dict(t=10, b=10, l=0, r=0))
                    st.plotly_chart(fig_cat, use_container_width=True)

            # Full expense records for this cycle
            if cycle_expenses:
                st.markdown("""<p style="font-family:'Syne',sans-serif;font-weight:700;
                            font-size:0.9rem;color:#0A1628;margin-bottom:0.5rem;">
                            All Expense Records This Cycle</p>""", unsafe_allow_html=True)
                exp_records = []
                vmap = {v.id: v.name for v in vehicles}
                for e in sorted(cycle_expenses, key=lambda x: x.date, reverse=True):
                    exp_records.append({
                        "Date": e.date,
                        "Vehicle": vmap.get(e.vehicle_id, "Unknown"),
                        "Category": e.category or "Other",
                        "Description": e.description or "—",
                        "Amount": fmt(e.amount),
                    })
                st.dataframe(pd.DataFrame(exp_records), use_container_width=True, hide_index=True)
        else:
            st.info(f"No transactions found for the cycle: {selected_cycle_label}")

    st.divider()

    # ── Build Summary Data ────────────────────────────────────────────────────
    def in_range_expense(d):
        try:
            return date_from <= datetime.strptime(str(d), "%Y-%m-%d").date() <= date_to
        except:
            return True

    def in_range_income(d):
        # Income on the 20th belongs to the cycle that just closed —
        # use get_cycle_start_for_income() so the 20th payment lands in the right cycle
        try:
            parsed = datetime.strptime(str(d), "%Y-%m-%d").date()
            cycle_start = get_cycle_start_for_income(parsed)
            return date_from <= cycle_start <= date_to
        except:
            return True

    filtered_expenses = [e for e in expenses if in_range_expense(e.date)]
    filtered_incomes = [i for i in incomes if in_range_income(i.date)]

    summary_data = []
    for v in vehicles:
        ve = [e for e in filtered_expenses if e.vehicle_id == v.id]
        vi = [i for i in filtered_incomes if i.vehicle_id == v.id]
        total_e = sum(e.amount for e in ve)
        total_i = sum(i.amount for i in vi)
        profit = total_i - total_e
        driver_name = v.driver.name if v.driver else "Unassigned"
        summary_data.append({
            "Vehicle": v.name,
            "Location": v.location or "Unknown",
            "Plate": v.plate or "—",
            "Driver": driver_name,
            "Income": total_i,
            "Expense": total_e,
            "Profit": profit,
        })

    df = pd.DataFrame(summary_data)

    total_income = df["Income"].sum()
    total_expense = df["Expense"].sum()
    total_profit = df["Profit"].sum()
    best_vehicle = df.loc[df["Profit"].idxmax(), "Vehicle"] if not df.empty else "—"

    # ── KPI Row ───────────────────────────────────────────────────────────────
    total_income = df["Income"].sum()
    total_expense = df["Expense"].sum()
    total_profit = df["Profit"].sum()

    # SAFE MARGIN CALCULATION
    margin = 0
    if total_income > 0:
        margin = (total_profit / total_income) * 100

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Fleet Income", fmt(total_income))
    k2.metric("Total Fleet Expenses", fmt(total_expense))

    k3.metric("Net Profit", fmt(total_profit),
              delta=f"{margin:.1f}% margin" if total_income > 0 else None)

    best_vehicle = df.loc[df["Profit"].idxmax(), "Vehicle"] if not df.empty and total_income > 0 else "—"
    k4.metric("Best Performing Vehicle", best_vehicle)

    # ── Vehicle Selector ──────────────────────────────────────────────────────
    st.markdown("""<p style="font-size:0.7rem;font-weight:700;color:#2563EB;
                letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;">
                🔍 Vehicle Filter</p>""", unsafe_allow_html=True)

    vehicle_names = ["All Vehicles"] + [v.name for v in vehicles]
    selected_vehicle = st.selectbox("View specific vehicle or all", vehicle_names,
                                     label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    if selected_vehicle == "All Vehicles":
        display_df = df
    else:
        display_df = df[df["Vehicle"] == selected_vehicle]

    # ── Fleet Overview Table ──────────────────────────────────────────────────
    st.markdown("""<p style="font-family:'Syne',sans-serif;font-weight:700;font-size:1rem;
                color:#0A1628;margin-bottom:0.75rem;">Fleet Overview</p>""",
                unsafe_allow_html=True)

    styled_rows = []
    for _, row in display_df.iterrows():
        profit_val = row["Profit"]
        status = "🟢 Profit" if profit_val >= 0 else "🔴 Loss"
        styled_rows.append({
            "Vehicle": row["Vehicle"],
            "Plate": row["Plate"],
            "Driver": row["Driver"],
            "Income": fmt(row["Income"]),
            "Expense": fmt(row["Expense"]),
            "Net Profit": fmt(profit_val),
            "Status": status,
        })

    st.dataframe(pd.DataFrame(styled_rows), use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ────────────────────────────────────────────────────────────────
    if not display_df.empty:
        ch1, ch2 = st.columns(2)

        with ch1:
            st.markdown("""<p style="font-family:'Syne',sans-serif;font-weight:700;
                        font-size:0.95rem;color:#0A1628;margin-bottom:0.5rem;">
                        Income vs Expense</p>""", unsafe_allow_html=True)
            melted = display_df.melt(id_vars="Vehicle",
                                     value_vars=["Income", "Expense"],
                                     var_name="Type", value_name="Amount")
            fig1 = px.bar(
                melted, x="Vehicle", y="Amount", color="Type", barmode="group",
                color_discrete_map={"Income": "#2563EB", "Expense": "#F59E0B"},
                template="plotly_white"
            )
            fig1.update_layout(
                plot_bgcolor="#fff", paper_bgcolor="#fff",
                font_family="DM Sans", margin=dict(t=10, b=10, l=0, r=0),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis_tickangle=-30
            )
            st.plotly_chart(fig1, use_container_width=True)

        with ch2:
            st.markdown("""<p style="font-family:'Syne',sans-serif;font-weight:700;
                        font-size:0.95rem;color:#0A1628;margin-bottom:0.5rem;">
                        Profit per Vehicle</p>""", unsafe_allow_html=True)
            fig2 = px.bar(
                display_df, x="Vehicle", y="Profit",
                color="Profit",
                color_continuous_scale=["#EF4444", "#F59E0B", "#10B981"],
                template="plotly_white"
            )
            fig2.update_layout(
                plot_bgcolor="#fff", paper_bgcolor="#fff",
                font_family="DM Sans", margin=dict(t=10, b=10, l=0, r=0),
                coloraxis_showscale=False, xaxis_tickangle=-30
            )
            st.plotly_chart(fig2, use_container_width=True)

        st.divider()
        st.markdown("""<p style="font-family:'Syne',sans-serif;font-weight:700;
                    font-size:0.95rem;color:#0A1628;margin-bottom:0.5rem;">
                    📍 Performance by Location</p>""", unsafe_allow_html=True)

        loc_df = display_df.groupby("Location")[["Income", "Expense"]].sum().reset_index()

        fig_loc = px.bar(
            loc_df, x="Location", y=["Income", "Expense"],
            barmode="group",
            color_discrete_map={"Income": "#2563EB", "Expense": "#F59E0B"},
            template="plotly_white"
        )
        fig_loc.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=10, b=10, l=0, r=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_loc, use_container_width=True)

    # ── Expense Category Breakdown ────────────────────────────────────────────
    expense_data = []
    for e in filtered_expenses:
        v = next((x for x in vehicles if x.id == e.vehicle_id), None)
        if v and (selected_vehicle == "All Vehicles" or v.name == selected_vehicle):
            expense_data.append({
                "Vehicle": v.name,
                "Category": e.category or "Other",
                "Amount": e.amount,
                "Date": e.date,
                "Description": e.description
            })

    df_exp = pd.DataFrame(expense_data)

    if not df_exp.empty:
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("""<p style="font-family:'Syne',sans-serif;font-weight:700;
                        font-size:0.95rem;color:#0A1628;margin-bottom:0.5rem;">
                        Expense by Category</p>""", unsafe_allow_html=True)
            cat_df = df_exp.groupby("Category")["Amount"].sum().reset_index()
            fig3 = px.pie(cat_df, names="Category", values="Amount",
                          color_discrete_sequence=px.colors.sequential.Blues_r,
                          template="plotly_white")
            fig3.update_layout(
                paper_bgcolor="#fff", font_family="DM Sans",
                margin=dict(t=10, b=10, l=0, r=0)
            )
            st.plotly_chart(fig3, use_container_width=True)

        with c2:
            st.markdown("""<p style="font-family:'Syne',sans-serif;font-weight:700;
                        font-size:0.95rem;color:#0A1628;margin-bottom:0.5rem;">
                        Expense Trend by Business Cycle</p>""", unsafe_allow_html=True)

            # ── UPDATED: Group by 20th-to-20th business cycle ────────────────
            df_exp["Date"] = pd.to_datetime(df_exp["Date"], errors="coerce")
            df_exp["Period"] = df_exp["Date"].apply(
                lambda d: get_custom_period_label(d.date()) if pd.notna(d) else None
            )
            monthly = df_exp.groupby("Period")["Amount"].sum().reset_index()
            monthly.columns = ["Month", "Amount"]
            # Sort chronologically by parsing the label back to a date
            monthly["_sort"] = pd.to_datetime(monthly["Month"], format="%b %d, %Y")
            monthly = monthly.sort_values("_sort").drop(columns=["_sort"])

            fig4 = px.line(monthly, x="Month", y="Amount",
                           markers=True, template="plotly_white",
                           color_discrete_sequence=["#2563EB"])
            fig4.update_traces(line_width=2.5, marker_size=7)
            fig4.update_layout(
                plot_bgcolor="#fff", paper_bgcolor="#fff",
                font_family="DM Sans", margin=dict(t=10, b=10, l=0, r=0),
                xaxis_title="Cycle Start (20th)",
                xaxis_tickangle=-30
            )
            st.plotly_chart(fig4, use_container_width=True)

    # ── Export ────────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("""<p style="font-family:'Syne',sans-serif;font-weight:700;
                font-size:0.95rem;color:#0A1628;margin-bottom:0.75rem;">
                Export Report</p>""", unsafe_allow_html=True)

    if st.button("⬇️  Generate Excel Report"):
        output = io.BytesIO()
        all_exp_rows = [{
            "Vehicle": next((v.name for v in vehicles if v.id == e.vehicle_id), "Unknown"),
            "Category": e.category or "General",
            "Amount": e.amount,
            "Description": e.description,
            "Date": e.date
        } for e in filtered_expenses]

        all_inc_rows = [{
            "Vehicle": next((v.name for v in vehicles if v.id == i.vehicle_id), "Unknown"),
            "Amount": i.amount,
            "Date": i.date
        } for i in filtered_incomes]

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df[["Vehicle", "Plate", "Driver", "Income", "Expense", "Profit"]].to_excel(
                writer, sheet_name="Summary", index=False)
            pd.DataFrame(all_exp_rows).to_excel(writer, sheet_name="Expenses", index=False)
            pd.DataFrame(all_inc_rows).to_excel(writer, sheet_name="Income", index=False)

        st.download_button(
            label="📥  Download Excel",
            data=output.getvalue(),
            file_name=f"fleet_report_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )



# ══════════════════════════════════════════════════════════════════════════════
# PAGE: VEHICLES
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "🚗  Vehicles":
    page_header("Vehicles", "Manage fleet, assignments, and locations")

    tab1, tab2, tab3 = st.tabs(["➕  Add Vehicle", "📋  All Vehicles", "✏️  Update/Reassign"])

    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("add_vehicle_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                v_name = st.text_input("Vehicle Name", placeholder="e.g. Toyota Hiace")
                v_plate = st.text_input("Plate Number", placeholder="e.g. LAG-234-XY")
            with col2:
                v_location = st.text_input("Operational Location", placeholder="e.g. Lagos, Abuja")
                drivers = session.query(Driver).all()
                driver_options = {"None": None, **{d.name: d.id for d in drivers}}
                selected_driver = st.selectbox("Assign Driver (optional)", list(driver_options.keys()))

            submitted = st.form_submit_button("Add Vehicle")
            if submitted:
                if v_name.strip():
                    vehicle = Vehicle(
                        name=v_name.strip(),
                        plate=v_plate.strip(),
                        location=v_location.strip(),
                        driver_id=driver_options[selected_driver]
                    )
                    session.add(vehicle)
                    session.commit()
                    st.toast(f"✅ {v_name} added to {v_location}!", icon='🚗')
                    import time; time.sleep(1); st.rerun()
                else:
                    st.warning("Please enter a vehicle name.")

    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        vehicles = session.query(Vehicle).all()
        if not vehicles:
            st.info("No vehicles added yet.")
        else:
            rows = []
            for v in vehicles:
                rows.append({
                    "ID": v.id,
                    "Vehicle": v.name,
                    "Plate": v.plate or "—",
                    "Location": v.location or "Unknown",
                    "Current Driver": v.driver.name if v.driver else "Unassigned",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("🗑️ Delete a Vehicle")
            v_names_map = {f"{v.name} ({v.plate})": v.id for v in vehicles}
            v_to_del = st.selectbox("Select vehicle to PERMANENTLY remove", list(v_names_map.keys()))
            if st.button("Delete Vehicle", type="primary"):
                target = session.query(Vehicle).get(v_names_map[v_to_del])
                session.query(Expense).filter_by(vehicle_id=target.id).delete()
                session.query(Income).filter_by(vehicle_id=target.id).delete()
                session.delete(target)
                session.commit()
                st.toast("Vehicle and data removed.")
                st.rerun()

    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        vehicles = session.query(Vehicle).all()
        drivers = session.query(Driver).all()

        if not vehicles:
            st.info("No vehicles to update.")
        else:
            v_select_map = {f"{v.name} ({v.plate or 'No plate'})": v.id for v in vehicles}
            selected_v_label = st.selectbox("Choose a Vehicle to Edit", list(v_select_map.keys()))
            target_vehicle = session.query(Vehicle).get(v_select_map[selected_v_label])

            st.divider()
            st.write(f"### Editing: {target_vehicle.name}")

            with st.form("update_vehicle_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    new_name = st.text_input("Edit Name", value=target_vehicle.name)
                    new_plate = st.text_input("Edit Plate", value=target_vehicle.plate or "")
                with col_b:
                    new_location = st.text_input("Edit Location", value=target_vehicle.location or "")
                    driver_opts = {"Unassigned (None)": None, **{d.name: d.id for d in drivers}}
                    current_driver_name = target_vehicle.driver.name if target_vehicle.driver else "Unassigned (None)"
                    default_idx = list(driver_opts.keys()).index(current_driver_name) if current_driver_name in driver_opts else 0
                    new_driver = st.selectbox("Reassign Driver", list(driver_opts.keys()), index=default_idx)

                if st.form_submit_button("💾  Save Changes"):
                    target_vehicle.name = new_name.strip()
                    target_vehicle.plate = new_plate.strip()
                    target_vehicle.location = new_location.strip()
                    target_vehicle.driver_id = driver_opts[new_driver]
                    session.commit()
                    st.toast("✅ Vehicle updated successfully!", icon="📝")
                    import time; time.sleep(1); st.rerun()



# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DRIVERS
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "👤  Drivers":
    page_header("Drivers", "Manage driver profiles and information")

    tab1, tab2, tab3 = st.tabs(["➕  Add Driver", "📋  All Drivers", "✏️  Update Profile"])

    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("add_driver_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                d_name = st.text_input("Full Name", placeholder="e.g. Emeka Okafor")
                d_phone = st.text_input("Phone Number", placeholder="e.g. 08012345678")
            with col2:
                d_license = st.text_input("License Number", placeholder="e.g. LAG20241234")

            submitted = st.form_submit_button("Add Driver")
            if submitted:
                if d_name.strip():
                    driver = Driver(
                        name=d_name.strip(),
                        phone=d_phone.strip(),
                        license_number=d_license.strip()
                    )
                    session.add(driver)
                    session.commit()
                    st.toast(f"✅ Driver {d_name} registered!", icon='👤')
                    import time; time.sleep(1); st.rerun()
                else:
                    st.warning("Please enter the driver's name.")

    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        drivers = session.query(Driver).all()
        if not drivers:
            st.info("No drivers added yet.")
        else:
            rows = []
            for d in drivers:
                assigned = [v.name for v in d.vehicles]
                rows.append({
                    "ID": d.id,
                    "Name": d.name,
                    "Phone": d.phone or "—",
                    "License": d.license_number or "—",
                    "Assigned Vehicle(s)": ", ".join(assigned) if assigned else "Unassigned",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("🗑️ Remove a Driver")
            d_names_map = {d.name: d.id for d in drivers}
            d_to_del_name = st.selectbox("Select driver to remove", list(d_names_map.keys()), key="del_d_select")

            if st.button("Delete Driver Profile", type="primary"):
                target_d = session.query(Driver).get(d_names_map[d_to_del_name])
                for v in target_d.vehicles:
                    v.driver_id = None
                session.delete(target_d)
                session.commit()
                st.toast(f"Driver '{d_to_del_name}' removed.")
                st.rerun()

    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        drivers = session.query(Driver).all()

        if not drivers:
            st.info("No drivers to update.")
        else:
            d_select_map = {d.name: d.id for d in drivers}
            selected_d_name = st.selectbox("Choose a Driver to Edit", list(d_select_map.keys()))
            target_driver = session.query(Driver).get(d_select_map[selected_d_name])

            st.divider()
            st.write(f"### Editing Profile: {target_driver.name}")

            with st.form("update_driver_form"):
                col_x, col_y = st.columns(2)
                with col_x:
                    new_d_name = st.text_input("Edit Name", value=target_driver.name)
                    new_d_phone = st.text_input("Edit Phone", value=target_driver.phone or "")
                with col_y:
                    new_d_license = st.text_input("Edit License", value=target_driver.license_number or "")

                if st.form_submit_button("💾  Update Profile"):
                    if new_d_name.strip():
                        target_driver.name = new_d_name.strip()
                        target_driver.phone = new_d_phone.strip()
                        target_driver.license_number = new_d_license.strip()
                        session.commit()
                        st.toast(f"✅ Profile for {new_d_name} updated!", icon="👤")
                        import time; time.sleep(1); st.rerun()
                    else:
                        st.error("Name cannot be empty.")



# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ADD EXPENSE
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "💸  Add Expense":
    page_header("Add Expense", "Record a new expense for a vehicle")

    vehicles = session.query(Vehicle).all()
    vehicle_dict = {f"{v.name} ({v.plate or 'No plate'})": v.id for v in vehicles}

    if not vehicle_dict:
        st.warning("Add a vehicle first before recording expenses.")
    else:
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                vehicle_name = st.selectbox("Vehicle", list(vehicle_dict.keys()))
                amount = st.number_input("Amount (₦)", min_value=0.0, step=500.0, format="%.2f")
                category = st.selectbox("Category", EXPENSE_CATEGORIES)
            with col2:
                description = st.text_input("Description", placeholder="Brief note")
                expense_date = st.date_input("Date", value=date.today())
                receipts = st.file_uploader(
                    "Upload Receipts (Max 2 files)",
                    type=["png", "jpg", "jpeg", "pdf"],
                    accept_multiple_files=True
                )

            submitted = st.form_submit_button("💾  Save Expense")

            if submitted:
                if amount <= 0:
                    st.error("Please enter an amount.")
                elif receipts and len(receipts) > 2:
                    st.error("❌ You can only upload a maximum of 2 files.")
                else:
                    image_urls = []

                    if receipts:
                        with st.spinner(f"Uploading {len(receipts)} file(s) to cloud..."):
                            for r in receipts:
                                upload_result = cloudinary.uploader.upload(r)
                                image_urls.append(upload_result["secure_url"])

                    final_receipt_path = ",".join(image_urls)

                    new_expense = Expense(
                        vehicle_id=vehicle_dict[vehicle_name],
                        amount=amount,
                        description=description,
                        category=category,
                        date=str(expense_date),
                        receipt_path=final_receipt_path
                    )

                    session.add(new_expense)
                    session.commit()
                    st.toast(f"✅ Expense of {fmt(amount)} saved!", icon="💸")
                    st.balloons()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ADD INCOME
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "💰  Add Income":
    page_header("Add Income", "Record income earned by a vehicle")

    vehicles = session.query(Vehicle).all()
    vehicle_dict = {f"{v.name} ({v.plate or 'No plate'})": v.id for v in vehicles}

    if not vehicle_dict:
        st.warning("Add a vehicle first before recording income.")
    else:
        st.markdown("<br>", unsafe_allow_html=True)

        with st.form("income_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                vehicle_name = st.selectbox("Vehicle", list(vehicle_dict.keys()))
                amount = st.number_input("Income Amount (₦)", min_value=0.0, step=500.0, format="%.2f")
            with col2:
                income_date = st.date_input("Date", value=date.today())

            submitted = st.form_submit_button("💾  Save Income")

            if submitted:
                if amount <= 0:
                    st.error("Please enter an amount.")
                else:
                    income = Income(
                        vehicle_id=vehicle_dict[vehicle_name],
                        amount=amount,
                        date=str(income_date)
                    )
                    session.add(income)
                    session.commit()
                    st.toast(f"✅ Income of {fmt(amount)} recorded!", icon="💰")
                    st.balloons()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: RECORDS
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "📋  Records":
    page_header("Records", "Browse, Edit, or Delete Transactions")

    vehicles = session.query(Vehicle).all()
    vehicle_map = {v.id: v.name for v in vehicles}

    tab1, tab2 = st.tabs(["💸  Expenses", "💰  Income"])

    with tab1:
        expenses = session.query(Expense).all()
        if not expenses:
            st.info("No expenses recorded yet.")
        else:
            exp_data = []
            for e in expenses:
                urls = e.receipt_path.split(",") if e.receipt_path else []
                exp_data.append({
                    "ID": e.id,
                    "Vehicle": vehicle_map.get(e.vehicle_id, "Unknown"),
                    "Category": e.category or "Other",
                    "Amount": float(e.amount),
                    "Date": e.date,
                    "Description": e.description or "",
                    "Receipt 1": urls[0] if len(urls) > 0 else "",
                    "Receipt 2": urls[1] if len(urls) > 1 else ""
                })

            df_exp = pd.DataFrame(exp_data)

            st.write("### Expense List")

            edited_exp_df = st.data_editor(
                df_exp,
                key="exp_edit_table",
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Receipt 1": st.column_config.LinkColumn(
                        "Receipt 1",
                        display_text="View 📄"
                    ),
                    "Receipt 2": st.column_config.LinkColumn(
                        "Receipt 2",
                        display_text="View 📄"
                    ),
                    "ID": st.column_config.NumberColumn(width="small"),
                    "Amount": st.column_config.NumberColumn(format="₦%.2f")
                }
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Expense Changes"):
                    for _, row in edited_exp_df.iterrows():
                        record = session.query(Expense).get(row["ID"])
                        if record:
                            record.amount = row["Amount"]
                            record.category = row["Category"]
                            record.date = str(row["Date"])
                            record.description = row["Description"]
                    session.commit()
                    st.toast("Expenses Updated!", icon="✅")
                    st.rerun()

            with col2:
                st.write("---")
                exp_to_del = st.selectbox("Select ID to Delete", df_exp["ID"].tolist(), key="del_exp_sel")
                if st.button("🗑️ Delete Expense", type="primary"):
                    target = session.query(Expense).get(exp_to_del)
                    session.delete(target)
                    session.commit()
                    st.toast("Expense Deleted.")
                    st.rerun()

    with tab2:
        incomes = session.query(Income).all()
        if not incomes:
            st.info("No income records found.")
        else:
            inc_data = []
            for i in incomes:
                inc_data.append({
                    "ID": i.id,
                    "Vehicle": vehicle_map.get(i.vehicle_id, "Unknown"),
                    "Amount": float(i.amount),
                    "Date": i.date
                })

            df_inc = pd.DataFrame(inc_data)

            st.write("### Income List")
            st.caption("Double-click any cell to edit details.")

            edited_inc_df = st.data_editor(df_inc, key="inc_edit_table", hide_index=True, use_container_width=True)

            col1_i, col2_i = st.columns(2)
            with col1_i:
                if st.button("💾 Save Income Changes"):
                    for _, row in edited_inc_df.iterrows():
                        record = session.query(Income).get(row["ID"])
                        if record:
                            record.amount = row["Amount"]
                            record.date = str(row["Date"])
                    session.commit()
                    st.toast("Income Updated!", icon="✅")
                    st.rerun()

            with col2_i:
                st.write("---")
                inc_to_del = st.selectbox("Select ID to Delete", df_inc["ID"].tolist(), key="del_inc_sel")
                if st.button("🗑️ Delete Income", type="primary"):
                    target = session.query(Income).get(inc_to_del)
                    session.delete(target)
                    session.commit()
                    st.toast("Income Record Deleted.")
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE: AUTO DEDUCTIONS
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "⚡  Auto Deductions":
    page_header("Auto Deductions", "Automatically calculate and record Tithe, Manager & Analyst salaries")

    # ── Constants ─────────────────────────────────────────────────────────────
    EXEMPT_VEHICLE_ID = 3          # 4RA — church vehicle, always excluded
    TITHE_RATE        = 0.10       # 10%
    MANAGER_RATE      = 0.15       # 15%
    ANALYST_RATE      = 0.02       # 2%

    vehicles  = session.query(Vehicle).all()
    expenses  = session.query(Expense).all()
    incomes   = session.query(Income).all()

    # ── Build cycle list from all income + expense dates ──────────────────────
    all_dates = []
    for e in expenses:
        try:
            all_dates.append(datetime.strptime(str(e.date), "%Y-%m-%d").date())
        except:
            pass
    for i in incomes:
        try:
            all_dates.append(datetime.strptime(str(i.date), "%Y-%m-%d").date())
        except:
            pass

    if not all_dates:
        st.info("No income or expense records found. Add income first before running auto deductions.")
        st.stop()

    def get_cycle_start_date(d):
        if d.day >= 20:
            return d.replace(day=20)
        else:
            first = d.replace(day=1)
            prev  = first - timedelta(days=1)
            return prev.replace(day=20)

    earliest    = min(all_dates)
    cycle_starts = []
    cursor      = get_cycle_start_date(earliest)
    today_cycle = get_current_cycle_start()
    while cursor <= today_cycle:
        cycle_starts.append(cursor)
        next_month_first = (cursor.replace(day=1) + timedelta(days=32)).replace(day=1)
        cursor = next_month_first.replace(day=20)

    def cycle_label(start):
        next_start_first = (start.replace(day=1) + timedelta(days=32)).replace(day=1)
        end = next_start_first.replace(day=20) - timedelta(days=1)
        return f"{start.strftime('%b %d')} – {end.strftime('%b %d, %Y')}"

    cycle_map = {cycle_label(s): s for s in cycle_starts}

    # ── Cycle selector ────────────────────────────────────────────────────────
    st.markdown("""<p style="font-size:0.7rem;font-weight:700;color:#2563EB;
                letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem;">
                Select Business Cycle</p>""", unsafe_allow_html=True)

    selected_label = st.selectbox(
        "Choose cycle",
        options=list(reversed(list(cycle_map.keys()))),
        label_visibility="collapsed"
    )

    selected_start = cycle_map[selected_label]
    next_cs_first  = (selected_start.replace(day=1) + timedelta(days=32)).replace(day=1)
    selected_end   = next_cs_first.replace(day=20) - timedelta(days=1)
    # Income paid ON the 20th belongs to the closing cycle
    income_end     = next_cs_first.replace(day=20)  # inclusive of payment day

    st.markdown(
        f'<p style="font-size:0.78rem;color:#64748B;margin:0.25rem 0 1.25rem;">'
        f'📅 Cycle: <strong>{selected_start.strftime("%b %d, %Y")}</strong> → '
        f'<strong>{selected_end.strftime("%b %d, %Y")}</strong> '
        f'(income collected on <strong>{income_end.strftime("%b %d, %Y")}</strong>)</p>',
        unsafe_allow_html=True
    )

    # ── Calculate per-vehicle income for this cycle ───────────────────────────
    def in_cycle_income_auto(d):
        try:
            parsed = datetime.strptime(str(d), "%Y-%m-%d").date()
            # Payment on the 20th belongs to the cycle that just closed
            if parsed.day > 20:
                cycle_s = parsed.replace(day=20)
            else:
                first = parsed.replace(day=1)
                prev  = first - timedelta(days=1)
                cycle_s = prev.replace(day=20)
            return cycle_s == selected_start
        except:
            return False

    cycle_incomes = [i for i in incomes if in_cycle_income_auto(i.date)]

    # Group income by vehicle, skip exempt vehicle
    vehicle_income = {}
    for i in cycle_incomes:
        if i.vehicle_id == EXEMPT_VEHICLE_ID:
            continue
        vehicle_income[i.vehicle_id] = vehicle_income.get(i.vehicle_id, 0) + i.amount

    if not vehicle_income:
        st.warning(f"No income recorded for any vehicle in the **{selected_label}** cycle. "
                   f"Record income first before running deductions.")
        st.stop()

    # ── Preview table ─────────────────────────────────────────────────────────
    vmap = {v.id: v.name for v in vehicles}

    preview_rows = []
    total_tithe = total_manager = total_analyst = 0

    for vid, income_amt in vehicle_income.items():
        tithe   = round(income_amt * TITHE_RATE)
        manager = round(income_amt * MANAGER_RATE)
        analyst = round(income_amt * ANALYST_RATE)
        total_tithe   += tithe
        total_manager += manager
        total_analyst += analyst
        preview_rows.append({
            "Vehicle":          vmap.get(vid, f"ID {vid}"),
            "Cycle Income":     fmt(income_amt),
            "Tithe (10%)":      fmt(tithe),
            "Manager (15%)":    fmt(manager),
            "Analyst (2%)":     fmt(analyst),
            "Total Deductions": fmt(tithe + manager + analyst),
        })

    st.markdown("""<p style="font-family:'Syne',sans-serif;font-weight:700;font-size:1rem;
                color:#0A1628;margin-bottom:0.75rem;">Deduction Preview</p>""",
                unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

    # ── Totals ────────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Total Tithe",           fmt(total_tithe))
    t2.metric("Total Manager Salary",  fmt(total_manager))
    t3.metric("Total Analyst Salary",  fmt(total_analyst))
    t4.metric("Grand Total Deductions",fmt(total_tithe + total_manager + total_analyst))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Check if already posted ───────────────────────────────────────────────
    # Look for any auto-deduction expenses already in this cycle
    def in_cycle_expense_check(d):
        try:
            parsed = datetime.strptime(str(d), "%Y-%m-%d").date()
            return selected_start <= parsed <= selected_end
        except:
            return False

    existing_auto = [
        e for e in expenses
        if in_cycle_expense_check(e.date)
        and e.category in ("Other", "Salary")
        and e.description in ("Tithe", "Manager's Salary", "Data Analyst")
    ]

    if existing_auto:
        st.warning(f"⚠️ Auto deductions appear to have already been posted for **{selected_label}** "
                   f"({len(existing_auto)} entries found). Running again will create duplicates. "
                   f"Delete the existing ones from Records first if you need to repost.")
    else:
        # ── Deduction date = payment day (20th of closing month) ──────────────
        deduction_date = str(income_end)

        if st.button("⚡ Post All Deductions to Expenses", type="primary"):
            count = 0
            for vid, income_amt in vehicle_income.items():
                tithe   = round(income_amt * TITHE_RATE)
                manager = round(income_amt * MANAGER_RATE)
                analyst = round(income_amt * ANALYST_RATE)

                session.add(Expense(
                    vehicle_id=vid, amount=tithe,
                    category="Other", description="Tithe",
                    date=deduction_date, receipt_path=""
                ))
                session.add(Expense(
                    vehicle_id=vid, amount=manager,
                    category="Salary", description="Manager's Salary",
                    date=deduction_date, receipt_path=""
                ))
                session.add(Expense(
                    vehicle_id=vid, amount=analyst,
                    category="Salary", description="Data Analyst",
                    date=deduction_date, receipt_path=""
                ))
                count += 3

            session.commit()
            st.toast(f"✅ {count} deduction entries posted to expenses!", icon="⚡")
            st.balloons()
            import time; time.sleep(1); st.rerun()


# ── Cleanup ───────────────────────────────────────────────────────────────────
session.close()
