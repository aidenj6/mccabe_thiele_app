import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# 1. Page configuration
st.set_page_config(page_title="McCabe-Thiele Solver", layout="wide")

# 2. UI Tightening: Hide header/footer and reduce padding
st.markdown("""
    <style>
    /* Hide the Streamlit header and footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Reduce top padding to pull content up */
    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 0rem;
    }

    /* Shrink the sidebar spacing for a cleaner look */
    [data-testid="stSidebar"] .stElementContainer { margin-bottom: -18px; }
    
    /* Adjust metric font size to save vertical space */
    [data-testid="stMetricValue"] { font-size: 1.8rem; }
    </style>
    """, unsafe_allow_html=True)

# Smaller header to save space
st.subheader("McCabe-Thiele Diagram Generator")

# --- SESSION STATE SYNC ---
def sync_input(key_to_update, key_from_update):
    st.session_state[key_to_update] = st.session_state[key_from_update]

defaults = {'alpha': 2.5, 'xF': 0.5, 'xD': 0.95, 'xB': 0.05, 'R': 2.0, 'q': 1.0, 'eff': 0.7}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- SIDEBAR INPUTS ---
st.sidebar.header("Design Parameters")

def create_dual_input(label, key, min_val, max_val, step):
    col1, col2 = st.sidebar.columns([2, 1])
    with col1:
        st.markdown(f"**{label}**")
    with col2:
        st.number_input(label, min_val, max_val, step=step, key=f"{key}_num", 
                        on_change=sync_input, args=(key, f"{key}_num"), label_visibility="collapsed")
    st.sidebar.slider(label, min_val, max_val, step=step, key=key, 
                      on_change=sync_input, args=(f"{key}_num", key), label_visibility="collapsed")
    st.sidebar.markdown("---")

create_dual_input("Relative Volatility (α)", "alpha", 1.01, 5.0, 0.01)
create_dual_input("Feed Comp. (zF)", "xF", 0.01, 0.99, 0.01)
create_dual_input("Distillate Purity (xD)", "xD", 0.01, 0.99, 0.01)
create_dual_input("Bottoms Purity (xB)", "xB", 0.01, 0.99, 0.01)
create_dual_input("Reflux Ratio (R)", "R", 0.1, 10.0, 0.1)
create_dual_input("Feed Condition (q)", "q", -0.5, 1.5, 0.1)
create_dual_input("Tray Efficiency (EMV)", "eff", 0.1, 1.0, 0.05)

alpha, xF, xD, xB, R, q, eff = [st.session_state[k] for k in defaults.keys()]

# Validation
if xB >= xF or xF >= xD:
    st.error("⚠️ Invalid range: Ensure $x_B < z_F < x_D$.")
    st.
