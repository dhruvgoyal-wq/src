import streamlit as st
import psycopg2
# import sys, os
# sys.path.append(os.path.dirname(__file__))

import pandas as pd
from datetime import datetime
import re
from src.insights import lead_insights_dashboard
import plotly.express as px

# ===============================
# 🔌 DATABASE CONNECTION
# ===============================
def get_connection():
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        dbname=st.secrets["postgres"]["dbname"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"]
    )

# ===============================
# 🔐 AUTHENTICATION
# ===============================
def authenticate_user(email, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT role FROM user_access WHERE email=%s AND password=%s", (email, password))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None

# ===============================
# 👥 USER MANAGEMENT
# ===============================
def add_user(email, password, role="user"):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO user_access (email, password, role) VALUES (%s, %s, %s) ON CONFLICT (email) DO NOTHING",
            (email, password, role)
        )
        conn.commit()
        st.success(f"✅ User '{email}' added successfully.")
    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

def show_user_table():
    conn = get_connection()
    df = pd.read_sql("SELECT id, email, role FROM user_access ORDER BY id", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

# ===============================
# 📋 DATA OPERATIONS
# ===============================
@st.cache_data(ttl=600)
def load_vendor_data():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM vendor_data", conn)
    conn.close()
    return df

def setup_status_column():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("ALTER TABLE vendor_data ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'New';")
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error setting up status column: {e}")
        return False

def add_new_column(column_name):
    column_name = column_name.strip().lower()
    if not column_name:
        st.warning("Please enter a column name.")
        return
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", column_name):
        st.error("❌ Invalid name. Use only letters, numbers, and underscores.")
        return
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f'ALTER TABLE vendor_data ADD COLUMN IF NOT EXISTS "{column_name}" TEXT;')
        conn.commit()
        cur.close()
        conn.close()
        st.success(f"✅ Column '{column_name}' added successfully!")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Error adding column: {e}")

def delete_column(column_name):
    column_name = column_name.strip().lower()
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", column_name):
        st.error("❌ Invalid column name.")
        return
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f'ALTER TABLE vendor_data DROP COLUMN IF EXISTS "{column_name}";')
        conn.commit()
        cur.close()
        conn.close()
        st.warning(f"🗑️ Column '{column_name}' deleted successfully.")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Error deleting column: {e}")

def save_changes_to_db(updated_df, original_df, current_user_email):
    try:
        updated_df = updated_df.reset_index(drop=True)
        original_df = original_df.reset_index(drop=True)
        changed_rows = []
        
        for i in range(len(updated_df)):
            row_old = original_df.loc[i]
            row_new = updated_df.loc[i]
            diffs = {}
            
            for col in updated_df.columns:
                old_val = str(row_old[col]) if pd.notna(row_old[col]) else ""
                new_val = str(row_new[col]) if pd.notna(row_new[col]) else ""
                if old_val != new_val:
                    diffs[col] = new_val
            
            if diffs:
                diffs["uuid"] = row_new["uuid"]
                diffs["updated_at"] = datetime.now()
                diffs["updated_by"] = current_user_email
                changed_rows.append(diffs)
        
        if not changed_rows:
            st.info("No changes detected.")
            return
        
        conn = get_connection()
        cur = conn.cursor()
        
        for row in changed_rows:
            uuid_val = row.pop("uuid")
            set_clause = ", ".join([f'"{col}" = %s' for col in row.keys()])
            query = f'UPDATE vendor_data SET {set_clause} WHERE uuid = %s'
            values = list(row.values()) + [uuid_val]
            cur.execute(query, values)
        
        conn.commit()
        cur.close()
        conn.close()
        st.success(f"✅ Saved {len(changed_rows)} changes")
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"⚠️ Error saving changes: {e}")

# ===============================
# 🎯 FILTERING SYSTEM (UNIFIED)
# ===============================
def apply_filters(df, filter_key_prefix=""):
    """Unified filtering system used by both admin and user dashboards"""
    all_columns = df.columns.tolist()
    
    if f'{filter_key_prefix}filters' not in st.session_state:
        st.session_state[f'{filter_key_prefix}filters'] = {}
    
    filter_tab1, filter_tab2, filter_tab3 = st.tabs(["🔤 Text Search", "📋 Dropdown Filters", "🎯 Quick Filters"])
    
    # Tab 1: Text Search
    with filter_tab1:
        st.caption("Search across multiple columns simultaneously")
        text_search_cols = st.multiselect(
            "Select columns to search",
            options=[c for c in all_columns if df[c].dtype == 'object'],
            key=f"{filter_key_prefix}text_cols"
        )
        
        if text_search_cols:
            search_cols_area = st.columns(min(3, len(text_search_cols)))
            for idx, col in enumerate(text_search_cols):
                with search_cols_area[idx % 3]:
                    search_val = st.text_input(
                        f"🔍 {col}",
                        key=f"{filter_key_prefix}search_{col}",
                        placeholder=f"Search..."
                    )
                    if search_val:
                        st.session_state[f'{filter_key_prefix}filters'][col] = {'type': 'text', 'value': search_val}
                    elif col in st.session_state[f'{filter_key_prefix}filters'] and st.session_state[f'{filter_key_prefix}filters'][col].get('type') == 'text':
                        del st.session_state[f'{filter_key_prefix}filters'][col]
    
    # Tab 2: Dropdown Filters
    with filter_tab2:
        st.caption("Select specific values from columns - includes blanks/NaN as filterable options")
        
        # Allow filtering on ALL columns (removed the 100 unique value limit)
        dropdown_filter_cols = st.multiselect(
            "Select columns for dropdown filtering",
            options=[c for c in all_columns if df[c].dtype == 'object'],
            key=f"{filter_key_prefix}dropdown_cols"
        )
        
        if dropdown_filter_cols:
            num_cols = min(3, len(dropdown_filter_cols))
            dropdown_cols_area = st.columns(num_cols)
            
            for idx, col in enumerate(dropdown_filter_cols):
                with dropdown_cols_area[idx % num_cols]:
                    # Get all unique values including NaN/blanks
                    unique_vals = []
                    has_blanks = False
                    
                    for val in df[col].unique():
                        if pd.isna(val) or str(val).strip() in ['', 'nan', 'None', 'NaN']:
                            has_blanks = True
                        else:
                            unique_vals.append(str(val))
                    
                    # Sort and add blank option at the top if exists
                    unique_vals = sorted(unique_vals)
                    if has_blanks:
                        unique_vals = ['[Blank/NaN]'] + unique_vals
                    
                    # Initialize selection state if not exists
                    selection_key = f"{filter_key_prefix}dropdown_selection_{col}"
                    if selection_key not in st.session_state:
                        st.session_state[selection_key] = []
                    
                    # Select All / Deselect All buttons
                    button_cols = st.columns([1, 1])
                    with button_cols[0]:
                        if st.button(f"✅ Select All", key=f"{filter_key_prefix}select_all_{col}", use_container_width=True):
                            st.session_state[selection_key] = unique_vals.copy()
                            st.rerun()
                    with button_cols[1]:
                        if st.button(f"❌ Deselect All", key=f"{filter_key_prefix}deselect_all_{col}", use_container_width=True):
                            st.session_state[selection_key] = []
                            st.rerun()
                    
                    # Multiselect with current selection
                    selected = st.multiselect(
                        f"📋 {col} ({len(unique_vals)} options)",
                        options=unique_vals,
                        default=st.session_state[selection_key],
                        key=f"{filter_key_prefix}dropdown_{col}",
                        placeholder=f"Choose {col}..."
                    )
                    
                    # Update session state
                    st.session_state[selection_key] = selected
                    
                    # Update filters
                    if selected:
                        st.session_state[f'{filter_key_prefix}filters'][col] = {'type': 'dropdown', 'value': selected}
                    elif col in st.session_state[f'{filter_key_prefix}filters'] and st.session_state[f'{filter_key_prefix}filters'][col].get('type') == 'dropdown':
                        del st.session_state[f'{filter_key_prefix}filters'][col]
    
    # Tab 3: Quick Filters
    with filter_tab3:
        st.caption("Quick access filters for common scenarios")
        quick_cols = st.columns(3)
        
        # Status Filter
        if 'status' in df.columns:
            with quick_cols[0]:
                st.markdown("##### 📊 Status Filter")
                status_values = df['status'].dropna().unique().tolist()
                selected_statuses = st.multiselect(
                    "Select Status",
                    options=sorted(status_values),
                    key=f"{filter_key_prefix}status_filter",
                    placeholder="All statuses"
                )
                
                if selected_statuses:
                    st.session_state[f'{filter_key_prefix}filters']['status'] = {'type': 'dropdown', 'value': selected_statuses}
                elif 'status' in st.session_state[f'{filter_key_prefix}filters'] and st.session_state[f'{filter_key_prefix}filters']['status'].get('type') == 'dropdown':
                    del st.session_state[f'{filter_key_prefix}filters']['status']
        
        # Assignment Filter
        with quick_cols[1]:
            st.markdown("##### 👤 Assignment Filter")
            assignment_filter = st.radio(
                "Assignment Status",
                ["All", "Assigned", "Unassigned"],
                key=f"{filter_key_prefix}assignment_status"
            )
            
            if assignment_filter == "Assigned":
                st.session_state[f'{filter_key_prefix}filters']['assigned_to'] = {'type': 'assignment', 'value': 'assigned'}
            elif assignment_filter == "Unassigned":
                st.session_state[f'{filter_key_prefix}filters']['assigned_to'] = {'type': 'assignment', 'value': 'unassigned'}
            elif 'assigned_to' in st.session_state[f'{filter_key_prefix}filters'] and st.session_state[f'{filter_key_prefix}filters']['assigned_to'].get('type') == 'assignment':
                del st.session_state[f'{filter_key_prefix}filters']['assigned_to']
        
        # Date Range Filter
        with quick_cols[2]:
            st.markdown("##### 📅 Date Range")
            date_cols = [c for c in all_columns if 'date' in c.lower() or 'created' in c.lower() or 'updated' in c.lower()]
            
            if date_cols:
                date_col = st.selectbox("Select date column", date_cols, key=f"{filter_key_prefix}date_col")
                date_range = st.date_input("Filter dates", value=(), key=f"{filter_key_prefix}date_range_{date_col}")
                
                if len(date_range) == 2:
                    st.session_state[f'{filter_key_prefix}filters'][date_col] = {'type': 'date', 'value': date_range}
                elif date_col in st.session_state[f'{filter_key_prefix}filters'] and st.session_state[f'{filter_key_prefix}filters'][date_col].get('type') == 'date':
                    del st.session_state[f'{filter_key_prefix}filters'][date_col]
    
    # Clear Filters Button
    filter_action_cols = st.columns([3, 1])
    with filter_action_cols[0]:
        if st.session_state[f'{filter_key_prefix}filters']:
            st.markdown("**🎯 Active Filters:**")
            filter_tags = []
            for col, config in st.session_state[f'{filter_key_prefix}filters'].items():
                if config['type'] == 'text':
                    filter_tags.append(f"`{col}` contains '{config['value']}'")
                elif config['type'] == 'dropdown':
                    filter_tags.append(f"`{col}` = {len(config['value'])} selected")
                elif config['type'] == 'assignment':
                    filter_tags.append(f"Status: {config['value']}")
                elif config['type'] == 'date':
                    filter_tags.append(f"`{col}` [{config['value'][0]} to {config['value'][1]}]")
            st.caption(" **|** ".join(filter_tags))
    
    with filter_action_cols[1]:
        if st.button("🧹 Clear All Filters", type="secondary", use_container_width=True, key=f"{filter_key_prefix}clear_filters"):
            st.session_state[f'{filter_key_prefix}filters'] = {}
            st.rerun()
    
    # Apply Filters
    df_filtered = df.copy()
    for col, filter_config in st.session_state[f'{filter_key_prefix}filters'].items():
        filter_type = filter_config['type']
        filter_value = filter_config['value']
        
        if filter_type == 'text':
            mask = df_filtered[col].astype(str).str.contains(filter_value, case=False, na=False)
            df_filtered = df_filtered[mask]
        elif filter_type == 'dropdown':
            mask = df_filtered[col].astype(str).isin(filter_value)
            df_filtered = df_filtered[mask]
        elif filter_type == 'date':
            try:
                df_filtered[col] = pd.to_datetime(df_filtered[col], errors='coerce')
                start_date, end_date = filter_value
                mask = (df_filtered[col].dt.date >= start_date) & (df_filtered[col].dt.date <= end_date)
                df_filtered = df_filtered[mask]
            except Exception as e:
                st.warning(f"Could not apply date filter on {col}: {e}")
        elif filter_type == 'assignment':
            if filter_value == 'assigned':
                mask = df_filtered['assigned_to'].notna() & (df_filtered['assigned_to'].astype(str).str.strip() != '')
                df_filtered = df_filtered[mask]
            elif filter_value == 'unassigned':
                mask = df_filtered['assigned_to'].isna() | (df_filtered['assigned_to'].astype(str).str.strip() == '')
                df_filtered = df_filtered[mask]
    
    return df_filtered

# ===============================
# 📦 BULK ASSIGNMENT
# ===============================
def bulk_assignment_interface():
    st.title("🎯 Bulk Lead Assignment")
    
    df = load_vendor_data().fillna("")
    
    # Check status column
    if 'status' not in df.columns:
        st.warning("⚠️ Status column not found in database.")
        if st.button("➕ Create Status Column"):
            if setup_status_column():
                st.success("✅ Status column created successfully!")
                st.cache_data.clear()
                st.rerun()
        return
    
    st.markdown("## 🔍 Step 1: Filter Leads")
    df_filtered = apply_filters(df, filter_key_prefix="bulk_")
    
    # Filter Results
    st.markdown("---")
    st.markdown("### 📊 Filter Results")
    result_cols = st.columns(4)
    result_cols[0].metric("📋 Total Records", f"{len(df):,}")
    result_cols[1].metric("✅ Filtered Records", f"{len(df_filtered):,}")
    result_cols[2].metric("🎯 Active Filters", len(st.session_state.get('bulk_filters', {})))
    if len(df) > 0:
        reduction_pct = ((len(df) - len(df_filtered)) / len(df) * 100)
        result_cols[3].metric("📉 Filtered Out", f"{reduction_pct:.1f}%")
    
    with st.expander("👁️ Preview Filtered Data", expanded=False):
        st.dataframe(df_filtered.head(100), use_container_width=True, height=300)
    
    if len(df_filtered) == 0:
        st.warning("⚠️ No leads match your filters. Please adjust filters above.")
        return
    
    st.markdown("---")
    st.markdown("## 📦 Step 2: Select Leads to Assign")
    
    select_cols = st.columns([2, 1])
    with select_cols[0]:
        leads_to_assign = st.number_input(
            "How many leads do you want to assign?",
            min_value=1,
            max_value=len(df_filtered),
            value=min(50, len(df_filtered)),
            step=10
        )
    with select_cols[1]:
        st.markdown("")
        st.markdown("")
        assignment_date = st.date_input("📅 Assignment Date", value=datetime.now().date())
    
    df_to_assign = df_filtered.head(leads_to_assign).copy()
    st.info(f"✅ Selected **{len(df_to_assign):,}** leads for assignment")
    
    st.markdown("---")
    st.markdown("## 👥 Step 3: Choose Team Members & Distribution")
    
    conn = get_connection()
    sales_users = pd.read_sql("SELECT email FROM user_access WHERE role='user'", conn)
    conn.close()
    
    if len(sales_users) == 0:
        st.error("❌ No users found. Please add users first.")
        return
    
    selected_members = st.multiselect(
        "Select team members to assign leads to",
        options=sales_users['email'].tolist()
    )
    
    if not selected_members:
        st.warning("⚠️ Please select at least one team member to continue.")
        return
    
    st.markdown("---")
    st.markdown("### 📊 Distribution Method")
    
    distribution_method = st.radio(
        "How do you want to distribute the leads?",
        ["Equal Distribution", "Custom Distribution"],
        horizontal=True
    )
    
    if 'custom_distribution' not in st.session_state:
        st.session_state.custom_distribution = {}
    
    distribution_plan = {}
    
    if distribution_method == "Equal Distribution":
        leads_per_person = leads_to_assign // len(selected_members)
        remainder = leads_to_assign % len(selected_members)
        
        for idx, member in enumerate(selected_members):
            count = leads_per_person + (1 if idx < remainder else 0)
            distribution_plan[member] = count
        
        dist_df = pd.DataFrame([
            {"Salesperson": member, "Leads Assigned": count}
            for member, count in distribution_plan.items()
        ])
        st.dataframe(dist_df, use_container_width=True, hide_index=True)
    else:
        st.markdown("#### ✏️ Custom Distribution")
        custom_cols = st.columns(min(3, len(selected_members)))
        
        for idx, member in enumerate(selected_members):
            with custom_cols[idx % 3]:
                default_val = st.session_state.custom_distribution.get(member, leads_to_assign // len(selected_members))
                count = st.number_input(
                    f"👤 {member}",
                    min_value=0,
                    max_value=leads_to_assign,
                    value=int(default_val),
                    step=1,
                    key=f"custom_{member}"
                )
                distribution_plan[member] = count
                st.session_state.custom_distribution[member] = count
        
        total_assigned = sum(distribution_plan.values())
        st.markdown("---")
        validation_cols = st.columns(3)
        validation_cols[0].metric("🎯 Leads to Assign", f"{leads_to_assign:,}")
        validation_cols[1].metric("📊 Total Allocated", f"{total_assigned:,}")
        
        difference = leads_to_assign - total_assigned
        if difference == 0:
            validation_cols[2].metric("✅ Status", "Perfect!", delta="0")
        elif difference > 0:
            validation_cols[2].metric("⚠️ Remaining", f"{difference:,}", delta=f"{difference:,}")
            st.warning(f"⚠️ You have {difference:,} leads remaining. Please allocate all leads.")
        else:
            validation_cols[2].metric("❌ Over Allocated", f"{abs(difference):,}", delta=f"{difference:,}")
            st.error(f"❌ You've allocated {abs(difference):,} more leads than available!")
    
    st.markdown("---")
    st.markdown("## ✅ Step 4: Review & Execute Assignment")
    
    total_to_assign = sum(distribution_plan.values())
    summary_cols = st.columns(4)
    summary_cols[0].metric("📋 Total Leads", f"{leads_to_assign:,}")
    summary_cols[1].metric("👥 Team Members", len(selected_members))
    summary_cols[2].metric("📊 To Be Assigned", f"{total_to_assign:,}")
    summary_cols[3].metric("📅 Assignment Date", assignment_date.strftime("%d %b %Y"))
    
    final_df = pd.DataFrame([
        {
            "Salesperson": member,
            "Leads to Assign": count,
            "Assignment Date": assignment_date.strftime("%Y-%m-%d"),
            "Percentage": f"{(count/total_to_assign*100):.1f}%" if total_to_assign > 0 else "0%"
        }
        for member, count in distribution_plan.items() if count > 0
    ])
    
    if not final_df.empty:
        st.dataframe(final_df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    can_execute = (total_to_assign == leads_to_assign and total_to_assign > 0)
    
    execute_cols = st.columns([2, 1])
    with execute_cols[0]:
        if can_execute:
            st.success(f"✅ Ready to assign {total_to_assign:,} leads")
        else:
            if total_to_assign == 0:
                st.warning("⚠️ No leads allocated.")
            elif total_to_assign != leads_to_assign:
                st.error(f"❌ Mismatch: Need {leads_to_assign:,} but allocated {total_to_assign:,}")
    
    with execute_cols[1]:
        st.markdown("")
        if st.button("🚀 Execute Assignment", type="primary", use_container_width=True, disabled=not can_execute):
            execute_assignment(df_to_assign, distribution_plan, assignment_date)

def execute_assignment(df_to_assign, distribution_plan, assignment_date):
    try:
        conn = get_connection()
        cur = conn.cursor()
        assignments_made = []
        current_idx = 0
        
        for member, count in distribution_plan.items():
            if count == 0:
                continue
            
            leads_subset = df_to_assign.iloc[current_idx:current_idx + count]
            uuids_to_assign = leads_subset['uuid'].tolist()
            
            if len(uuids_to_assign) > 0:
                cur.execute(
                    """
                    UPDATE vendor_data
                    SET assigned_to = %s, assigned_on = %s, updated_at = NOW(), updated_by = %s
                    WHERE uuid = ANY(%s)
                    """,
                    (member, assignment_date, st.session_state.email, uuids_to_assign)
                )
                
                assignments_made.append({
                    'salesperson': member,
                    'leads_assigned': len(uuids_to_assign),
                    'assignment_date': assignment_date.strftime("%Y-%m-%d")
                })
                current_idx += count
        
        conn.commit()
        cur.close()
        conn.close()
        
        st.success(f"🎉 **Assignment Completed Successfully!**")
        st.balloons()
        st.markdown("### 📊 Assignment Summary")
        st.dataframe(pd.DataFrame(assignments_made), use_container_width=True, hide_index=True)
        
        st.cache_data.clear()
        if 'custom_distribution' in st.session_state:
            del st.session_state.custom_distribution
        
        import time
        time.sleep(2)
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error during assignment: {e}")

def show_assignment_history():
    st.markdown("## 📜 Assignment History & Analytics")
    
    conn = get_connection()
    df_history = pd.read_sql(
        """
        SELECT assigned_to, DATE(assigned_on) as assignment_date, COUNT(*) as leads_assigned,
               MIN(assigned_on) as first_assignment_time, MAX(assigned_on) as last_assignment_time, updated_by as assigned_by
        FROM vendor_data 
        WHERE assigned_to IS NOT NULL AND assigned_to != ''
        GROUP BY assigned_to, DATE(assigned_on), updated_by
        ORDER BY assignment_date DESC, assigned_to
        """, conn
    )
    conn.close()
    
    if len(df_history) == 0:
        st.info("📭 No assignment history available yet.")
        return
    
    metric_cols = st.columns(5)
    metric_cols[0].metric("📅 Total Days", df_history['assignment_date'].nunique())
    metric_cols[1].metric("👥 Salespeople", df_history['assigned_to'].nunique())
    metric_cols[2].metric("📊 Total Assignments", len(df_history))
    metric_cols[3].metric("🎯 Total Leads", f"{df_history['leads_assigned'].sum():,}")
    metric_cols[4].metric("📈 Avg/Day", f"{df_history['leads_assigned'].mean():.0f}")
    
    st.markdown("---")
    
    filter_cols = st.columns(3)
    with filter_cols[0]:
        date_filter = st.date_input("📅 Filter by Date Range", value=(), key="history_date_filter")
    with filter_cols[1]:
        user_filter = st.multiselect("👤 Filter by Salesperson", options=df_history['assigned_to'].unique().tolist(), key="history_user_filter")
    with filter_cols[2]:
        sort_by = st.selectbox("📊 Sort by", ["Date (Recent First)", "Date (Oldest First)", "Leads (High-Low)", "Leads (Low-High)"], key="history_sort")
    
    df_filtered = df_history.copy()
    if len(date_filter) == 2:
        df_filtered = df_filtered[(df_filtered['assignment_date'] >= date_filter[0]) & (df_filtered['assignment_date'] <= date_filter[1])]
    if user_filter:
        df_filtered = df_filtered[df_filtered['assigned_to'].isin(user_filter)]
    
    if sort_by == "Date (Recent First)":
        df_filtered = df_filtered.sort_values('assignment_date', ascending=False)
    elif sort_by == "Date (Oldest First)":
        df_filtered = df_filtered.sort_values('assignment_date', ascending=True)
    elif sort_by == "Leads (High-Low)":
        df_filtered = df_filtered.sort_values('leads_assigned', ascending=False)
    else:
        df_filtered = df_filtered.sort_values('leads_assigned', ascending=True)
    
    st.markdown(f"### 📋 Assignment Records ({len(df_filtered)})")
    st.dataframe(df_filtered, use_container_width=True, height=400, hide_index=True)
    
    if len(df_filtered) > 0:
        st.markdown("---")
        viz_tab1, viz_tab2, viz_tab3 = st.tabs(["📈 Daily Trend", "👥 By Salesperson", "📊 Distribution"])
        
        with viz_tab1:
            daily_summary = df_filtered.groupby('assignment_date')['leads_assigned'].sum().reset_index()
            fig1 = px.line(daily_summary, x='assignment_date', y='leads_assigned', title="Daily Lead Assignments", markers=True)
            fig1.update_traces(line_color='#1f77b4', line_width=3, marker=dict(size=10))
            st.plotly_chart(fig1, use_container_width=True)
        
        with viz_tab2:
            user_summary = df_filtered.groupby('assigned_to')['leads_assigned'].sum().reset_index().sort_values('leads_assigned', ascending=True)
            fig2 = px.bar(user_summary, x='leads_assigned', y='assigned_to', title="Total Leads by Salesperson", 
                         text='leads_assigned', orientation='h', color='leads_assigned', color_continuous_scale='Blues')
            fig2.update_traces(textposition='outside')
            st.plotly_chart(fig2, use_container_width=True)
        
        with viz_tab3:
            fig3 = px.pie(user_summary, values='leads_assigned', names='assigned_to', title="Lead Distribution")
            st.plotly_chart(fig3, use_container_width=True)
    
    st.markdown("---")
    st.download_button(
        "📥 Download Assignment History",
        data=df_filtered.to_csv(index=False).encode("utf-8"),
        file_name=f"assignment_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )

# ===============================
# 👤 USER DASHBOARD
# ===============================
def user_dashboard():
    st.title("👤 User Dashboard")
    st.write(f"Welcome, **{st.session_state.email}**!")
    
    st.sidebar.header("User Navigation")
    page = st.sidebar.radio("Choose Section", ["My Leads", "Lead Insights"])
    
    if page == "Lead Insights":
        lead_insights_dashboard(assigned_to=st.session_state.email)
        return
    
    # My Leads Section
    conn = get_connection()
    df_user = pd.read_sql("SELECT * FROM vendor_data WHERE assigned_to = %s", conn, params=[st.session_state.email])
    conn.close()
    
    st.info(f"📦 You have **{len(df_user)}** records assigned to you.")
    
    if len(df_user) == 0:
        st.warning("No records assigned yet.")
        return
    
    st.markdown("### ✏️ Edit Your Assigned Leads")
    
    # Status dropdown configuration
    STATUS_OPTIONS = ["New", "Interested", "In Talk", "Follow Up", "Converted", "Closed", "Not Interested", "Unreachable"]
    
    if 'status' in df_user.columns:
        column_config = {
            "status": st.column_config.SelectboxColumn(
                "Status",
                help="Lead status",
                width="medium",
                options=STATUS_OPTIONS,
                required=False,
            )
        }
        edited_df = st.data_editor(df_user, use_container_width=True, height=600, key="user_editable_table", column_config=column_config)
    else:
        edited_df = st.data_editor(df_user, use_container_width=True, height=600, key="user_editable_table")
    
    if st.button("💾 Save Changes", key="user_save"):
        save_changes_to_db(edited_df, df_user, st.session_state.email)
    
    st.download_button(
        "⬇️ Download My Assigned Data",
        data=df_user.to_csv(index=False).encode("utf-8"),
        file_name=f"my_assigned_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# ===============================
# 📋 STANDARD ASSIGNMENT (Admin)
# ===============================
def standard_assignment():
    st.title("📋 Standard Lead Assignment")
    
    df = load_vendor_data().fillna("")
    all_columns = df.columns.tolist()
    
    # Status column check
    if 'status' not in all_columns:
        st.warning("⚠️ Status column not found in database.")
        if st.button("➕ Create Status Column", key="std_create_status"):
            if setup_status_column():
                st.success("✅ Status column created successfully!")
                st.cache_data.clear()
                st.rerun()
    
    st.markdown("### ➕ Manage Columns")
    col_input_area = st.columns([3, 1, 1])
    
    with col_input_area[0]:
        new_col_name = st.text_input("Enter new column name", placeholder="e.g. remarks, follow_up_date")
    with col_input_area[1]:
        if st.button("➕ Add Column"):
            add_new_column(new_col_name)
    with col_input_area[2]:
        if st.button("🗑️ Delete Column"):
            delete_column(new_col_name)
    
    st.divider()
    
    st.markdown("### ✏️ Edit All Vendor Data")
    STATUS_OPTIONS = ["New", "Interested", "In Talk", "Follow Up", "Converted", "Closed", "Not Interested", "Unreachable"]
    
    if 'status' in df.columns:
        column_config = {
            "status": st.column_config.SelectboxColumn("Status", help="Lead status", width="medium", options=STATUS_OPTIONS, required=False)
        }
        edited_df = st.data_editor(df, use_container_width=True, height=600, key="admin_editable_table", column_config=column_config)
    else:
        edited_df = st.data_editor(df, use_container_width=True, height=600, key="admin_editable_table")
    
    if st.button("💾 Save Changes", key="admin_save"):
        save_changes_to_db(edited_df, df, st.session_state.email)
    
    st.divider()
    st.markdown("### 🎯 Filter & Assign Leads")
    
    df_filtered = apply_filters(df, filter_key_prefix="std_")
    
    # Display results
    reduction_pct = ((len(df) - len(df_filtered)) / len(df) * 100) if len(df) > 0 else 0
    result_metric_cols = st.columns(4)
    result_metric_cols[0].metric("📊 Total Records", f"{len(df):,}")
    result_metric_cols[1].metric("✅ Filtered Records", f"{len(df_filtered):,}")
    result_metric_cols[2].metric("🎯 Active Filters", len(st.session_state.get('std_filters', {})))
    result_metric_cols[3].metric("📉 Filtered Out", f"{reduction_pct:.1f}%")
    
    st.markdown("---")
    st.markdown("### 📋 Filtered Records")
    
    if len(df_filtered) > 0:
        # Pagination
        page_size = st.selectbox("Rows per page", [25, 50, 100, 250], index=1, key="std_page_size")
        total_pages = (len(df_filtered) - 1) // page_size + 1
        
        page_nav_cols = st.columns([1, 3, 1])
        with page_nav_cols[1]:
            current_page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, key="std_current_page")
        
        start_idx = (current_page - 1) * page_size
        end_idx = start_idx + page_size
        
        st.caption(f"Showing records {start_idx + 1} to {min(end_idx, len(df_filtered))} of {len(df_filtered):,}")
        st.dataframe(df_filtered.iloc[start_idx:end_idx], use_container_width=True, height=500)
        
        # Assign section
        st.markdown("---")
        st.markdown("### ✅ Assign Filtered Records")
        
        conn = get_connection()
        sales_users = pd.read_sql("SELECT email FROM user_access WHERE role='user'", conn)
        conn.close()
        
        assign_cols = st.columns([2, 1])
        with assign_cols[0]:
            salesperson = st.selectbox("Assign To", sales_users['email'].tolist(), index=None, placeholder="Select salesperson", key="std_salesperson_select")
        with assign_cols[1]:
            st.markdown("")
            st.markdown("")
            if st.button("✅ Assign Filtered Leads", type="primary", use_container_width=True, key="std_assign_btn"):
                if not salesperson:
                    st.warning("Please select a salesperson.")
                else:
                    try:
                        conn = get_connection()
                        cur = conn.cursor()
                        cur.execute(
                            "UPDATE vendor_data SET assigned_to = %s, assigned_on = NOW() WHERE uuid = ANY(%s)",
                            (salesperson, df_filtered['uuid'].tolist())
                        )
                        conn.commit()
                        cur.close()
                        conn.close()
                        st.success(f"✅ Assigned {len(df_filtered):,} leads to {salesperson}!")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        st.warning("⚠️ No records match the current filters.")
    
    # Summary sections
    st.markdown("---")
    summary_tab1, summary_tab2 = st.tabs(["📊 Assignment Summary", "📈 Status Summary"])
    
    with summary_tab1:
        conn = get_connection()
        df_assign = pd.read_sql(
            """
            SELECT COALESCE(assigned_to, 'Unassigned') as assigned_to, COUNT(*) as total,
                   MIN(assigned_on) as first_assigned, MAX(assigned_on) as last_assigned
            FROM vendor_data GROUP BY assigned_to ORDER BY total DESC
            """, conn
        )
        conn.close()
        st.dataframe(df_assign, use_container_width=True, height=400)
    
    with summary_tab2:
        if 'status' in df.columns:
            conn = get_connection()
            df_status = pd.read_sql(
                """
                SELECT COALESCE(status, 'Not Set') as status, COUNT(*) as total,
                       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM vendor_data), 2) as percentage
                FROM vendor_data GROUP BY status ORDER BY total DESC
                """, conn
            )
            conn.close()
            st.dataframe(df_status, use_container_width=True, height=400)
            
            if not df_status.empty:
                fig = px.bar(df_status, x='status', y='total', text='total', title="Lead Status Distribution",
                            color='status', color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_traces(textposition='outside')
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Status column not available. Create it to see status summary.")

# ===============================
# 🌐 ADMIN DASHBOARD
# ===============================
def admin_dashboard():
    st.sidebar.header("Admin Navigation")
    page = st.sidebar.radio("Choose Section", ["Add Users", "Standard Assignment", "Bulk Assignment", "Assignment History", "View Users", "Lead Insights"])
    
    if page == "Lead Insights":
        lead_insights_dashboard()
    elif page == "Add Users":
        st.subheader("Add a new user")
        new_email = st.text_input("User Email")
        new_pass = st.text_input("User Password", type="password")
        role = st.selectbox("Role", ["user", "admin"])
        if st.button("Add User"):
            if new_email and new_pass:
                add_user(new_email, new_pass, role)
            else:
                st.warning("Please fill all fields.")
    elif page == "View Users":
        st.subheader("👥 All Users")
        show_user_table()
    elif page == "Standard Assignment":
        standard_assignment()
    elif page == "Bulk Assignment":
        bulk_assignment_interface()
    elif page == "Assignment History":
        show_assignment_history()

# ===============================
# 🚪 LOGIN SYSTEM
# ===============================
def login_screen():
    st.title("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        role = authenticate_user(email, password)
        if role:
            st.session_state.logged_in = True
            st.session_state.role = role
            st.session_state.email = email
            st.rerun()
        else:
            st.error("❌ Invalid credentials.")

# ===============================
# 🧠 MAIN FUNCTION
# ===============================
def main():
    st.set_page_config(page_title="Vendor Assignment System", page_icon="🧩", layout="wide")
    
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.email = None
    
    if st.session_state.logged_in:
        st.sidebar.success(f"Logged in as: {st.session_state.email}")
        if st.sidebar.button("Logout"):
            st.session_state.clear()
            st.rerun()
    
    if not st.session_state.logged_in:
        login_screen()
    elif st.session_state.role == "admin":
        admin_dashboard()
    else:
        user_dashboard()

if __name__ == "__main__":
    main()