# ===============================
# 📊 LEAD INSIGHTS DASHBOARD (Admin/User)
# ===============================
import plotly.express as px
import pandas as pd
import streamlit as st
import psycopg2


# --- Database connection utility ---
def get_connection():
    return psycopg2.connect(
        host="localhost",
        dbname="postgres",
        user="postgres",
        password="manan",
        port=5433
    )

# ===============================
# def lead_insights_dashboard(assigned_to=None):
#     """
#     Lead Insights Dashboard with optional user filtering
    
#     Args:
#         assigned_to (str, optional): Email of user to filter leads by. 
#                                      If None, shows all leads (admin view)
#     """
#     st.title("📊 Lead Insights Dashboard")
    
#     # --- Load data from DB ---
#     try:
#         conn = get_connection()
#         if assigned_to:
#             # User view - only their assigned leads
#             query = "SELECT * FROM vendor_data WHERE assigned_to = %s"
#             df = pd.read_sql(query, conn, params=[assigned_to])
#             st.info(f"📊 Your assigned records: {len(df):,}")
            
#             if df.empty:
#                 st.warning(f"No records assigned to {assigned_to} yet.")
#                 conn.close()
#                 return
#         else:
#             # Admin view - all leads
#             query = "SELECT * FROM vendor_data"
#             df = pd.read_sql(query, conn)
#             st.info(f"📊 Total records loaded: {len(df):,}")
            
#             if df.empty:
#                 st.warning("No data found in vendor_data table.")
#                 conn.close()
#                 return
        
#         conn.close()
#     except Exception as e:
#         st.error(f"Database error: {e}")
#         return
    
#     # Initialize session state for filters
#     filter_key = f"insight_filters_{assigned_to}" if assigned_to else "insight_filters"
#     if filter_key not in st.session_state:
#         st.session_state[filter_key] = {}
    
#     # ===============================
#     # 🎯 MULTI-COLUMN FILTERING SYSTEM
#     # ===============================
#     st.sidebar.markdown("### 🎯 Apply Filters (Multi-Column)")
#     st.sidebar.caption("Filter data before analysis. All filters use AND logic.")
    
#     # Get valid columns for filtering
#     valid_columns = [c for c in df.columns if df[c].dtype in ["object", "int64", "float64"]]
    
#     # --- Text Search Filters ---
#     with st.sidebar.expander("🔤 Text Search", expanded=False):
#         text_cols = st.multiselect(
#             "Select columns to search",
#             options=[c for c in valid_columns if df[c].dtype == 'object'],
#             key=f"insight_text_cols_{assigned_to}"
#         )
        
#         for col in text_cols:
#             search_val = st.text_input(
#                 f"Search {col}",
#                 key=f"insight_search_{col}_{assigned_to}",
#                 placeholder=f"Type keyword..."
#             )
#             if search_val:
#                 st.session_state[filter_key][col] = {
#                     'type': 'text',
#                     'value': search_val
#                 }
#             elif col in st.session_state[filter_key] and st.session_state[filter_key][col].get('type') == 'text':
#                 del st.session_state[filter_key][col]
    
#     # --- Dropdown Filters ---
#     with st.sidebar.expander("📋 Exact Match (Dropdown)", expanded=True):
#         dropdown_cols = st.multiselect(
#             "Select columns for filtering",
#             options=[c for c in valid_columns if df[c].dtype == 'object' and df[c].nunique() <= 100],
#             key=f"insight_dropdown_cols_{assigned_to}",
#             help="Only columns with ≤100 unique values shown"
#         )
        
#         for col in dropdown_cols:
#             unique_vals = sorted(df[col].astype(str).dropna().unique().tolist())
#             unique_vals = [v for v in unique_vals if str(v).strip() not in ['', 'nan', 'None']]
            
#             selected = st.multiselect(
#                 f"{col}",
#                 options=unique_vals,
#                 key=f"insight_dropdown_{col}_{assigned_to}",
#                 placeholder=f"Select {col}..."
#             )
            
#             if selected:
#                 st.session_state[filter_key][col] = {
#                     'type': 'dropdown',
#                     'value': selected
#                 }
#             elif col in st.session_state[filter_key] and st.session_state[filter_key][col].get('type') == 'dropdown':
#                 del st.session_state[filter_key][col]
    
#     # --- Numeric Range Filters ---
#     with st.sidebar.expander("🔢 Numeric Range", expanded=False):
#         numeric_cols = st.multiselect(
#             "Select numeric columns",
#             options=[c for c in valid_columns if pd.api.types.is_numeric_dtype(df[c])],
#             key=f"insight_numeric_cols_{assigned_to}"
#         )
        
#         for col in numeric_cols:
#             try:
#                 min_val = float(df[col].min())
#                 max_val = float(df[col].max())
                
#                 range_val = st.slider(
#                     f"{col}",
#                     min_value=min_val,
#                     max_value=max_val,
#                     value=(min_val, max_val),
#                     key=f"insight_range_{col}_{assigned_to}"
#                 )
                
#                 if range_val != (min_val, max_val):
#                     st.session_state[filter_key][col] = {
#                         'type': 'range',
#                         'value': range_val
#                     }
#                 elif col in st.session_state[filter_key] and st.session_state[filter_key][col].get('type') == 'range':
#                     del st.session_state[filter_key][col]
#             except:
#                 st.warning(f"Could not create range filter for {col}")
    
#     # --- Clear Filters Button ---
#     if st.session_state[filter_key]:
#         st.sidebar.markdown("---")
#         if st.sidebar.button("🧹 Clear All Filters", type="secondary", use_container_width=True, key=f"clear_filters_{assigned_to}"):
#             st.session_state[filter_key] = {}
#             st.rerun()
        
#         # Show active filters
#         st.sidebar.markdown("##### 🎯 Active Filters:")
#         for col, config in st.session_state[filter_key].items():
#             if config['type'] == 'text':
#                 st.sidebar.caption(f"✓ `{col}` contains '{config['value']}'")
#             elif config['type'] == 'dropdown':
#                 st.sidebar.caption(f"✓ `{col}` in {len(config['value'])} values")
#             elif config['type'] == 'range':
#                 st.sidebar.caption(f"✓ `{col}` [{config['value'][0]:.1f} - {config['value'][1]:.1f}]")
    
#     # ===============================
#     # 🔄 APPLY FILTERS TO DATAFRAME
#     # ===============================
#     df_filtered = df.copy()
    
#     for col, filter_config in st.session_state[filter_key].items():
#         filter_type = filter_config['type']
#         filter_value = filter_config['value']
        
#         if filter_type == 'text':
#             mask = df_filtered[col].astype(str).str.contains(filter_value, case=False, na=False)
#             df_filtered = df_filtered[mask]
        
#         elif filter_type == 'dropdown':
#             mask = df_filtered[col].astype(str).isin(filter_value)
#             df_filtered = df_filtered[mask]
        
#         elif filter_type == 'range':
#             mask = (df_filtered[col] >= filter_value[0]) & (df_filtered[col] <= filter_value[1])
#             df_filtered = df_filtered[mask]
    
#     # Show filter impact
#     if st.session_state[filter_key]:
#         filter_impact = ((len(df) - len(df_filtered)) / len(df) * 100) if len(df) > 0 else 0
#         st.info(f"🎯 **Filters Applied:** {len(st.session_state[filter_key])} | **Showing:** {len(df_filtered):,} / {len(df):,} records ({100-filter_impact:.1f}%)")
    
#     if df_filtered.empty:
#         st.warning("⚠️ No records match the current filters. Try adjusting your criteria.")
#         return
    
#     st.markdown("---")
    
#     # ===============================
#     # 📊 ANALYSIS DIMENSION SELECTION
#     # ===============================
#     st.markdown("### 📊 Select Analysis Dimension")
    
#     analysis_cols = st.columns([2, 2, 1])
    
#     with analysis_cols[0]:
#         valid_analysis_cols = [c for c in df_filtered.columns if df_filtered[c].dtype in ["object", "int64", "float64"]]
#         selected_col = st.selectbox(
#             "Analyze this column:",
#             options=valid_analysis_cols,
#             index=valid_analysis_cols.index("country_preference") if "country_preference" in valid_analysis_cols else 0,
#             key=f"selected_analysis_col_{assigned_to}"
#         )
    
#     with analysis_cols[1]:
#         top_n = st.slider("Show top N categories", 5, 50, 25, key=f"top_n_slider_{assigned_to}")
    
#     with analysis_cols[2]:
#         st.markdown("")
#         view_mode = st.radio("View", ["Table", "Charts"], horizontal=True, key=f"view_mode_{assigned_to}")
    
#     if not selected_col:
#         st.warning("Please select a column to analyze.")
#         return
    
#     # ===============================
#     # 🧹 CLEAN AND PROCESS SELECTED COLUMN
#     # ===============================
#     df_work = df_filtered.copy()
#     df_work[selected_col] = df_work[selected_col].astype(str).str.strip().str.lower()
#     df_work[selected_col] = df_work[selected_col].replace(["", "nan", "none", "null", "na"], pd.NA)
#     df_clean = df_work[df_work[selected_col].notna()].copy()
    
#     if df_clean.empty:
#         st.warning(f"No valid data found in column '{selected_col}' after cleaning.")
#         return
    
#     # Count values
#     col_counts = df_clean[selected_col].value_counts().reset_index()
#     col_counts.columns = [selected_col, "count"]
    
#     # Calculate percentage
#     total = col_counts["count"].sum()
#     col_counts["percentage"] = (col_counts["count"] / total * 100).round(2)
#     col_counts = col_counts.sort_values(by="count", ascending=False).reset_index(drop=True)
    
#     # Apply top N
#     original_count = len(col_counts)
#     col_counts_display = col_counts.head(top_n).copy()
    
#     # ===============================
#     # 📈 DISPLAY SUMMARY STATISTICS
#     # ===============================
#     metric_cols = st.columns(4)
    
#     with metric_cols[0]:
#         st.metric("📊 Total Records", f"{total:,}")
    
#     with metric_cols[1]:
#         st.metric("🔢 Unique Values", original_count)
    
#     with metric_cols[2]:
#         top_val = col_counts.iloc[0][selected_col]
#         st.metric("🏆 Top Category", f"{top_val[:12]}...")
    
#     with metric_cols[3]:
#         top_count = col_counts.iloc[0]["count"]
#         top_pct = col_counts.iloc[0]["percentage"]
#         st.metric("📍 Top Count", f"{top_count:,}", f"{top_pct:.1f}%")
    
#     st.markdown("---")
    
#     # ===============================
#     # 📊 CHARTS OR TABLE VIEW
#     # ===============================
#     if view_mode == "Charts":
#         chart_cols = st.columns(2)
        
#         with chart_cols[0]:
#             st.markdown(f"#### 📊 {selected_col.replace('_', ' ').title()} - Bar Chart")
            
#             fig_bar = px.bar(
#                 col_counts_display,
#                 x=selected_col,
#                 y="count",
#                 text="count",
#                 color="count",
#                 color_continuous_scale="Blues"
#             )
#             fig_bar.update_traces(
#                 texttemplate='%{text:,}',
#                 textposition='outside'
#             )
#             fig_bar.update_layout(
#                 xaxis_tickangle=-45,
#                 height=500,
#                 showlegend=False,
#                 xaxis_title="",
#                 yaxis_title="Count"
#             )
#             st.plotly_chart(fig_bar, use_container_width=True)
        
#         with chart_cols[1]:
#             st.markdown(f"#### 🥧 {selected_col.replace('_', ' ').title()} - Pie Chart")
            
#             fig_pie = px.pie(
#                 col_counts_display,
#                 names=selected_col,
#                 values="count",
#                 hole=0.4,
#                 color_discrete_sequence=px.colors.qualitative.Set3
#             )
#             fig_pie.update_traces(
#                 textposition='auto',
#                 textinfo='label+percent'
#             )
#             fig_pie.update_layout(height=500)
#             st.plotly_chart(fig_pie, use_container_width=True)
    
#     # ===============================
#     # 📋 DATA TABLE VIEW
#     # ===============================
#     st.markdown("---")
#     st.markdown(f"### 📋 {selected_col.replace('_', ' ').title()} Distribution Table")
    
#     # Format display
#     display_df = col_counts_display.copy()
#     display_df["count_formatted"] = display_df["count"].apply(lambda x: f"{x:,}")
#     display_df["percentage_formatted"] = display_df["percentage"].apply(lambda x: f"{x}%")
    
#     # Create display columns
#     show_df = display_df[[selected_col, "count_formatted", "percentage_formatted"]].copy()
#     show_df.columns = [selected_col.replace('_', ' ').title(), "Count", "Percentage"]
    
#     st.dataframe(
#         show_df,
#         use_container_width=True,
#         hide_index=True,
#         height=400
#     )
    
#     # ===============================
#     # 📥 DOWNLOAD OPTIONS
#     # ===============================
#     download_cols = st.columns([1, 1, 2])
    
#     with download_cols[0]:
#         csv = col_counts.to_csv(index=False).encode('utf-8')
#         st.download_button(
#             label="📥 Download Full Data",
#             data=csv,
#             file_name=f"{selected_col}_distribution_full.csv",
#             mime="text/csv",
#             use_container_width=True,
#             key=f"download_full_{assigned_to}"
#         )
    
#     with download_cols[1]:
#         csv_top = col_counts_display.to_csv(index=False).encode('utf-8')
#         st.download_button(
#             label=f"📥 Download Top {top_n}",
#             data=csv_top,
#             file_name=f"{selected_col}_distribution_top{top_n}.csv",
#             mime="text/csv",
#             use_container_width=True,
#             key=f"download_top_{assigned_to}"
#         )
    
#     # ===============================
#     # 💡 INSIGHTS SECTION
#     # ===============================
#     with st.expander("💡 Quick Insights", expanded=False):
#         # Calculate insights
#         top_3 = col_counts.head(3)
#         top_3_pct = top_3["percentage"].sum()
        
#         st.markdown(f"""
#         **📊 Distribution Analysis for `{selected_col}`:**
        
#         - **Total Categories:** {original_count:,}
#         - **Showing:** Top {min(top_n, original_count)} categories
#         - **Top 3 Dominance:** {top_3_pct:.1f}% of all records
        
#         **🏆 Top 3 Categories:**
#         """)
        
#         for idx, row in top_3.iterrows():
#             st.markdown(f"{idx + 1}. **{row[selected_col]}** → {row['count']:,} records ({row['percentage']:.1f}%)")
        
#         # Distribution type
#         if top_3_pct > 75:
#             st.info("📌 **High Concentration:** Top 3 categories represent >75% of data")
#         elif top_3_pct < 30:
#             st.info("📌 **Well Distributed:** Data is spread across many categories")
#         else:
#             st.info("📌 **Moderate Distribution:** Balanced spread across categories")

# def lead_insights_dashboard(assigned_to=None):
#     """
#     Enhanced Lead Insights Dashboard with multi-dimensional analysis
    
#     Args:
#         assigned_to (str, optional): Email of user to filter leads by. 
#                                      If None, shows all leads (admin view)
#     """
#     st.title("📊 Lead Insights Dashboard")
    
#     # --- Load data from DB ---
#     try:
#         conn = get_connection()
#         if assigned_to:
#             query = "SELECT * FROM vendor_data WHERE assigned_to = %s"
#             df = pd.read_sql(query, conn, params=[assigned_to])
#             st.info(f"📊 Your assigned records: {len(df):,}")
            
#             if df.empty:
#                 st.warning(f"No records assigned to {assigned_to} yet.")
#                 conn.close()
#                 return
#         else:
#             query = "SELECT * FROM vendor_data"
#             df = pd.read_sql(query, conn)
#             st.info(f"📊 Total records loaded: {len(df):,}")
            
#             if df.empty:
#                 st.warning("No data found in vendor_data table.")
#                 conn.close()
#                 return
        
#         conn.close()
#     except Exception as e:
#         st.error(f"Database error: {e}")
#         return
    
#     # Initialize session state for filters
#     filter_key = f"insight_filters_{assigned_to}" if assigned_to else "insight_filters"
#     if filter_key not in st.session_state:
#         st.session_state[filter_key] = {}
    
#     # ===============================
#     # 🎯 MULTI-COLUMN FILTERING SYSTEM
#     # ===============================
#     st.sidebar.markdown("### 🎯 Apply Filters (Multi-Column)")
#     st.sidebar.caption("Filter data before analysis. All filters use AND logic.")
    
#     valid_columns = [c for c in df.columns if df[c].dtype in ["object", "int64", "float64"]]
    
#     # --- Text Search Filters ---
#     with st.sidebar.expander("🔤 Text Search", expanded=False):
#         text_cols = st.multiselect(
#             "Select columns to search",
#             options=[c for c in valid_columns if df[c].dtype == 'object'],
#             key=f"insight_text_cols_{assigned_to}"
#         )
        
#         for col in text_cols:
#             search_val = st.text_input(
#                 f"Search {col}",
#                 key=f"insight_search_{col}_{assigned_to}",
#                 placeholder=f"Type keyword..."
#             )
#             if search_val:
#                 st.session_state[filter_key][col] = {'type': 'text', 'value': search_val}
#             elif col in st.session_state[filter_key] and st.session_state[filter_key][col].get('type') == 'text':
#                 del st.session_state[filter_key][col]
    
#     # --- Dropdown Filters ---
#     with st.sidebar.expander("📋 Exact Match (Dropdown)", expanded=True):
#         dropdown_cols = st.multiselect(
#             "Select columns for filtering",
#             options=[c for c in valid_columns if df[c].dtype == 'object' and df[c].nunique() <= 100],
#             key=f"insight_dropdown_cols_{assigned_to}",
#             help="Only columns with ≤100 unique values shown"
#         )
        
#         for col in dropdown_cols:
#             unique_vals = sorted(df[col].astype(str).dropna().unique().tolist())
#             unique_vals = [v for v in unique_vals if str(v).strip() not in ['', 'nan', 'None']]
            
#             selected = st.multiselect(
#                 f"{col}",
#                 options=unique_vals,
#                 key=f"insight_dropdown_{col}_{assigned_to}",
#                 placeholder=f"Select {col}..."
#             )
            
#             if selected:
#                 st.session_state[filter_key][col] = {'type': 'dropdown', 'value': selected}
#             elif col in st.session_state[filter_key] and st.session_state[filter_key][col].get('type') == 'dropdown':
#                 del st.session_state[filter_key][col]
    
#     # --- Numeric Range Filters ---
#     with st.sidebar.expander("🔢 Numeric Range", expanded=False):
#         numeric_cols = st.multiselect(
#             "Select numeric columns",
#             options=[c for c in valid_columns if pd.api.types.is_numeric_dtype(df[c])],
#             key=f"insight_numeric_cols_{assigned_to}"
#         )
        
#         for col in numeric_cols:
#             try:
#                 min_val = float(df[col].min())
#                 max_val = float(df[col].max())
                
#                 range_val = st.slider(
#                     f"{col}",
#                     min_value=min_val,
#                     max_value=max_val,
#                     value=(min_val, max_val),
#                     key=f"insight_range_{col}_{assigned_to}"
#                 )
                
#                 if range_val != (min_val, max_val):
#                     st.session_state[filter_key][col] = {'type': 'range', 'value': range_val}
#                 elif col in st.session_state[filter_key] and st.session_state[filter_key][col].get('type') == 'range':
#                     del st.session_state[filter_key][col]
#             except:
#                 st.warning(f"Could not create range filter for {col}")
    
#     # --- Clear Filters Button ---
#     if st.session_state[filter_key]:
#         st.sidebar.markdown("---")
#         if st.sidebar.button("🧹 Clear All Filters", type="secondary", use_container_width=True, key=f"clear_filters_{assigned_to}"):
#             st.session_state[filter_key] = {}
#             st.rerun()
        
#         st.sidebar.markdown("##### 🎯 Active Filters:")
#         for col, config in st.session_state[filter_key].items():
#             if config['type'] == 'text':
#                 st.sidebar.caption(f"✓ `{col}` contains '{config['value']}'")
#             elif config['type'] == 'dropdown':
#                 st.sidebar.caption(f"✓ `{col}` in {len(config['value'])} values")
#             elif config['type'] == 'range':
#                 st.sidebar.caption(f"✓ `{col}` [{config['value'][0]:.1f} - {config['value'][1]:.1f}]")
    
#     # ===============================
#     # 🔄 APPLY FILTERS TO DATAFRAME
#     # ===============================
#     df_filtered = df.copy()
    
#     for col, filter_config in st.session_state[filter_key].items():
#         filter_type = filter_config['type']
#         filter_value = filter_config['value']
        
#         if filter_type == 'text':
#             mask = df_filtered[col].astype(str).str.contains(filter_value, case=False, na=False)
#             df_filtered = df_filtered[mask]
#         elif filter_type == 'dropdown':
#             mask = df_filtered[col].astype(str).isin(filter_value)
#             df_filtered = df_filtered[mask]
#         elif filter_type == 'range':
#             mask = (df_filtered[col] >= filter_value[0]) & (df_filtered[col] <= filter_value[1])
#             df_filtered = df_filtered[mask]
    
#     if st.session_state[filter_key]:
#         filter_impact = ((len(df) - len(df_filtered)) / len(df) * 100) if len(df) > 0 else 0
#         st.info(f"🎯 **Filters Applied:** {len(st.session_state[filter_key])} | **Showing:** {len(df_filtered):,} / {len(df):,} records ({100-filter_impact:.1f}%)")
    
#     if df_filtered.empty:
#         st.warning("⚠️ No records match the current filters. Try adjusting your criteria.")
#         return
    
#     st.markdown("---")
    
#     # ===============================
#     # 📊 OVERVIEW SUMMARY METRICS
#     # ===============================
#     st.markdown("### 📊 Overview Summary")
    
#     metric_cols = st.columns(5)
    
#     # Calculate key metrics
#     total_leads = len(df_filtered)
    
#     # Email availability
#     email_cols = [c for c in df_filtered.columns if 'email' in c.lower()]
#     leads_with_email = 0
#     if email_cols:
#         for col in email_cols:
#             leads_with_email += df_filtered[col].notna().sum()
#         leads_with_email = min(leads_with_email, total_leads)
    
#     # Unique countries
#     country_cols = [c for c in df_filtered.columns if 'country' in c.lower()]
#     unique_countries = 0
#     if country_cols:
#         unique_countries = df_filtered[country_cols[0]].nunique()
    
#     # Assignment rate
#     assigned_cols = [c for c in df_filtered.columns if 'assigned' in c.lower()]
#     leads_assigned = 0
#     if assigned_cols:
#         leads_assigned = df_filtered[assigned_cols[0]].notna().sum()
    
#     # Conversion/Status check
#     status_cols = [c for c in df_filtered.columns if 'status' in c.lower() or 'stage' in c.lower()]
#     conversion_rate = 0
#     if status_cols:
#         converted = df_filtered[status_cols[0]].astype(str).str.lower().str.contains('convert|won|closed|success', na=False).sum()
#         conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0
    
#     with metric_cols[0]:
#         st.metric("📊 Total Leads", f"{total_leads:,}")
    
#     with metric_cols[1]:
#         email_pct = (leads_with_email / total_leads * 100) if total_leads > 0 else 0
#         st.metric("📧 With Email", f"{leads_with_email:,}", f"{email_pct:.1f}%")
    
#     with metric_cols[2]:
#         st.metric("🌍 Unique Countries", f"{unique_countries:,}")
    
#     with metric_cols[3]:
#         assigned_pct = (leads_assigned / total_leads * 100) if total_leads > 0 else 0
#         st.metric("👤 Assigned", f"{leads_assigned:,}", f"{assigned_pct:.1f}%")
    
#     with metric_cols[4]:
#         st.metric("✅ Conversion Rate", f"{conversion_rate:.1f}%")
    
#     st.markdown("---")
    
#     # ===============================
#     # 🔍 ANALYSIS TYPE SELECTION
#     # ===============================
#     st.markdown("### 🔍 Select Analysis Type")
    
#     analysis_type = st.radio(
#         "Choose analysis:",
#         ["Single Column Distribution", "Cross-Column Analysis", "Trend & Time Analysis"],
#         horizontal=True,
#         key=f"analysis_type_{assigned_to}"
#     )
    
#     st.markdown("---")
    
#     # ===============================
#     # ANALYSIS TYPE 1: SINGLE COLUMN
#     # ===============================
#     if analysis_type == "Single Column Distribution":
#         analysis_cols = st.columns([2, 1, 1])
        
#         with analysis_cols[0]:
#             valid_analysis_cols = [c for c in df_filtered.columns if df_filtered[c].dtype in ["object", "int64", "float64"]]
#             selected_col = st.selectbox(
#                 "Analyze this column:",
#                 options=valid_analysis_cols,
#                 key=f"selected_analysis_col_{assigned_to}"
#             )
        
#         with analysis_cols[1]:
#             top_n = st.slider("Show top N", 5, 50, 15, key=f"top_n_slider_{assigned_to}")
        
#         with analysis_cols[2]:
#             chart_type = st.selectbox("Chart", ["Bar", "Pie", "Both"], key=f"chart_type_{assigned_to}")
        
#         if selected_col:
#             # Clean data
#             df_work = df_filtered.copy()
#             df_work[selected_col] = df_work[selected_col].astype(str).str.strip().str.lower()
#             df_work[selected_col] = df_work[selected_col].replace(["", "nan", "none", "null", "na"], pd.NA)
#             df_clean = df_work[df_work[selected_col].notna()].copy()
            
#             if not df_clean.empty:
#                 col_counts = df_clean[selected_col].value_counts().reset_index()
#                 col_counts.columns = [selected_col, "count"]
#                 total = col_counts["count"].sum()
#                 col_counts["percentage"] = (col_counts["count"] / total * 100).round(2)
#                 col_counts = col_counts.sort_values(by="count", ascending=False).reset_index(drop=True)
                
#                 original_count = len(col_counts)
#                 col_counts_display = col_counts.head(top_n).copy()
                
#                 # Display metrics
#                 metric_cols2 = st.columns(4)
#                 with metric_cols2[0]:
#                     st.metric("📊 Valid Records", f"{total:,}")
#                 with metric_cols2[1]:
#                     st.metric("🔢 Unique Values", original_count)
#                 with metric_cols2[2]:
#                     top_val = str(col_counts.iloc[0][selected_col])[:15]
#                     st.metric("🏆 Top Category", top_val)
#                 with metric_cols2[3]:
#                     top_pct = col_counts.iloc[0]["percentage"]
#                     st.metric("📍 Top %", f"{top_pct:.1f}%")
                
#                 st.markdown("---")
                
#                 # Charts
#                 if chart_type in ["Bar", "Both"]:
#                     fig_bar = px.bar(
#                         col_counts_display,
#                         x=selected_col,
#                         y="count",
#                         text="count",
#                         color="count",
#                         color_continuous_scale="Blues",
#                         title=f"{selected_col.replace('_', ' ').title()} Distribution"
#                     )
#                     fig_bar.update_traces(texttemplate='%{text:,}', textposition='outside')
#                     fig_bar.update_layout(xaxis_tickangle=-45, height=450, showlegend=False)
#                     st.plotly_chart(fig_bar, use_container_width=True)
                
#                 if chart_type in ["Pie", "Both"]:
#                     fig_pie = px.pie(
#                         col_counts_display,
#                         names=selected_col,
#                         values="count",
#                         hole=0.4,
#                         title=f"{selected_col.replace('_', ' ').title()} Composition"
#                     )
#                     fig_pie.update_traces(textposition='auto', textinfo='label+percent')
#                     st.plotly_chart(fig_pie, use_container_width=True)
                
#                 # Insights
#                 with st.expander("💡 Advanced Insights", expanded=True):
#                     top_3 = col_counts.head(3)
#                     top_3_pct = top_3["percentage"].sum()
                    
#                     st.markdown(f"**🏆 Top 3 Performers:**")
#                     for idx, row in top_3.iterrows():
#                         st.markdown(f"{idx + 1}. **{row[selected_col]}** → {row['count']:,} leads ({row['percentage']:.1f}%)")
                    
#                     st.markdown(f"\n**📊 Distribution Pattern:**")
#                     if top_3_pct > 75:
#                         st.warning(f"⚠️ **High Concentration Alert:** Top 3 represent {top_3_pct:.1f}% - consider diversification")
#                     elif top_3_pct < 30:
#                         st.success(f"✅ **Well Distributed:** Top 3 only {top_3_pct:.1f}% - healthy spread")
#                     else:
#                         st.info(f"📌 **Moderate Concentration:** Top 3 represent {top_3_pct:.1f}%")
                    
#                     # Data quality
#                     missing_pct = ((len(df_filtered) - total) / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
#                     if missing_pct > 10:
#                         st.warning(f"⚠️ **Data Quality Alert:** {missing_pct:.1f}% missing/invalid values in {selected_col}")
#                     elif missing_pct > 0:
#                         st.info(f"ℹ️ Data Completeness: {100-missing_pct:.1f}% ({missing_pct:.1f}% missing)")
#                     else:
#                         st.success(f"✅ Perfect data quality - no missing values")
                
#                 # Download
#                 csv = col_counts.to_csv(index=False).encode('utf-8')
#                 st.download_button(
#                     "📥 Download Analysis",
#                     data=csv,
#                     file_name=f"{selected_col}_analysis.csv",
#                     mime="text/csv",
#                     key=f"download_{assigned_to}"
#                 )
    
#     # ===============================
#     # ANALYSIS TYPE 2: CROSS-COLUMN
#     # ===============================
#     elif analysis_type == "Cross-Column Analysis":
#         st.markdown("### 🔗 Cross-Column Relationship Analysis")
        
#         cross_cols = st.columns(2)
        
#         with cross_cols[0]:
#             valid_cols = [c for c in df_filtered.columns if df_filtered[c].dtype == 'object']
#             col1 = st.selectbox("Primary Dimension:", options=valid_cols, key=f"cross_col1_{assigned_to}")
        
#         with cross_cols[1]:
#             col2 = st.selectbox("Secondary Dimension:", options=valid_cols, key=f"cross_col2_{assigned_to}")
        
#         if col1 and col2 and col1 != col2:
#             # Create cross-tabulation
#             df_cross = df_filtered[[col1, col2]].copy()
#             df_cross[col1] = df_cross[col1].astype(str).str.strip()
#             df_cross[col2] = df_cross[col2].astype(str).str.strip()
            
#             # Remove invalid values
#             df_cross = df_cross[
#                 (~df_cross[col1].isin(['', 'nan', 'None', 'null'])) &
#                 (~df_cross[col2].isin(['', 'nan', 'None', 'null']))
#             ]
            
#             if not df_cross.empty:
#                 # Create pivot table
#                 pivot = pd.crosstab(df_cross[col1], df_cross[col2], margins=True)
                
#                 # Show top combinations
#                 combo_counts = df_cross.groupby([col1, col2]).size().reset_index(name='count')
#                 combo_counts = combo_counts.sort_values('count', ascending=False).head(20)
#                 combo_counts['percentage'] = (combo_counts['count'] / len(df_cross) * 100).round(2)
                
#                 st.markdown("#### 🏆 Top Combinations")
                
#                 # Create sunburst chart
#                 fig_sunburst = px.sunburst(
#                     combo_counts.head(15),
#                     path=[col1, col2],
#                     values='count',
#                     title=f"{col1} → {col2} Relationship"
#                 )
#                 st.plotly_chart(fig_sunburst, use_container_width=True)
                
#                 # Show table
#                 st.dataframe(combo_counts.head(15), use_container_width=True)
                
#                 # Insights
#                 with st.expander("💡 Cross-Column Insights", expanded=True):
#                     top_combo = combo_counts.iloc[0]
#                     st.markdown(f"**🎯 Dominant Combination:**")
#                     st.success(f"{top_combo[col1]} + {top_combo[col2]} → {top_combo['count']:,} leads ({top_combo['percentage']:.1f}%)")
                    
#                     # Find unique patterns
#                     col1_unique = df_cross[col1].nunique()
#                     col2_unique = df_cross[col2].nunique()
#                     st.markdown(f"\n**📊 Diversity Metrics:**")
#                     st.info(f"• {col1}: {col1_unique} unique values\n• {col2}: {col2_unique} unique values\n• Combinations: {len(combo_counts)} observed")
#         else:
#             st.info("👆 Select two different columns to analyze their relationship")
    
#     # ===============================
#     # ANALYSIS TYPE 3: TREND/TIME
#     # ===============================
#     else:  # Trend & Time Analysis
#         st.markdown("### 📈 Trend & Time-Based Analysis")
        
#         date_cols = [c for c in df_filtered.columns if 'date' in c.lower() or 'time' in c.lower() or 'created' in c.lower()]
        
#         if date_cols:
#             time_col = st.selectbox("Select time column:", options=date_cols, key=f"time_col_{assigned_to}")
            
#             if time_col:
#                 try:
#                     df_time = df_filtered.copy()
#                     df_time[time_col] = pd.to_datetime(df_time[time_col], errors='coerce')
#                     df_time = df_time[df_time[time_col].notna()]
                    
#                     if not df_time.empty:
#                         # Group by period
#                         period = st.radio("Group by:", ["Day", "Week", "Month"], horizontal=True, key=f"period_{assigned_to}")
                        
#                         if period == "Day":
#                             df_time['period'] = df_time[time_col].dt.date
#                         elif period == "Week":
#                             df_time['period'] = df_time[time_col].dt.to_period('W').astype(str)
#                         else:
#                             df_time['period'] = df_time[time_col].dt.to_period('M').astype(str)
                        
#                         trend_data = df_time.groupby('period').size().reset_index(name='count')
#                         trend_data = trend_data.sort_values('period')
                        
#                         # Line chart
#                         fig_trend = px.line(
#                             trend_data,
#                             x='period',
#                             y='count',
#                             markers=True,
#                             title=f"Lead Volume Trend ({period}ly)"
#                         )
#                         fig_trend.update_layout(xaxis_tickangle=-45, height=400)
#                         st.plotly_chart(fig_trend, use_container_width=True)
                        
#                         # Trend insights
#                         with st.expander("💡 Trend Insights", expanded=True):
#                             avg_leads = trend_data['count'].mean()
#                             peak_period = trend_data.loc[trend_data['count'].idxmax(), 'period']
#                             peak_count = trend_data['count'].max()
                            
#                             st.markdown(f"**📊 Trend Analysis:**")
#                             st.info(f"• Average {period}ly leads: {avg_leads:.0f}\n• Peak period: {peak_period} ({peak_count:,} leads)\n• Total periods: {len(trend_data)}")
                            
#                             # Growth rate
#                             if len(trend_data) > 1:
#                                 latest = trend_data.iloc[-1]['count']
#                                 previous = trend_data.iloc[-2]['count']
#                                 growth = ((latest - previous) / previous * 100) if previous > 0 else 0
                                
#                                 if growth > 10:
#                                     st.success(f"📈 Growing: +{growth:.1f}% vs previous {period.lower()}")
#                                 elif growth < -10:
#                                     st.warning(f"📉 Declining: {growth:.1f}% vs previous {period.lower()}")
#                                 else:
#                                     st.info(f"➡️ Stable: {growth:+.1f}% vs previous {period.lower()}")
#                 except:
#                     st.error("Unable to parse dates in selected column")
#         else:
#             st.info("⚠️ No date/time columns found in the data")

# def lead_insights_dashboard(assigned_to=None):
#     """
#     Enhanced Lead Insights Dashboard with multi-dimensional analysis
    
#     Args:
#         assigned_to (str, optional): Email of user to filter leads by. 
#                                      If None, shows all leads (admin view)
#     """
#     st.title("📊 Lead Insights Dashboard")
    
#     # --- Load data from DB ---
#     try:
#         conn = get_connection()
#         if assigned_to:
#             query = "SELECT * FROM vendor_data WHERE assigned_to = %s"
#             df = pd.read_sql(query, conn, params=[assigned_to])
#             st.info(f"📊 Your assigned records: {len(df):,}")
            
#             if df.empty:
#                 st.warning(f"No records assigned to {assigned_to} yet.")
#                 conn.close()
#                 return
#         else:
#             query = "SELECT * FROM vendor_data"
#             df = pd.read_sql(query, conn)
#             st.info(f"📊 Total records loaded: {len(df):,}")
            
#             if df.empty:
#                 st.warning("No data found in vendor_data table.")
#                 conn.close()
#                 return
        
#         conn.close()
#     except Exception as e:
#         st.error(f"Database error: {e}")
#         return
    
#     # Initialize session state for filters
#     filter_key = f"insight_filters_{assigned_to}" if assigned_to else "insight_filters"
#     if filter_key not in st.session_state:
#         st.session_state[filter_key] = {}
    
#     # ===============================
#     # 🎯 MULTI-COLUMN FILTERING SYSTEM
#     # ===============================
#     st.sidebar.markdown("### 🎯 Apply Filters (Multi-Column)")
#     st.sidebar.caption("Filter data before analysis. All filters use AND logic.")
    
#     valid_columns = [c for c in df.columns if df[c].dtype in ["object", "int64", "float64"]]
    
#     # --- Text Search Filters ---
#     with st.sidebar.expander("🔤 Text Search", expanded=False):
#         text_cols = st.multiselect(
#             "Select columns to search",
#             options=[c for c in valid_columns if df[c].dtype == 'object'],
#             key=f"insight_text_cols_{assigned_to}"
#         )
        
#         for col in text_cols:
#             search_val = st.text_input(
#                 f"Search {col}",
#                 key=f"insight_search_{col}_{assigned_to}",
#                 placeholder=f"Type keyword..."
#             )
#             if search_val:
#                 st.session_state[filter_key][col] = {'type': 'text', 'value': search_val}
#             elif col in st.session_state[filter_key] and st.session_state[filter_key][col].get('type') == 'text':
#                 del st.session_state[filter_key][col]
    
#     # --- Dropdown Filters ---
#     with st.sidebar.expander("📋 Exact Match (Dropdown)", expanded=True):
#         dropdown_cols = st.multiselect(
#             "Select columns for filtering",
#             options=[c for c in valid_columns if df[c].dtype == 'object' and df[c].nunique() <= 100],
#             key=f"insight_dropdown_cols_{assigned_to}",
#             help="Only columns with ≤100 unique values shown"
#         )
        
#         for col in dropdown_cols:
#             unique_vals = sorted(df[col].astype(str).dropna().unique().tolist())
#             unique_vals = [v for v in unique_vals if str(v).strip() not in ['', 'nan', 'None']]
            
#             selected = st.multiselect(
#                 f"{col}",
#                 options=unique_vals,
#                 key=f"insight_dropdown_{col}_{assigned_to}",
#                 placeholder=f"Select {col}..."
#             )
            
#             if selected:
#                 st.session_state[filter_key][col] = {'type': 'dropdown', 'value': selected}
#             elif col in st.session_state[filter_key] and st.session_state[filter_key][col].get('type') == 'dropdown':
#                 del st.session_state[filter_key][col]
    
#     # --- Numeric Range Filters ---
#     with st.sidebar.expander("🔢 Numeric Range", expanded=False):
#         numeric_cols = st.multiselect(
#             "Select numeric columns",
#             options=[c for c in valid_columns if pd.api.types.is_numeric_dtype(df[c])],
#             key=f"insight_numeric_cols_{assigned_to}"
#         )
        
#         for col in numeric_cols:
#             try:
#                 min_val = float(df[col].min())
#                 max_val = float(df[col].max())
                
#                 range_val = st.slider(
#                     f"{col}",
#                     min_value=min_val,
#                     max_value=max_val,
#                     value=(min_val, max_val),
#                     key=f"insight_range_{col}_{assigned_to}"
#                 )
                
#                 if range_val != (min_val, max_val):
#                     st.session_state[filter_key][col] = {'type': 'range', 'value': range_val}
#                 elif col in st.session_state[filter_key] and st.session_state[filter_key][col].get('type') == 'range':
#                     del st.session_state[filter_key][col]
#             except:
#                 st.warning(f"Could not create range filter for {col}")
    
#     # --- Clear Filters Button ---
#     if st.session_state[filter_key]:
#         st.sidebar.markdown("---")
#         if st.sidebar.button("🧹 Clear All Filters", type="secondary", use_container_width=True, key=f"clear_filters_{assigned_to}"):
#             st.session_state[filter_key] = {}
#             st.rerun()
        
#         st.sidebar.markdown("##### 🎯 Active Filters:")
#         for col, config in st.session_state[filter_key].items():
#             if config['type'] == 'text':
#                 st.sidebar.caption(f"✓ `{col}` contains '{config['value']}'")
#             elif config['type'] == 'dropdown':
#                 st.sidebar.caption(f"✓ `{col}` in {len(config['value'])} values")
#             elif config['type'] == 'range':
#                 st.sidebar.caption(f"✓ `{col}` [{config['value'][0]:.1f} - {config['value'][1]:.1f}]")
    
#     # ===============================
#     # 🔄 APPLY FILTERS TO DATAFRAME
#     # ===============================
#     df_filtered = df.copy()
    
#     for col, filter_config in st.session_state[filter_key].items():
#         filter_type = filter_config['type']
#         filter_value = filter_config['value']
        
#         if filter_type == 'text':
#             mask = df_filtered[col].astype(str).str.contains(filter_value, case=False, na=False)
#             df_filtered = df_filtered[mask]
#         elif filter_type == 'dropdown':
#             mask = df_filtered[col].astype(str).isin(filter_value)
#             df_filtered = df_filtered[mask]
#         elif filter_type == 'range':
#             mask = (df_filtered[col] >= filter_value[0]) & (df_filtered[col] <= filter_value[1])
#             df_filtered = df_filtered[mask]
    
#     if st.session_state[filter_key]:
#         filter_impact = ((len(df) - len(df_filtered)) / len(df) * 100) if len(df) > 0 else 0
#         st.info(f"🎯 **Filters Applied:** {len(st.session_state[filter_key])} | **Showing:** {len(df_filtered):,} / {len(df):,} records ({100-filter_impact:.1f}%)")
    
#     if df_filtered.empty:
#         st.warning("⚠️ No records match the current filters. Try adjusting your criteria.")
#         return
    
#     st.markdown("---")
    
#     # ===============================
#     # 📊 OVERVIEW SUMMARY METRICS
#     # ===============================
#     st.markdown("### 📊 Overview Summary")
    
#     metric_cols = st.columns(5)
    
#     # Calculate key metrics
#     total_leads = len(df_filtered)
    
#     # Email availability
#     email_cols = [c for c in df_filtered.columns if 'email' in c.lower()]
#     leads_with_email = 0
#     if email_cols:
#         for col in email_cols:
#             leads_with_email += df_filtered[col].notna().sum()
#         leads_with_email = min(leads_with_email, total_leads)
    
#     # Unique countries
#     country_cols = [c for c in df_filtered.columns if 'country' in c.lower()]
#     unique_countries = 0
#     if country_cols:
#         unique_countries = df_filtered[country_cols[0]].nunique()
    
#     # Assignment rate
#     assigned_cols = [c for c in df_filtered.columns if 'assigned' in c.lower()]
#     leads_assigned = 0
#     if assigned_cols:
#         leads_assigned = df_filtered[assigned_cols[0]].notna().sum()
    
#     # Conversion/Status check
#     status_cols = [c for c in df_filtered.columns if 'status' in c.lower() or 'stage' in c.lower()]
#     conversion_rate = 0
#     if status_cols:
#         converted = df_filtered[status_cols[0]].astype(str).str.lower().str.contains('convert|won|closed|success', na=False).sum()
#         conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0
    
#     with metric_cols[0]:
#         st.metric("📊 Total Leads", f"{total_leads:,}")
    
#     with metric_cols[1]:
#         email_pct = (leads_with_email / total_leads * 100) if total_leads > 0 else 0
#         st.metric("📧 With Email", f"{leads_with_email:,}", f"{email_pct:.1f}%")
    
#     with metric_cols[2]:
#         st.metric("🌍 Unique Countries", f"{unique_countries:,}")
    
#     with metric_cols[3]:
#         assigned_pct = (leads_assigned / total_leads * 100) if total_leads > 0 else 0
#         st.metric("👤 Assigned", f"{leads_assigned:,}", f"{assigned_pct:.1f}%")
    
#     with metric_cols[4]:
#         st.metric("✅ Conversion Rate", f"{conversion_rate:.1f}%")
    
#     st.markdown("---")
    
#     # ===============================
#     # 🔍 ANALYSIS TYPE SELECTION
#     # ===============================
#     st.markdown("### 🔍 Select Analysis Type")
    
#     analysis_type = st.radio(
#         "Choose analysis:",
#         ["Single Column Distribution", "Cross-Column Analysis", "Trend & Time Analysis"],
#         horizontal=True,
#         key=f"analysis_type_{assigned_to}"
#     )
    
#     st.markdown("---")
    
#     # ===============================
#     # ANALYSIS TYPE 1: SINGLE COLUMN
#     # ===============================
#     if analysis_type == "Single Column Distribution":
#         analysis_cols = st.columns([2, 1, 1])
        
#         with analysis_cols[0]:
#             valid_analysis_cols = [c for c in df_filtered.columns if df_filtered[c].dtype in ["object", "int64", "float64"]]
#             selected_col = st.selectbox(
#                 "Analyze this column:",
#                 options=valid_analysis_cols,
#                 key=f"selected_analysis_col_{assigned_to}"
#             )
        
#         with analysis_cols[1]:
#             top_n = st.slider("Show top N", 5, 50, 15, key=f"top_n_slider_{assigned_to}")
        
#         with analysis_cols[2]:
#             chart_type = st.selectbox("Chart", ["Bar", "Pie", "Both"], key=f"chart_type_{assigned_to}")
        
#         if selected_col:
#             # Clean data
#             df_work = df_filtered.copy()
#             df_work[selected_col] = df_work[selected_col].astype(str).str.strip().str.lower()
#             df_work[selected_col] = df_work[selected_col].replace(["", "nan", "none", "null", "na"], pd.NA)
#             df_clean = df_work[df_work[selected_col].notna()].copy()
            
#             if not df_clean.empty:
#                 col_counts = df_clean[selected_col].value_counts().reset_index()
#                 col_counts.columns = [selected_col, "count"]
#                 total = col_counts["count"].sum()
#                 col_counts["percentage"] = (col_counts["count"] / total * 100).round(2)
#                 col_counts = col_counts.sort_values(by="count", ascending=False).reset_index(drop=True)
                
#                 original_count = len(col_counts)
#                 col_counts_display = col_counts.head(top_n).copy()
                
#                 # Display metrics
#                 metric_cols2 = st.columns(4)
#                 with metric_cols2[0]:
#                     st.metric("📊 Valid Records", f"{total:,}")
#                 with metric_cols2[1]:
#                     st.metric("🔢 Unique Values", original_count)
#                 with metric_cols2[2]:
#                     top_val = str(col_counts.iloc[0][selected_col])[:15]
#                     st.metric("🏆 Top Category", top_val)
#                 with metric_cols2[3]:
#                     top_pct = col_counts.iloc[0]["percentage"]
#                     st.metric("📍 Top %", f"{top_pct:.1f}%")
                
#                 st.markdown("---")
                
#                 # Charts
#                 if chart_type in ["Bar", "Both"]:
#                     fig_bar = px.bar(
#                         col_counts_display,
#                         x=selected_col,
#                         y="count",
#                         text="count",
#                         color="count",
#                         color_continuous_scale="Blues",
#                         title=f"{selected_col.replace('_', ' ').title()} Distribution"
#                     )
#                     fig_bar.update_traces(texttemplate='%{text:,}', textposition='outside')
#                     fig_bar.update_layout(xaxis_tickangle=-45, height=450, showlegend=False)
#                     st.plotly_chart(fig_bar, use_container_width=True)
                
#                 if chart_type in ["Pie", "Both"]:
#                     fig_pie = px.pie(
#                         col_counts_display,
#                         names=selected_col,
#                         values="count",
#                         hole=0.4,
#                         title=f"{selected_col.replace('_', ' ').title()} Composition"
#                     )
#                     fig_pie.update_traces(textposition='auto', textinfo='label+percent')
#                     st.plotly_chart(fig_pie, use_container_width=True)
                
#                 # Data Table
#                 st.markdown("---")
#                 st.markdown(f"### 📋 {selected_col.replace('_', ' ').title()} Distribution Table")
                
#                 display_df = col_counts_display.copy()
#                 display_df["count_formatted"] = display_df["count"].apply(lambda x: f"{x:,}")
#                 display_df["percentage_formatted"] = display_df["percentage"].apply(lambda x: f"{x}%")
                
#                 show_df = display_df[[selected_col, "count_formatted", "percentage_formatted"]].copy()
#                 show_df.columns = [selected_col.replace('_', ' ').title(), "Count", "Percentage"]
                
#                 st.dataframe(
#                     show_df,
#                     use_container_width=True,
#                     hide_index=True,
#                     height=400
#                 )
                
#                 # Download buttons
#                 download_cols = st.columns([1, 1, 2])
                
#                 with download_cols[0]:
#                     csv = col_counts.to_csv(index=False).encode('utf-8')
#                     st.download_button(
#                         label="📥 Download Full Data",
#                         data=csv,
#                         file_name=f"{selected_col}_distribution_full.csv",
#                         mime="text/csv",
#                         use_container_width=True,
#                         key=f"download_full_{assigned_to}"
#                     )
                
#                 with download_cols[1]:
#                     csv_top = col_counts_display.to_csv(index=False).encode('utf-8')
#                     st.download_button(
#                         label=f"📥 Download Top {top_n}",
#                         data=csv_top,
#                         file_name=f"{selected_col}_distribution_top{top_n}.csv",
#                         mime="text/csv",
#                         use_container_width=True,
#                         key=f"download_top_{assigned_to}"
#                     )
                
#                 # Insights
#                 with st.expander("💡 Advanced Insights", expanded=False):
#                     top_3 = col_counts.head(3)
#                     top_3_pct = top_3["percentage"].sum()
                    
#                     st.markdown(f"**🏆 Top 3 Performers:**")
#                     for idx, row in top_3.iterrows():
#                         st.markdown(f"{idx + 1}. **{row[selected_col]}** → {row['count']:,} leads ({row['percentage']:.1f}%)")
                    
#                     st.markdown(f"\n**📊 Distribution Pattern:**")
#                     if top_3_pct > 75:
#                         st.warning(f"⚠️ **High Concentration Alert:** Top 3 represent {top_3_pct:.1f}% - consider diversification")
#                     elif top_3_pct < 30:
#                         st.success(f"✅ **Well Distributed:** Top 3 only {top_3_pct:.1f}% - healthy spread")
#                     else:
#                         st.info(f"📌 **Moderate Concentration:** Top 3 represent {top_3_pct:.1f}%")
                    
#                     # Data quality
#                     missing_pct = ((len(df_filtered) - total) / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
#                     if missing_pct > 10:
#                         st.warning(f"⚠️ **Data Quality Alert:** {missing_pct:.1f}% missing/invalid values in {selected_col}")
#                     elif missing_pct > 0:
#                         st.info(f"ℹ️ Data Completeness: {100-missing_pct:.1f}% ({missing_pct:.1f}% missing)")
#                     else:
#                         st.success(f"✅ Perfect data quality - no missing values")
    
#     # ===============================
#     # ANALYSIS TYPE 2: CROSS-COLUMN
#     # ===============================
#     elif analysis_type == "Cross-Column Analysis":
#         st.markdown("### 🔗 Cross-Column Relationship Analysis")
        
#         cross_cols = st.columns(2)
        
#         with cross_cols[0]:
#             valid_cols = [c for c in df_filtered.columns if df_filtered[c].dtype == 'object']
#             col1 = st.selectbox("Primary Dimension:", options=valid_cols, key=f"cross_col1_{assigned_to}")
        
#         with cross_cols[1]:
#             col2 = st.selectbox("Secondary Dimension:", options=valid_cols, key=f"cross_col2_{assigned_to}")
        
#         if col1 and col2 and col1 != col2:
#             # Create cross-tabulation
#             df_cross = df_filtered[[col1, col2]].copy()
#             df_cross[col1] = df_cross[col1].astype(str).str.strip()
#             df_cross[col2] = df_cross[col2].astype(str).str.strip()
            
#             # Remove invalid values
#             df_cross = df_cross[
#                 (~df_cross[col1].isin(['', 'nan', 'None', 'null'])) &
#                 (~df_cross[col2].isin(['', 'nan', 'None', 'null']))
#             ]
            
#             if not df_cross.empty:
#                 # Create pivot table
#                 pivot = pd.crosstab(df_cross[col1], df_cross[col2], margins=True)
                
#                 # Show top combinations
#                 combo_counts = df_cross.groupby([col1, col2]).size().reset_index(name='count')
#                 combo_counts = combo_counts.sort_values('count', ascending=False).head(20)
#                 combo_counts['percentage'] = (combo_counts['count'] / len(df_cross) * 100).round(2)
                
#                 st.markdown("#### 🏆 Top Combinations")
                
#                 # Create sunburst chart
#                 fig_sunburst = px.sunburst(
#                     combo_counts.head(15),
#                     path=[col1, col2],
#                     values='count',
#                     title=f"{col1} → {col2} Relationship"
#                 )
#                 st.plotly_chart(fig_sunburst, use_container_width=True)
                
#                 # Show table
#                 st.dataframe(combo_counts.head(15), use_container_width=True)
                
#                 # Insights
#                 with st.expander("💡 Cross-Column Insights", expanded=True):
#                     top_combo = combo_counts.iloc[0]
#                     st.markdown(f"**🎯 Dominant Combination:**")
#                     st.success(f"{top_combo[col1]} + {top_combo[col2]} → {top_combo['count']:,} leads ({top_combo['percentage']:.1f}%)")
                    
#                     # Find unique patterns
#                     col1_unique = df_cross[col1].nunique()
#                     col2_unique = df_cross[col2].nunique()
#                     st.markdown(f"\n**📊 Diversity Metrics:**")
#                     st.info(f"• {col1}: {col1_unique} unique values\n• {col2}: {col2_unique} unique values\n• Combinations: {len(combo_counts)} observed")
#         else:
#             st.info("👆 Select two different columns to analyze their relationship")
    
#     # ===============================
#     # ANALYSIS TYPE 3: TREND/TIME
#     # ===============================
#     else:  # Trend & Time Analysis
#         st.markdown("### 📈 Trend & Time-Based Analysis")
        
#         date_cols = [c for c in df_filtered.columns if 'date' in c.lower() or 'time' in c.lower() or 'created' in c.lower()]
        
#         if date_cols:
#             time_col = st.selectbox("Select time column:", options=date_cols, key=f"time_col_{assigned_to}")
            
#             if time_col:
#                 try:
#                     df_time = df_filtered.copy()
#                     df_time[time_col] = pd.to_datetime(df_time[time_col], errors='coerce')
#                     df_time = df_time[df_time[time_col].notna()]
                    
#                     if not df_time.empty:
#                         # Group by period
#                         period = st.radio("Group by:", ["Day", "Week", "Month"], horizontal=True, key=f"period_{assigned_to}")
                        
#                         if period == "Day":
#                             df_time['period'] = df_time[time_col].dt.date
#                         elif period == "Week":
#                             df_time['period'] = df_time[time_col].dt.to_period('W').astype(str)
#                         else:
#                             df_time['period'] = df_time[time_col].dt.to_period('M').astype(str)
                        
#                         trend_data = df_time.groupby('period').size().reset_index(name='count')
#                         trend_data = trend_data.sort_values('period')
                        
#                         # Line chart
#                         fig_trend = px.line(
#                             trend_data,
#                             x='period',
#                             y='count',
#                             markers=True,
#                             title=f"Lead Volume Trend ({period}ly)"
#                         )
#                         fig_trend.update_layout(xaxis_tickangle=-45, height=400)
#                         st.plotly_chart(fig_trend, use_container_width=True)
                        
#                         # Trend insights
#                         with st.expander("💡 Trend Insights", expanded=True):
#                             avg_leads = trend_data['count'].mean()
#                             peak_period = trend_data.loc[trend_data['count'].idxmax(), 'period']
#                             peak_count = trend_data['count'].max()
                            
#                             st.markdown(f"**📊 Trend Analysis:**")
#                             st.info(f"• Average {period}ly leads: {avg_leads:.0f}\n• Peak period: {peak_period} ({peak_count:,} leads)\n• Total periods: {len(trend_data)}")
                            
#                             # Growth rate
#                             if len(trend_data) > 1:
#                                 latest = trend_data.iloc[-1]['count']
#                                 previous = trend_data.iloc[-2]['count']
#                                 growth = ((latest - previous) / previous * 100) if previous > 0 else 0
                                
#                                 if growth > 10:
#                                     st.success(f"📈 Growing: +{growth:.1f}% vs previous {period.lower()}")
#                                 elif growth < -10:
#                                     st.warning(f"📉 Declining: {growth:.1f}% vs previous {period.lower()}")
#                                 else:
#                                     st.info(f"➡️ Stable: {growth:+.1f}% vs previous {period.lower()}")
#                 except:
#                     st.error("Unable to parse dates in selected column")
#         else:
#             st.info("⚠️ No date/time columns found in the data")





def lead_insights_dashboard(assigned_to=None):
    """
    Enhanced Lead Insights Dashboard with multi-dimensional analysis
    
    Args:
        assigned_to (str, optional): Email of user to filter leads by. 
                                     If None, shows all leads (admin view)
    """
    st.title("📊 Lead Insights Dashboard")
    
    # --- Load data from DB ---
    try:
        conn = get_connection()
        if assigned_to:
            query = "SELECT * FROM vendor_data WHERE assigned_to = %s"
            df = pd.read_sql(query, conn, params=[assigned_to])
            st.info(f"📊 Your assigned records: {len(df):,}")
            
            if df.empty:
                st.warning(f"No records assigned to {assigned_to} yet.")
                conn.close()
                return
        else:
            query = "SELECT * FROM vendor_data"
            df = pd.read_sql(query, conn)
            st.info(f"📊 Total records loaded: {len(df):,}")
            
            if df.empty:
                st.warning("No data found in vendor_data table.")
                conn.close()
                return
        
        conn.close()
    except Exception as e:
        st.error(f"Database error: {e}")
        return
    
    # Initialize session state for filters
    filter_key = f"insight_filters_{assigned_to}" if assigned_to else "insight_filters"
    if filter_key not in st.session_state:
        st.session_state[filter_key] = {}
    
    # ===============================
    # 🎯 MULTI-COLUMN FILTERING SYSTEM
    # ===============================
    st.sidebar.markdown("### 🎯 Apply Filters (Multi-Column)")
    st.sidebar.caption("Filter data before analysis. All filters use AND logic.")
    
    valid_columns = [c for c in df.columns if df[c].dtype in ["object", "int64", "float64"]]
    
    # --- Text Search Filters ---
    with st.sidebar.expander("🔤 Text Search", expanded=False):
        text_cols = st.multiselect(
            "Select columns to search",
            options=[c for c in valid_columns if df[c].dtype == 'object'],
            key=f"insight_text_cols_{assigned_to}"
        )
        
        for col in text_cols:
            search_val = st.text_input(
                f"Search {col}",
                key=f"insight_search_{col}_{assigned_to}",
                placeholder=f"Type keyword..."
            )
            if search_val:
                st.session_state[filter_key][col] = {'type': 'text', 'value': search_val}
            elif col in st.session_state[filter_key] and st.session_state[filter_key][col].get('type') == 'text':
                del st.session_state[filter_key][col]
    
    # --- Dropdown Filters ---
    with st.sidebar.expander("📋 Exact Match (Dropdown)", expanded=True):
        dropdown_cols = st.multiselect(
            "Select columns for filtering",
            options=[c for c in valid_columns if df[c].dtype == 'object' and df[c].nunique() <= 100],
            key=f"insight_dropdown_cols_{assigned_to}",
            help="Only columns with ≤100 unique values shown"
        )
        
        for col in dropdown_cols:
            unique_vals = sorted(df[col].astype(str).dropna().unique().tolist())
            unique_vals = [v for v in unique_vals if str(v).strip() not in ['', 'nan', 'None']]
            
            selected = st.multiselect(
                f"{col}",
                options=unique_vals,
                key=f"insight_dropdown_{col}_{assigned_to}",
                placeholder=f"Select {col}..."
            )
            
            if selected:
                st.session_state[filter_key][col] = {'type': 'dropdown', 'value': selected}
            elif col in st.session_state[filter_key] and st.session_state[filter_key][col].get('type') == 'dropdown':
                del st.session_state[filter_key][col]
    
    # --- Numeric Range Filters ---
    with st.sidebar.expander("🔢 Numeric Range", expanded=False):
        numeric_cols = st.multiselect(
            "Select numeric columns",
            options=[c for c in valid_columns if pd.api.types.is_numeric_dtype(df[c])],
            key=f"insight_numeric_cols_{assigned_to}"
        )
        
        for col in numeric_cols:
            try:
                min_val = float(df[col].min())
                max_val = float(df[col].max())
                
                range_val = st.slider(
                    f"{col}",
                    min_value=min_val,
                    max_value=max_val,
                    value=(min_val, max_val),
                    key=f"insight_range_{col}_{assigned_to}"
                )
                
                if range_val != (min_val, max_val):
                    st.session_state[filter_key][col] = {'type': 'range', 'value': range_val}
                elif col in st.session_state[filter_key] and st.session_state[filter_key][col].get('type') == 'range':
                    del st.session_state[filter_key][col]
            except:
                st.warning(f"Could not create range filter for {col}")
    
    # --- Clear Filters Button ---
    if st.session_state[filter_key]:
        st.sidebar.markdown("---")
        if st.sidebar.button("🧹 Clear All Filters", type="secondary", use_container_width=True, key=f"clear_filters_{assigned_to}"):
            st.session_state[filter_key] = {}
            st.rerun()
        
        st.sidebar.markdown("##### 🎯 Active Filters:")
        for col, config in st.session_state[filter_key].items():
            if config['type'] == 'text':
                st.sidebar.caption(f"✓ `{col}` contains '{config['value']}'")
            elif config['type'] == 'dropdown':
                st.sidebar.caption(f"✓ `{col}` in {len(config['value'])} values")
            elif config['type'] == 'range':
                st.sidebar.caption(f"✓ `{col}` [{config['value'][0]:.1f} - {config['value'][1]:.1f}]")
    
    # ===============================
    # 🔄 APPLY FILTERS TO DATAFRAME
    # ===============================
    df_filtered = df.copy()
    
    for col, filter_config in st.session_state[filter_key].items():
        filter_type = filter_config['type']
        filter_value = filter_config['value']
        
        if filter_type == 'text':
            mask = df_filtered[col].astype(str).str.contains(filter_value, case=False, na=False)
            df_filtered = df_filtered[mask]
        elif filter_type == 'dropdown':
            mask = df_filtered[col].astype(str).isin(filter_value)
            df_filtered = df_filtered[mask]
        elif filter_type == 'range':
            mask = (df_filtered[col] >= filter_value[0]) & (df_filtered[col] <= filter_value[1])
            df_filtered = df_filtered[mask]
    
    if st.session_state[filter_key]:
        filter_impact = ((len(df) - len(df_filtered)) / len(df) * 100) if len(df) > 0 else 0
        st.info(f"🎯 **Filters Applied:** {len(st.session_state[filter_key])} | **Showing:** {len(df_filtered):,} / {len(df):,} records ({100-filter_impact:.1f}%)")
    
    if df_filtered.empty:
        st.warning("⚠️ No records match the current filters. Try adjusting your criteria.")
        return
    
    st.markdown("---")
    
    # ===============================
    # 📊 OVERVIEW SUMMARY METRICS
    # ===============================
    st.markdown("### 📊 Overview Summary")
    
    metric_cols = st.columns(5)
    
    # Calculate key metrics
    total_leads = len(df_filtered)
    
    # Email availability
    email_cols = [c for c in df_filtered.columns if 'email' in c.lower()]
    leads_with_email = 0
    if email_cols:
        for col in email_cols:
            leads_with_email += df_filtered[col].notna().sum()
        leads_with_email = min(leads_with_email, total_leads)
    
    # Unique countries
    country_cols = [c for c in df_filtered.columns if 'country' in c.lower()]
    unique_countries = 0
    if country_cols:
        unique_countries = df_filtered[country_cols[0]].nunique()
    
    # Assignment rate
    assigned_cols = [c for c in df_filtered.columns if 'assigned' in c.lower()]
    leads_assigned = 0
    if assigned_cols:
        leads_assigned = df_filtered[assigned_cols[0]].notna().sum()
    
    # Conversion/Status check
    status_cols = [c for c in df_filtered.columns if 'status' in c.lower() or 'stage' in c.lower()]
    conversion_rate = 0
    if status_cols:
        converted = df_filtered[status_cols[0]].astype(str).str.lower().str.contains('convert|won|closed|success', na=False).sum()
        conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0
    
    with metric_cols[0]:
        st.metric("📊 Total Leads", f"{total_leads:,}")
    
    with metric_cols[1]:
        email_pct = (leads_with_email / total_leads * 100) if total_leads > 0 else 0
        st.metric("📧 With Email", f"{leads_with_email:,}", f"{email_pct:.1f}%")
    
    with metric_cols[2]:
        st.metric("🌍 Unique Countries", f"{unique_countries:,}")
    
    with metric_cols[3]:
        assigned_pct = (leads_assigned / total_leads * 100) if total_leads > 0 else 0
        st.metric("👤 Assigned", f"{leads_assigned:,}", f"{assigned_pct:.1f}%")
    
    with metric_cols[4]:
        st.metric("✅ Conversion Rate", f"{conversion_rate:.1f}%")
    
    st.markdown("---")
    
    # ===============================
    # 🔍 ANALYSIS TYPE SELECTION
    # ===============================
    st.markdown("### 🔍 Select Analysis Type")
    
    analysis_type = st.radio(
        "Choose analysis:",
        ["Single Column Distribution", "Cross-Column Analysis", "Trend & Time Analysis"],
        horizontal=True,
        key=f"analysis_type_{assigned_to}"
    )
    
    st.markdown("---")
    
    # ===============================
    # ANALYSIS TYPE 1: SINGLE COLUMN
    # ===============================
    if analysis_type == "Single Column Distribution":
        analysis_cols = st.columns([2, 1, 1])
        
        with analysis_cols[0]:
            valid_analysis_cols = [c for c in df_filtered.columns if df_filtered[c].dtype in ["object", "int64", "float64"]]
            selected_col = st.selectbox(
                "Analyze this column:",
                options=valid_analysis_cols,
                key=f"selected_analysis_col_{assigned_to}"
            )
        
        with analysis_cols[1]:
            top_n = st.slider("Show top N", 5, 50, 15, key=f"top_n_slider_{assigned_to}")
        
        if selected_col:
            # Clean data
            df_work = df_filtered.copy()
            df_work[selected_col] = df_work[selected_col].astype(str).str.strip().str.lower()
            df_work[selected_col] = df_work[selected_col].replace(["", "nan", "none", "null", "na"], pd.NA)
            df_clean = df_work[df_work[selected_col].notna()].copy()
            
            if not df_clean.empty:
                col_counts = df_clean[selected_col].value_counts().reset_index()
                col_counts.columns = [selected_col, "count"]
                total = col_counts["count"].sum()
                col_counts["percentage"] = (col_counts["count"] / total * 100).round(2)
                col_counts = col_counts.sort_values(by="count", ascending=False).reset_index(drop=True)
                
                original_count = len(col_counts)
                col_counts_display = col_counts.head(top_n).copy()
                
                # Display metrics
                metric_cols2 = st.columns(4)
                with metric_cols2[0]:
                    st.metric("📊 Valid Records", f"{total:,}")
                with metric_cols2[1]:
                    st.metric("🔢 Unique Values", original_count)
                with metric_cols2[2]:
                    top_val = str(col_counts.iloc[0][selected_col])[:15]
                    st.metric("🏆 Top Category", top_val)
                with metric_cols2[3]:
                    top_pct = col_counts.iloc[0]["percentage"]
                    st.metric("📍 Top %", f"{top_pct:.1f}%")
                
                st.markdown("---")
                
                # Data Table
                st.markdown("---")
                st.markdown(f"### 📋 {selected_col.replace('_', ' ').title()} Distribution Table")
                
                display_df = col_counts_display.copy()
                display_df["count_formatted"] = display_df["count"].apply(lambda x: f"{x:,}")
                display_df["percentage_formatted"] = display_df["percentage"].apply(lambda x: f"{x}%")
                
                show_df = display_df[[selected_col, "count_formatted", "percentage_formatted"]].copy()
                show_df.columns = [selected_col.replace('_', ' ').title(), "Count", "Percentage"]
                
                st.dataframe(
                    show_df,
                    use_container_width=True,
                    hide_index=True,
                    height=400
                )
                
                # Download buttons
                download_cols = st.columns([1, 1, 2])
                
                with download_cols[0]:
                    csv = col_counts.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Full Data",
                        data=csv,
                        file_name=f"{selected_col}_distribution_full.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key=f"download_full_{assigned_to}"
                    )
                
                with download_cols[1]:
                    csv_top = col_counts_display.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=f"📥 Download Top {top_n}",
                        data=csv_top,
                        file_name=f"{selected_col}_distribution_top{top_n}.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key=f"download_top_{assigned_to}"
                    )
                
                # Insights
                with st.expander("💡 Advanced Insights", expanded=False):
                    top_3 = col_counts.head(3)
                    top_3_pct = top_3["percentage"].sum()
                    
                    st.markdown(f"**🏆 Top 3 Performers:**")
                    for idx, row in top_3.iterrows():
                        st.markdown(f"{idx + 1}. **{row[selected_col]}** → {row['count']:,} leads ({row['percentage']:.1f}%)")
                    
                    st.markdown(f"\n**📊 Distribution Pattern:**")
                    if top_3_pct > 75:
                        st.warning(f"⚠️ **High Concentration Alert:** Top 3 represent {top_3_pct:.1f}% - consider diversification")
                    elif top_3_pct < 30:
                        st.success(f"✅ **Well Distributed:** Top 3 only {top_3_pct:.1f}% - healthy spread")
                    else:
                        st.info(f"📌 **Moderate Concentration:** Top 3 represent {top_3_pct:.1f}%")
                    
                    # Data quality
                    missing_pct = ((len(df_filtered) - total) / len(df_filtered) * 100) if len(df_filtered) > 0 else 0
                    if missing_pct > 10:
                        st.warning(f"⚠️ **Data Quality Alert:** {missing_pct:.1f}% missing/invalid values in {selected_col}")
                    elif missing_pct > 0:
                        st.info(f"ℹ️ Data Completeness: {100-missing_pct:.1f}% ({missing_pct:.1f}% missing)")
                    else:
                        st.success(f"✅ Perfect data quality - no missing values")
    
    # ===============================
    # ANALYSIS TYPE 2: CROSS-COLUMN
    # ===============================
    elif analysis_type == "Cross-Column Analysis":
        st.markdown("### 🔗 Cross-Column Relationship Analysis")
        
        cross_cols = st.columns(2)
        
        with cross_cols[0]:
            valid_cols = [c for c in df_filtered.columns if df_filtered[c].dtype == 'object']
            col1 = st.selectbox("Primary Dimension:", options=valid_cols, key=f"cross_col1_{assigned_to}")
        
        with cross_cols[1]:
            col2 = st.selectbox("Secondary Dimension:", options=valid_cols, key=f"cross_col2_{assigned_to}")
        
        if col1 and col2 and col1 != col2:
            # Create cross-tabulation
            df_cross = df_filtered[[col1, col2]].copy()
            df_cross[col1] = df_cross[col1].astype(str).str.strip()
            df_cross[col2] = df_cross[col2].astype(str).str.strip()
            
            # Remove invalid values
            df_cross = df_cross[
                (~df_cross[col1].isin(['', 'nan', 'None', 'null'])) &
                (~df_cross[col2].isin(['', 'nan', 'None', 'null']))
            ]
            
            if not df_cross.empty:
                # Create pivot table
                pivot = pd.crosstab(df_cross[col1], df_cross[col2], margins=True)
                
                # Show top combinations
                combo_counts = df_cross.groupby([col1, col2]).size().reset_index(name='count')
                combo_counts = combo_counts.sort_values('count', ascending=False).head(20)
                combo_counts['percentage'] = (combo_counts['count'] / len(df_cross) * 100).round(2)
                
                st.markdown("#### 🏆 Top Combinations")
                
                # Show table
                st.dataframe(combo_counts.head(15), use_container_width=True)
                
                # Insights
                with st.expander("💡 Cross-Column Insights", expanded=True):
                    top_combo = combo_counts.iloc[0]
                    st.markdown(f"**🎯 Dominant Combination:**")
                    st.success(f"{top_combo[col1]} + {top_combo[col2]} → {top_combo['count']:,} leads ({top_combo['percentage']:.1f}%)")
                    
                    # Find unique patterns
                    col1_unique = df_cross[col1].nunique()
                    col2_unique = df_cross[col2].nunique()
                    st.markdown(f"\n**📊 Diversity Metrics:**")
                    st.info(f"• {col1}: {col1_unique} unique values\n• {col2}: {col2_unique} unique values\n• Combinations: {len(combo_counts)} observed")
        else:
            st.info("👆 Select two different columns to analyze their relationship")
    
    # ===============================
    # ANALYSIS TYPE 3: TREND/TIME
    # ===============================
    else:  # Trend & Time Analysis
        st.markdown("### 📈 Trend & Time-Based Analysis")
        
        date_cols = [c for c in df_filtered.columns if 'date' in c.lower() or 'time' in c.lower() or 'created' in c.lower()]
        
        if date_cols:
            time_col = st.selectbox("Select time column:", options=date_cols, key=f"time_col_{assigned_to}")
            
            if time_col:
                try:
                    df_time = df_filtered.copy()
                    df_time[time_col] = pd.to_datetime(df_time[time_col], errors='coerce')
                    df_time = df_time[df_time[time_col].notna()]
                    
                    if not df_time.empty:
                        # Group by period
                        period = st.radio("Group by:", ["Day", "Week", "Month"], horizontal=True, key=f"period_{assigned_to}")
                        
                        if period == "Day":
                            df_time['period'] = df_time[time_col].dt.date
                        elif period == "Week":
                            df_time['period'] = df_time[time_col].dt.to_period('W').astype(str)
                        else:
                            df_time['period'] = df_time[time_col].dt.to_period('M').astype(str)
                        
                        trend_data = df_time.groupby('period').size().reset_index(name='count')
                        trend_data = trend_data.sort_values('period')
                        
                        # Show trend table
                        st.markdown("#### 📊 Lead Volume by Period")
                        st.dataframe(trend_data, use_container_width=True, hide_index=True)
                        
                        # Trend insights
                        with st.expander("💡 Trend Insights", expanded=True):
                            avg_leads = trend_data['count'].mean()
                            peak_period = trend_data.loc[trend_data['count'].idxmax(), 'period']
                            peak_count = trend_data['count'].max()
                            
                            st.markdown(f"**📊 Trend Analysis:**")
                            st.info(f"• Average {period}ly leads: {avg_leads:.0f}\n• Peak period: {peak_period} ({peak_count:,} leads)\n• Total periods: {len(trend_data)}")
                            
                            # Growth rate
                            if len(trend_data) > 1:
                                latest = trend_data.iloc[-1]['count']
                                previous = trend_data.iloc[-2]['count']
                                growth = ((latest - previous) / previous * 100) if previous > 0 else 0
                                
                                if growth > 10:
                                    st.success(f"📈 Growing: +{growth:.1f}% vs previous {period.lower()}")
                                elif growth < -10:
                                    st.warning(f"📉 Declining: {growth:.1f}% vs previous {period.lower()}")
                                else:
                                    st.info(f"➡️ Stable: {growth:+.1f}% vs previous {period.lower()}")
                except:
                    st.error("Unable to parse dates in selected column")
        else:
            st.info("⚠️ No date/time columns found in the data")