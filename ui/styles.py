"""Custom CSS and Styling for the application."""

import streamlit as st


def load_css():
    """Inject custom CSS into Streamlit application."""
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

        :root {
            --primary: #2563EB;
            --primary-hover: #1D4ED8;
            --secondary: #64748B;
            --background: #FFFFFF;
            --surface: #FFFFFF;
            --text-main: #1E293B;
            --text-muted: #64748B;
            --glass-bg: rgba(255, 255, 255, 0.7);
            --glass-border: 1px solid rgba(255, 255, 255, 0.5);
            --glass-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            --radius-lg: 16px;
            --radius-md: 12px;
            --radius-sm: 8px;
        }

        .stApp {
            background-color: var(--background);
            font-family: 'Inter', sans-serif;
            color: var(--text-main);
            font-size: 0.9rem !important;
        }
        
        h1 { font-size: 2.5rem !important; font-weight: 800 !important; }
        h2 { font-size: 2rem !important; font-weight: 700 !important; }
        h3 { font-size: 1.5rem !important; font-weight: 600 !important; }
        h4 { font-size: 1.25rem !important; font-weight: 600 !important; }
        
        h1, h2, h3, h4 {
            font-family: 'Outfit', sans-serif !important;
            color: var(--text-main);
            margin-bottom: 0.5rem !important;
        }
        
        p, li { font-size: 0.9rem !important; line-height: 1.6 !important; }
        
        .stCaption, small, .small-text, [data-testid="stCaptionContainer"] {
            font-size: 0.8rem !important;
            color: var(--text-muted) !important;
        }

        [data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] span {
            font-size: 0.875rem !important;
        }

        [data-testid="stSidebar"] h3 {
            font-size: 1rem !important;
            font-weight: 700 !important;
            padding-top: 13px !important;
            padding-bottom: 5px !important;
            margin-top: 5px !important;
            margin-bottom: 1px !important;
            line-height: 1.3;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748B !important;
        }

        [data-testid="stSidebar"] .sidebar-logo-icon {
            font-size: 8.5rem !important;
            margin-bottom: -15px !important;
            line-height: 1 !important;
            display: block !important;
            color: #1E293B !important;
        }

        [data-testid="stSidebar"] .stRadio label p { font-size: 0.95rem !important; }
        [data-testid="stSidebar"] .stRadio > div { gap: 0.1rem !important; margin-bottom: 13px !important; }
        
        [data-testid="stSidebar"] .stTextInput,
        [data-testid="stSidebar"] .stSelectbox,
        [data-testid="stSidebar"] .stTextArea { margin-bottom: 8px !important; }
        
        [data-testid="stSidebar"] .stButton { margin-top: 3px !important; margin-bottom: 8px !important; }
        
        [data-testid="stSidebar"] .st-emotion-cache-1gulkj5,
        [data-testid="stSidebar"] details { margin-top: 8px !important; margin-bottom: 8px !important; }
        
        [data-testid="stSidebar"] > div > div > div { margin-bottom: 13px !important; }
        
        .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            font-size: 0.9rem !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        div.stButton > button {
            font-size: 0.9rem !important;
            padding: 0.7rem 1.3rem !important;
        }

        [data-testid="stMainBlockContainer"] {
            max-width: 1100px;
            margin: 0 auto;
            padding-top: 2rem;
        }

        .glass-card {
            background: var(--surface);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid #E2E8F0;
            border-radius: var(--radius-lg);
            padding: 30px;
            box-shadow: var(--glass-shadow);
            margin-bottom: 24px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .empty-state-box {
            border: 2px dashed #CBD5E1;
            border-radius: var(--radius-lg);
            background-color: #F1F5F9;
            padding: 40px;
            text-align: center;
            color: var(--text-muted);
            margin: 20px 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        div.stButton > button {
            background-color: var(--primary);
            color: white;
            border-radius: var(--radius-sm);
            font-weight: 500;
            border: none;
            padding: 0.6rem 1.2rem;
            transition: all 0.2s ease;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
            font-family: 'Outfit', sans-serif;
        }
        
        div.stButton > button:hover {
            background-color: var(--primary-hover);
            transform: translateY(-2px);
            box-shadow: 0 6px 10px -1px rgba(37, 99, 235, 0.3);
        }

        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #EEF2FF;
        }

        div[data-testid="stSidebarNav"] { display: none; }

        .step-card {
            background: #F8FAFC;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
            border-left: 3px solid var(--primary);
        }
        
        .stTextArea textarea {
            border-radius: var(--radius-md);
            border: 1px solid #CBD5E1;
            padding: 12px;
            font-family: 'Inter', sans-serif;
            background: #FFFFFF;
        }

        .stTextArea textarea:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.1);
        }
        
        .footer {
            text-align: center;
            padding: 40px 0;
            color: #94A3B8;
            font-size: 0.85rem;
            margin-top: 40px;
            border-top: 1px solid #F1F5F9;
        }

        .glass-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 0.95rem;
        }
        .glass-table th {
            text-align: left;
            padding: 12px 16px;
            border-bottom: 2px solid #E2E8F0;
            color: #64748B;
            font-weight: 600;
            font-family: 'Outfit', sans-serif;
        }
        .glass-table td {
            padding: 12px 16px;
            border-bottom: 1px solid #F1F5F9;
            color: #334155;
            vertical-align: middle;
        }
        .glass-table tr:last-child td { border-bottom: none; }
        .glass-table tr:hover { background-color: rgba(248, 250, 252, 0.6); }
        
        .badge-pos { background: #DCFCE7; color: #166534; padding: 4px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 500; }
        .badge-neg { background: #FEE2E2; color: #991B1B; padding: 4px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 500; }
        .badge-neu { background: #F1F5F9; color: #475569; padding: 4px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 500; }

        [data-testid="stMetricLabel"] {
            margin-bottom: 0.5rem !important;
            font-size: 1rem !important;
            color: var(--text-muted);
        }
        
        [data-testid="stMetricValue"] { padding-top: 5px !important; }
        
        .confidence-value {
            font-size: 2.5rem !important;
            font-weight: 700 !important;
            color: #1E293B !important;
            display: block !important;
            line-height: 1 !important;
        }
        
        .confidence-label {
            font-size: 0.9rem !important;
            color: #64748B !important;
            display: block !important;
        }
        
        .subtitle-text {
            color: #64748B !important;
            font-size: 1rem !important;
            margin-top: -20px !important;
            display: block !important;
            line-height: 1.2 !important;
        }
        
        .mode-caption {
            color: #64748B !important;
            font-size: 0.8rem !important;
            margin-top: -15px !important;
            margin-bottom: 10px !important;
        }
        
        /* Consistent spacing for all sidebar sections */
        [data-testid="stSidebar"] .stExpander > div > div > div {
            margin-top: -10px !important;
        }
        
        [data-testid="stSidebar"] .stSelectbox > div > div {
            margin-top: -8px !important;
        }
        
        [data-testid="stSidebar"] .stCheckbox {
            margin-top: -8px !important;
        }
        
        [data-testid="stSidebar"] .stInfo {
            margin-top: -8px !important;
            margin-bottom: 8px !important;
        }
        
        .section-label {
            margin-top: -10px !important;
            margin-bottom: 5px !important;
            font-weight: 600 !important;
            color: #374151 !important;
        }
        
        /* Reduce spacing around dividers */
        [data-testid="stSidebar"] .stDivider {
            margin-top: 8px !important;
            margin-bottom: 8px !important;
        }
        
        [data-testid="stSidebar"] hr {
            margin-top: 8px !important;
            margin-bottom: 8px !important;
        }
        
        [data-testid="stSidebar"] .sidebar-subtitle {
            color: #64748B !important;
            margin-top: -17px !important;
            font-size: 1.26rem !important;
            display: block !important;
            line-height: 1.2 !important;
            font-weight: 400 !important;
        }

        /* Feedback Section Styles */
        .feedback-btn {
            padding: 8px 16px !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }
        
        .feedback-btn:hover {
            transform: scale(1.02) !important;
        }
        
        /* Admin Panel Styles */
        .admin-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border: 1px solid #E2E8F0;
            margin-bottom: 15px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, var(--primary) 0%, #1D4ED8 100%);
            border-radius: 12px;
            padding: 20px;
            color: white;
            text-align: center;
        }
        
        .stat-card-value {
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.2;
        }
        
        .stat-card-label {
            font-size: 0.85rem;
            opacity: 0.9;
        }
        
        /* Tab Styles */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px !important;
            padding: 10px 20px !important;
            font-weight: 500 !important;
        }
        
        .stTabs [aria-selected="true"] {
            background-color: var(--primary) !important;
            color: white !important;
        }
        
        /* Slider Styles */
        .stSlider > div > div > div {
            background: linear-gradient(90deg, #2563EB, #3B82F6) !important;
        }
        
        /* Expander Styles */
        .streamlit-expanderHeader {
            font-weight: 600 !important;
            color: #1E293B !important;
        }
        
        /* Progress Bar Animation */
        @keyframes progressPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        
        .progress-animated {
            animation: progressPulse 2s ease-in-out infinite;
        }

        /* White background for file uploader drag-drop area */
        [data-testid="stFileUploader"] > section {
            background-color: white !important;
            padding: 15px !important;
            border-radius: 10px !important;
            border: 1px solid #E2E8F0 !important;
        }
        
        [data-testid="stFileUploader"] > section > div {
            background-color: white !important;
        }
        
        /* White background for number input */
        [data-testid="stNumberInput"] > div {
            background-color: white !important;
            padding: 8px !important;
            border-radius: 8px !important;
            border: 1px solid #E2E8F0 !important;
        }
        
        [data-testid="stNumberInput"] input {
            background-color: white !important;
        }

        @media only screen and (max-width: 768px) {
            .stApp h1 { font-size: 1.5rem !important; margin-bottom: 3px !important; }
            .stApp p { font-size: 0.85rem !important; }
            .glass-card { padding: 20px !important; }
            .glass-card h2 { font-size: 1.1rem !important; white-space: nowrap !important; }
            .glass-card p { font-size: 0.75rem !important; }
        }
        </style>
    """, unsafe_allow_html=True)
