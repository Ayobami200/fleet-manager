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
                st.session_state["date_from"] = date.today().replace(day=1)
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

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Build Summary Data ────────────────────────────────────────────────────
    def in_range(d):
        try:
            return date_from <= datetime.strptime(str(d), "%Y-%m-%d").date() <= date_to
        except:
            return True

    filtered_expenses = [e for e in expenses if in_range(e.date)]
    filtered_incomes = [i for i in incomes if in_range(i.date)]

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
    
    # Added the margin safety here
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
        
        # Grouping data by location
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
                        Monthly Expense Trend</p>""", unsafe_allow_html=True)
            df_exp["Date"] = pd.to_datetime(df_exp["Date"], errors="coerce")
            monthly = df_exp.groupby(df_exp["Date"].dt.to_period("M"))["Amount"].sum()
            monthly.index = monthly.index.astype(str)
            monthly_df = monthly.reset_index()
            monthly_df.columns = ["Month", "Amount"]
            fig4 = px.line(monthly_df, x="Month", y="Amount",
                           markers=True, template="plotly_white",
                           color_discrete_sequence=["#2563EB"])
            fig4.update_traces(line_width=2.5, marker_size=7)
            fig4.update_layout(
                plot_bgcolor="#fff", paper_bgcolor="#fff",
                font_family="DM Sans", margin=dict(t=10, b=10, l=0, r=0)
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
# PAGE: VEHICLES (Updated with Location Field)
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "🚗  Vehicles":
    page_header("Vehicles", "Manage fleet, assignments, and locations")

    tab1, tab2, tab3 = st.tabs(["➕  Add Vehicle", "📋  All Vehicles", "✏️  Update/Reassign"])

    # --- TAB 1: ADD NEW VEHICLE ---
    with tab1:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("add_vehicle_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                v_name = st.text_input("Vehicle Name", placeholder="e.g. Toyota Hiace")
                v_plate = st.text_input("Plate Number", placeholder="e.g. LAG-234-XY")
            with col2:
                # ADDED: Location Input
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
                        location=v_location.strip(), # SAVE LOCATION
                        driver_id=driver_options[selected_driver]
                    )
                    session.add(vehicle)
                    session.commit()
                    st.toast(f"✅ {v_name} added to {v_location}!", icon='🚗')
                    import time; time.sleep(1); st.rerun()
                else:
                    st.warning("Please enter a vehicle name.")

    # --- TAB 2: VIEW & DELETE ---
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
                    "Location": v.location or "Unknown", # DISPLAY LOCATION
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

    # --- TAB 3: UPDATE & REASSIGN ---
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
                    # ADDED: Update Location
                    new_location = st.text_input("Edit Location", value=target_vehicle.location or "")
                    
                    driver_opts = {"Unassigned (None)": None, **{d.name: d.id for d in drivers}}
                    current_driver_name = target_vehicle.driver.name if target_vehicle.driver else "Unassigned (None)"
                    default_idx = list(driver_opts.keys()).index(current_driver_name) if current_driver_name in driver_opts else 0
                    new_driver = st.selectbox("Reassign Driver", list(driver_opts.keys()), index=default_idx)

                if st.form_submit_button("💾  Save Changes"):
                    target_vehicle.name = new_name.strip()
                    target_vehicle.plate = new_plate.strip()
                    target_vehicle.location = new_location.strip() # UPDATE LOCATION
                    target_vehicle.driver_id = driver_opts[new_driver]
                    
                    session.commit()
                    st.toast("✅ Vehicle updated successfully!", icon="📝")
                    import time; time.sleep(1); st.rerun()



# ══════════════════════════════════════════════════════════════════════════════
# PAGE: DRIVERS
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "👤  Drivers":
    page_header("Drivers", "Manage driver profiles and information")

    # We now have 3 tabs here as well
    tab1, tab2, tab3 = st.tabs(["➕  Add Driver", "📋  All Drivers", "✏️  Update Profile"])

    # --- TAB 1: ADD NEW DRIVER ---
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

    # --- TAB 2: VIEW & DELETE ---
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

            # --- Delete Section ---
            st.divider()
            st.subheader("🗑️ Remove a Driver")
            d_names_map = {d.name: d.id for d in drivers}
            d_to_del_name = st.selectbox("Select driver to remove", list(d_names_map.keys()), key="del_d_select")
            
            if st.button("Delete Driver Profile", type="primary"):
                target_d = session.query(Driver).get(d_names_map[d_to_del_name])
                # Unlink from vehicles first
                for v in target_d.vehicles:
                    v.driver_id = None
                session.delete(target_d)
                session.commit()
                st.toast(f"Driver '{d_to_del_name}' removed.")
                st.rerun()

    # --- TAB 3: UPDATE DRIVER PROFILE (The New Part!) ---
    with tab3:
        st.markdown("<br>", unsafe_allow_html=True)
        drivers = session.query(Driver).all()
        
        if not drivers:
            st.info("No drivers to update.")
        else:
            # 1. Select Driver to edit
            d_select_map = {d.name: d.id for d in drivers}
            selected_d_name = st.selectbox("Choose a Driver to Edit", list(d_select_map.keys()))
            
            target_driver = session.query(Driver).get(d_select_map[selected_d_name])
            
            st.divider()
            st.write(f"### Editing Profile: {target_driver.name}")
            
            # 2. Update Form
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
    
    # Mapping the display name to the ID
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
                
                # --- CORRECTED: MULTI-FILE UPLOADER ---
                receipts = st.file_uploader(
                    "Upload Receipts (Max 2 files)", 
                    type=["png", "jpg", "jpeg", "pdf"],
                    accept_multiple_files=True  # Enables multi-upload
                )

            submitted = st.form_submit_button("💾  Save Expense")

            if submitted:
                if amount <= 0:
                    st.error("Please enter an amount.")
                elif receipts and len(receipts) > 2:
                    # Prevents saving if more than 2 files are selected
                    st.error("❌ You can only upload a maximum of 2 files.")
                else:
                    # --- CORRECTED: CLOUDINARY LOOP LOGIC ---
                    image_urls = []
                    
                    if receipts:
                        with st.spinner(f"Uploading {len(receipts)} file(s) to cloud..."):
                            for r in receipts:
                                upload_result = cloudinary.uploader.upload(r)
                                image_urls.append(upload_result["secure_url"])
                    
                    # Joining URLs into a single string separated by a comma
                    # Example: "https://url1.com,https://url2.com"
                    final_receipt_path = ",".join(image_urls)

                    # SAVING TO DATABASE
                    new_expense = Expense(
                        vehicle_id=vehicle_dict[vehicle_name],
                        amount=amount,
                        description=description,
                        category=category,
                        date=str(expense_date),
                        receipt_path=final_receipt_path  # Saves the combined string
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
        
        # This 'with st.form' is what makes it clear after you click save
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
# PAGE: RECORDS (REPLACE EVERYTHING FROM HERE TO THE BOTTOM)
# ══════════════════════════════════════════════════════════════════════════════
elif menu == "📋  Records":
    page_header("Records", "Browse, Edit, or Delete Transactions")

    # This map helps turn vehicle IDs (1, 2, 3) into names (Toyota, Honda)
    vehicles = session.query(Vehicle).all()
    vehicle_map = {v.id: v.name for v in vehicles}

    tab1, tab2 = st.tabs(["💸  Expenses", "💰  Income"])

    # --- TAB 1: EXPENSES ---
    # --- TAB 1: EXPENSES ---
    with tab1:
        # --- TAB 1: EXPENSES ---
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
                    "Description": e.description or "", # Description is back!
                    "Receipt 1": urls[0] if len(urls) > 0 else "",
                    "Receipt 2": urls[1] if len(urls) > 1 else ""     
                })
            
            df_exp = pd.DataFrame(exp_data)
            
            st.write("### Expense List")
            
            # --- THE FIX FOR LINKS AND COLUMN WIDTH ---
            edited_exp_df = st.data_editor(
                df_exp, 
                key="exp_edit_table", 
                hide_index=True, 
                use_container_width=True,
                column_config={
                    # "display_text" hides the long URL and shows a clean button
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
                            record.description = row["Description"] # Saves any edits to description
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

    # --- TAB 2: INCOME ---
    with tab2:
        incomes = session.query(Income).all()
        if not incomes:
            st.info("No income records found.")
        else:
            # Create a list for the editor
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

            # Editable table for Income
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


# ── Cleanup ───────────────────────────────────────────────────────────────────
session.close()
