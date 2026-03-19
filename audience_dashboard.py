import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import segment_public_api
from segment_public_api.models.update_audience_for_space_input import UpdateAudienceForSpaceInput
from segment_public_api.rest import ApiException
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Segment Audience Dashboard Customer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    h1 {
        color: #1f2937;
    }
    #MainMenu {visibility: hidden;}
    .stAppDeployButton {display: none;}
    a[href="https://github.com/streamlit/streamlit"] {display: none;}
    [data-testid="stToolbarActionButtonLabel"] {display: none;}
    button:has([data-testid="stToolbarActionButtonLabel"]) {display: none !important;}
    [data-testid="stToolbarActionButtonIcon"] {display: none !important;}
    button:has([data-testid="stToolbarActionButtonIcon"]) {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# Sidebar for configuration
st.sidebar.title("🔧 Configuration")
bearer_token = st.sidebar.text_input("Bearer Token", type="password", value="")
space_id = st.sidebar.text_input("Space ID", value="")
page_count = st.sidebar.slider("Results per page", min_value=5, max_value=50, value=10)

# Function to
# 
# 
# 
# 
# 
# 
# 
# 
# 
# 
# 
# 
# 
#   fetch audience data
@st.cache_data(ttl=300)
def fetch_audiences(token, space_id, count=10):
    """Fetch audience data from Segment API"""
    try:
        configuration = segment_public_api.Configuration(access_token=token)

        with segment_public_api.ApiClient(configuration) as api_client:
            api_instance = segment_public_api.AudiencesApi(api_client)
            pagination = segment_public_api.ListAudiencesPaginationInput(count=count)

            api_response = api_instance.list_audiences(space_id, pagination=pagination)
            audiences = api_response.data.audiences

            # Get total count from pagination
            total_count = api_response.data.pagination.total_entries if api_response.data.pagination else len(audiences)

            # Convert to list of dictionaries
            data = []
            for audience in audiences:
                data.append({
                    'id': audience.id,
                    'space_id': audience.space_id,
                    'name': audience.name,
                    'description': audience.description,
                    'key': audience.key,
                    'enabled': audience.enabled,
                    'query': audience.definition.query,
                    'target_entity': getattr(audience.definition, 'target_entity', 'N/A'),
                    'status': audience.status,
                    'size_count': getattr(audience.size, 'count', 0) if hasattr(audience, 'size') else 0,
                    'size_type': getattr(audience.size, 'type', 'N/A') if hasattr(audience, 'size') else 'N/A',
                    'audience_type': getattr(audience, 'audience_type', 'N/A'),
                    'compute_cadence': getattr(audience.compute_cadence, 'type', 'N/A') if hasattr(audience, 'compute_cadence') else 'N/A',
                    'created_by': audience.created_by,
                    'updated_by': audience.updated_by,
                    'created_at': audience.created_at,
                    'updated_at': audience.updated_at,
                    'include_historical_data': audience.options.include_historical_data,
                    'filter_by_external_ids': ', '.join(getattr(audience.options, 'filter_by_external_ids', [])) if hasattr(audience.options, 'filter_by_external_ids') and getattr(audience.options, 'filter_by_external_ids', None) else 'N/A'
                })

            return pd.DataFrame(data), total_count
    except ApiException as e:
        st.error(f"Error fetching audiences: {e}")
        return pd.DataFrame(), 0
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        return pd.DataFrame(), 0


def update_audience_enabled(token, space_id, audience_id, enabled):
    """Enable or disable an audience via the Segment API"""
    try:
        configuration = segment_public_api.Configuration(access_token=token)
        with segment_public_api.ApiClient(configuration) as api_client:
            api_instance = segment_public_api.AudiencesApi(api_client)
            update_input = UpdateAudienceForSpaceInput(enabled=enabled)
            api_response = api_instance.update_audience_for_space(space_id, audience_id, update_input)
            return True, api_response
    except ApiException as e:
        return False, str(e)
    except Exception as e:
        return False, str(e)


# Main app
st.title("📊 Segment Audience Dashboard")
st.markdown("**Real-time analytics and insights for your Segment audiences**")

# Check if credentials are provided
if not bearer_token or not space_id:
    st.warning("⚠️ Please enter your Bearer Token and Space ID in the sidebar to get started.")
    st.info("""
    ### How to get started:
    1. Enter your Segment **Bearer Token** in the sidebar
    2. Enter your **Space ID**
    3. Adjust the number of results if needed
    4. Click outside the input field to load the data
    """)
    st.stop()

# Fetch data
with st.spinner("🔄 Fetching audience data..."):
    df, total_count = fetch_audiences(bearer_token, space_id, page_count)

if df.empty:
    st.error("❌ No data available. Please check your credentials and try again.")
    st.stop()

# Show info about loaded data
if len(df) < total_count:
    st.info(f"📊 Showing {len(df)} of {total_count} audiences (adjust 'Results per page' in sidebar to load more)")

# Key Metrics Section
st.markdown("---")
st.subheader("📈 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Audiences",
        value=total_count
    )

with col2:
    enabled_count = df['enabled'].sum()
    st.metric(
        label="Enabled Audiences",
        value=enabled_count
    )

with col3:
    live_count = (df['status'] == 'Live').sum()
    st.metric(
        label="Live Audiences",
        value=live_count
    )

with col4:
    total_users = df['size_count'].sum()
    st.metric(
        label="Total Users",
        value=f"{total_users:,}"
    )

# Second row of metrics
col5, col6, col7, col8 = st.columns(4)

with col5:
    historical_count = df['include_historical_data'].sum()
    st.metric(
        label="With Historical Data",
        value=historical_count
    )

with col6:
    linked_count = (df['audience_type'] == 'LINKED').sum()
    st.metric(
        label="Linked Audiences",
        value=linked_count
    )

with col7:
    batch_count = (df['compute_cadence'] == 'BATCH').sum()
    st.metric(
        label="Batch Compute",
        value=batch_count
    )

with col8:
    avg_size = df['size_count'].mean()
    st.metric(
        label="Avg Audience Size",
        value=f"{avg_size:,.0f}"
    )

# Visualizations
st.markdown("---")
st.subheader("📊 Visualizations")

# Create two columns for charts
col1, col2 = st.columns(2)

with col1:
    # Status distribution pie chart
    status_counts = df['status'].value_counts()
    fig_status = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title="Audience Status Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3,
        hole=0.4
    )
    fig_status.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_status, use_container_width=True)

with col2:
    # Enabled vs Disabled bar chart
    enabled_counts = df['enabled'].value_counts()
    fig_enabled = px.bar(
        x=['Enabled', 'Disabled'],
        y=[enabled_counts.get(True, 0), enabled_counts.get(False, 0)],
        title="Enabled vs Disabled Audiences",
        color=['Enabled', 'Disabled'],
        color_discrete_map={'Enabled': '#10b981', 'Disabled': '#ef4444'},
        labels={'x': 'Status', 'y': 'Count'}
    )
    fig_enabled.update_layout(showlegend=False)
    st.plotly_chart(fig_enabled, use_container_width=True)

# Additional visualizations
col3, col4 = st.columns(2)

with col3:
    # Historical vs Non-historical data
    hist_counts = df['include_historical_data'].value_counts()
    fig_hist = go.Figure(data=[
        go.Bar(
            x=['With Historical Data', 'Without Historical Data'],
            y=[hist_counts.get(True, 0), hist_counts.get(False, 0)],
            marker_color=['#3b82f6', '#94a3b8']
        )
    ])
    fig_hist.update_layout(
        title="Historical Data Inclusion",
        yaxis_title="Count",
        showlegend=False
    )
    st.plotly_chart(fig_hist, use_container_width=True)

with col4:
    # Audience type distribution
    type_counts = df['audience_type'].value_counts()
    fig_type = px.pie(
        values=type_counts.values,
        names=type_counts.index,
        title="Audience Type Distribution",
        color_discrete_sequence=['#8b5cf6', '#d1d5db'],
        hole=0.4
    )
    st.plotly_chart(fig_type, use_container_width=True)

# Audience Size Visualizations
st.markdown("### 👥 Audience Size Analysis")

col5, col6 = st.columns(2)

with col5:
    # Top 10 audiences by size
    top_audiences = df.nlargest(10, 'size_count')[['name', 'size_count']]
    fig_top = px.bar(
        top_audiences,
        x='size_count',
        y='name',
        orientation='h',
        title="Top 10 Audiences by Size",
        labels={'size_count': 'User Count', 'name': 'Audience'},
        color='size_count',
        color_continuous_scale='Blues'
    )
    fig_top.update_layout(showlegend=False, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_top, use_container_width=True)

with col6:
    # Compute cadence distribution
    cadence_counts = df['compute_cadence'].value_counts()
    fig_cadence = px.bar(
        x=cadence_counts.index,
        y=cadence_counts.values,
        title="Compute Cadence Distribution",
        labels={'x': 'Cadence Type', 'y': 'Count'},
        color=cadence_counts.index,
        color_discrete_sequence=['#06b6d4', '#8b5cf6']
    )
    fig_cadence.update_layout(showlegend=False)
    st.plotly_chart(fig_cadence, use_container_width=True)

# Detailed Data Table
st.markdown("---")
st.subheader("📋 Audience Details")

# Add search and filter options
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    search_term = st.text_input("🔍 Search audiences", placeholder="Search by name, description, or query...")

with col2:
    status_filter = st.multiselect("Filter by Status", options=df['status'].unique(), default=df['status'].unique())

with col3:
    enabled_filter = st.selectbox("Filter by Enabled", options=['All', 'Enabled', 'Disabled'])

# Column selector
st.markdown("#### 📊 Customize Table Columns")
all_columns = ['name', 'key', 'status', 'enabled', 'size_count', 'size_type', 'audience_type',
               'compute_cadence', 'target_entity', 'query', 'description', 'created_at',
               'updated_at', 'created_by', 'updated_by', 'include_historical_data', 'filter_by_external_ids']

default_columns = ['name', 'status', 'enabled', 'size_count', 'audience_type', 'compute_cadence', 'created_at', 'updated_at']

selected_columns = st.multiselect(
    "Select columns to display:",
    options=all_columns,
    default=default_columns,
    help="Choose which fields you want to see in the table below"
)

# Apply filters
filtered_df = df.copy()

if search_term:
    mask = (
        filtered_df['name'].str.contains(search_term, case=False, na=False) |
        filtered_df['description'].str.contains(search_term, case=False, na=False) |
        filtered_df['query'].str.contains(search_term, case=False, na=False)
    )
    filtered_df = filtered_df[mask]

filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]

if enabled_filter == 'Enabled':
    filtered_df = filtered_df[filtered_df['enabled'] == True]
elif enabled_filter == 'Disabled':
    filtered_df = filtered_df[filtered_df['enabled'] == False]

# Display filtered count
st.info(f"Showing {len(filtered_df)} of {len(df)} audiences")

# Display table with selected columns
if selected_columns:
    # Reset index for reliable change detection
    display_df = filtered_df[selected_columns].reset_index(drop=True)
    original_enabled = filtered_df['enabled'].reset_index(drop=True)
    original_ids = filtered_df['id'].reset_index(drop=True)
    original_names = filtered_df['name'].reset_index(drop=True)

    col_config = {}
    if 'enabled' in selected_columns:
        col_config['enabled'] = st.column_config.CheckboxColumn(
            'Enabled',
            help='Check to enable, uncheck to disable audience',
        )
    if 'status' in selected_columns:
        col_config['status'] = st.column_config.TextColumn('Status')

    disabled_cols = [col for col in selected_columns if col != 'enabled']

    edited_df = st.data_editor(
        display_df,
        column_config=col_config,
        disabled=disabled_cols,
        use_container_width=True,
        height=400,
        key='audience_editor'
    )

    # Detect and apply changes to the 'enabled' column
    if 'enabled' in selected_columns:
        changed_mask = edited_df['enabled'] != original_enabled
        changed_rows = edited_df[changed_mask]

        if not changed_rows.empty:
            for idx in changed_rows.index:
                audience_id = original_ids[idx]
                audience_name = original_names[idx]
                new_enabled = bool(changed_rows.loc[idx, 'enabled'])
                action = 'Enabling' if new_enabled else 'Disabling'

                with st.spinner(f"{action} '{audience_name}'..."):
                    success, result = update_audience_enabled(
                        bearer_token, space_id, audience_id, new_enabled
                    )

                if success:
                    status_text = 'enabled' if new_enabled else 'disabled'
                    st.success(f"✅ Successfully {status_text} audience: **{audience_name}**")
                    fetch_audiences.clear()
                    st.rerun()
                else:
                    st.error(f"❌ Failed to update '{audience_name}': {result}")
else:
    st.warning("⚠️ Please select at least one column to display.")

# Expandable detailed view
st.markdown("---")
st.subheader("🔍 Detailed Audience View")

audience_names = filtered_df['name'].tolist()

# Preserve selection across reruns (e.g. after enable/disable triggers st.rerun())
if 'detail_view_audience' not in st.session_state:
    st.session_state.detail_view_audience = audience_names[0] if audience_names else None

default_idx = 0
if st.session_state.detail_view_audience in audience_names:
    default_idx = audience_names.index(st.session_state.detail_view_audience)

selected_audience = st.selectbox(
    "Select an audience to view details",
    options=audience_names,
    index=default_idx,
    key='detail_audience_selectbox'
)
st.session_state.detail_view_audience = selected_audience

if selected_audience:
    audience_data = filtered_df[filtered_df['name'] == selected_audience].iloc[0]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Basic Information**")
        st.write(f"**ID:** {audience_data['id']}")
        st.write(f"**Name:** {audience_data['name']}")
        st.write(f"**Key:** {audience_data['key']}")
        st.write(f"**Description:** {audience_data['description'] or 'N/A'}")
        st.write(f"**Status:** {audience_data['status']}")
        st.write(f"**Enabled:** {'✅ Yes' if audience_data['enabled'] else '❌ No'}")
        st.write(f"**Created At:** {audience_data['created_at']}")
        st.write(f"**Updated At:** {audience_data['updated_at']}")

    with col2:
        st.markdown("**Audience Configuration**")
        st.write(f"**Size:** {audience_data['size_count']:,} {audience_data['size_type']}")
        st.write(f"**Audience Type:** {audience_data['audience_type']}")
        st.write(f"**Compute Cadence:** {audience_data['compute_cadence']}")
        st.write(f"**Target Entity:** {audience_data['target_entity']}")
        st.write(f"**Historical Data:** {'✅ Yes' if audience_data['include_historical_data'] else '❌ No'}")
        st.write(f"**Created By:** {audience_data['created_by']}")
        st.write(f"**Updated By:** {audience_data['updated_by'] or 'N/A'}")

    with col3:
        st.markdown("**Query & Filters**")
        st.text_area("Query Definition", audience_data['query'], height=150, disabled=True, key=f"query_{selected_audience}")
        st.write(f"**Filter by External IDs:**")
        st.write(audience_data['filter_by_external_ids'])

# Download button
st.markdown("---")
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Full Data as CSV",
    data=csv,
    file_name=f"segment_audiences_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv"
)

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #6b7280; padding: 20px;'>
        <p>Built with Streamlit 🎈 | Powered by Segment API</p>
    </div>
""", unsafe_allow_html=True)