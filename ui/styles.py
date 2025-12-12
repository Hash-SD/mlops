"""
Module untuk mengelola Custom CSS dan Styling aplikasi.
Mengimplementasikan Glassmorphism & Clean UI Design principles.
"""

import streamlit as st

def load_css():
    """
    Inject custom CSS ke dalam aplikasi Streamlit.
    """
    st.markdown("""
        <style>
        /* Import Google Fonts (Outfit for Headers, Inter for Body) */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');

        :root {
            /* Palette */
            --primary: #2563EB; /* Bright Blue */
            --primary-hover: #1D4ED8;
            --secondary: #64748B;
            --background: #F8FAFC;
            --surface: #FFFFFF;
            --text-main: #1E293B;
            --text-muted: #64748B;
            
            /* Glassmorphism */
            --glass-bg: rgba(255, 255, 255, 0.7);
            --glass-border: 1px solid rgba(255, 255, 255, 0.5);
            --glass-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            
            /* Spacing */
            --radius-lg: 16px;
            --radius-md: 12px;
            --radius-sm: 8px;
        }

        /* Global Reset & Typography Scale */
        .stApp {
            background-color: var(--background);
            font-family: 'Inter', sans-serif;
            color: var(--text-main);
            font-size: 0.9rem !important; /* Base Body Text: ~14.4px */
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
        
        /* Paragraphs & Lists */
        p, li {
            font-size: 0.9rem !important;
            line-height: 1.6 !important;
        }
        
        /* Captions / Small Text */
        .stCaption, small, .small-text, [data-testid="stCaptionContainer"] {
            font-size: 0.8rem !important; /* ~12.8px */
            color: var(--text-muted) !important;
        }

        /* Sidebar Specific Upscaling */
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] span {
             font-size: 0.875rem !important;
        }

        [data-testid="stSidebar"] h3 {
             font-size: 1rem !important; /* ~16px */
             font-weight: 700 !important;
             padding-top: 20px !important;
             padding-bottom: 12px !important;
             margin-top: 12px !important;
             margin-bottom: 8px !important;
             line-height: 1.3;
             text-transform: uppercase;
             letter-spacing: 0.05em;
             color: #64748B !important;
        }

        /* Specific override for Logo Icon */
        [data-testid="stSidebar"] .sidebar-logo-icon {
            font-size: 8.5rem !important;
            margin-bottom: -15px !important;
            line-height: 1 !important;
            display: block !important;
            color: #1E293B !important;
        }

        /* Upscale Radio Button Labels (Navigation) */
        [data-testid="stSidebar"] .stRadio label p {
             font-size: 0.95rem !important; /* Navigation text */
        }
        
        /* Add spacing between radio options */
        [data-testid="stSidebar"] .stRadio > div {
             gap: 0.8rem !important;
             margin-bottom: 20px !important;  /* Space after navigation */
        }
        
        /* Add spacing to form elements in sidebar */
        [data-testid="stSidebar"] .stTextInput,
        [data-testid="stSidebar"] .stSelectbox,
        [data-testid="stSidebar"] .stTextArea {
             margin-bottom: 15px !important;
        }
        
        /* Add spacing to buttons in sidebar */
        [data-testid="stSidebar"] .stButton {
             margin-top: 10px !important;
             margin-bottom: 15px !important;
        }
        
        /* Add spacing to expanders in sidebar */
        [data-testid="stSidebar"] .st-emotion-cache-1gulkj5,
        [data-testid="stSidebar"] details {
             margin-top: 15px !important;
             margin-bottom: 15px !important;
        }
        
        /* General section spacing in sidebar */
        [data-testid="stSidebar"] > div > div > div {
             margin-bottom: 20px !important;
        }
        
        /* Inputs (Text Area, Input, Selectbox) */
        .stTextArea textarea, .stTextInput input, .stSelectbox div[data-baseweb="select"] {
            font-size: 0.9rem !important;
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Buttons */
        div.stButton > button {
            font-size: 0.9rem !important;
            padding: 0.7rem 1.3rem !important;
        }

        /* --- CONTAINER CENTERING --- */
        /* Center the main block content like a document */
        [data-testid="stMainBlockContainer"] {
            max-width: 1100px; /* Slightly wider to accommodate larger text */
            margin: 0 auto;
            padding-top: 2rem;
        }

        /* --- GLASS CARD COMPONENT --- */
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

        /* --- EMPTY STATE (Dotted Box) --- */
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
        
        /* --- BUTTONS --- */
        /* Primary Button */
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

        /* Example Buttons (Full Width Blue) */
        .example-btn-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            width: 100%;
        }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #EEF2FF;
        }

        /* Nav hidden if custom nav is used, currently we rely on radio */
        div[data-testid="stSidebarNav"] {
            display: none; 
        }

        /* Steps Card in Sidebar */
        .step-card {
            background: #F8FAFC;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
            border-left: 3px solid var(--primary);
        }
        
        /* Inputs */
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
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 40px 0;
            color: #94A3B8;
            font-size: 0.85rem;
            margin-top: 40px;
            border-top: 1px solid #F1F5F9;
        }
        /* Glass Table */
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
        .glass-table tr:last-child td {
            border-bottom: none;
        }
        .glass-table tr:hover {
            background-color: rgba(248, 250, 252, 0.6);
        }
        
        .badge-pos {
            background: #DCFCE7; color: #166534; padding: 4px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 500;
        }
        .badge-neg {
            background: #FEE2E2; color: #991B1B; padding: 4px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 500;
        }
        .badge-neu {
            background: #F1F5F9; color: #475569; padding: 4px 8px; border-radius: 6px; font-size: 0.8rem; font-weight: 500;
        }

        /* Metric Spacing Fix */
        [data-testid="stMetricLabel"] {
            margin-bottom: 0.5rem !important; /* Jarak antara Label dan Value */
            font-size: 1rem !important;
            color: var(--text-muted);
        }
        
        [data-testid="stMetricValue"] {
            padding-top: 5px !important; /* Tambahan jarak halus */
        }
        </style>
    """, unsafe_allow_html=True)

