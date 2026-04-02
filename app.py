import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="McCabe-Thiele Solver", layout="wide")

# --- CUSTOM CSS FOR COMPACT WINDOWS LAYOUT ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] .stElementContainer { margin-bottom: -18px; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("Distillation Design: McCabe-Thiele Analysis")

# --- SESSION STATE SYNC ---
def sync_input(key_to_update, key_from_update):
    st.session_state[key_to_update] = st.session_state[key_from_update]

defaults = {'alpha': 2.5, 'xF': 0.5, 'xD': 0.95, 'xB': 0.05, 'R': 2.0, 'q': 1.0, 'eff_val': 0.7}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- SIDEBAR: VLE & EFFICIENCY ---
st.sidebar.header("1. Thermodynamics")
vle_mode = st.sidebar.radio("VLE Data Mode", ["Relative Volatility (α)", "Custom X,Y Data"])

if vle_mode == "Relative Volatility (α)":
    st.sidebar.number_input("Alpha (α)", 1.01, 10.0, step=0.01, key="alpha_num", on_change=sync_input, args=("alpha", "alpha_num"), label_visibility="collapsed")
    st.sidebar.slider("Alpha (α)", 1.01, 10.0, step=0.01, key="alpha", on_change=sync_input, args=("alpha_num", "alpha"), label_visibility="collapsed")
else:
    vle_text = st.sidebar.text_area("X, Y pairs (e.g. 0.2, 0.45)", "0,0\n0.2,0.45\n0.4,0.7\n0.6,0.85\n0.8,0.95\n1,1", height=100)

eff_type = st.sidebar.selectbox("Efficiency Definition", ["Vapor (EMV)", "Liquid (EML)"])
st.sidebar.number_input(f"{eff_type} Value", 0.1, 1.0, step=0.05, key="eff_num", on_change=sync_input, args=("eff_val", "eff_num"), label_visibility="collapsed")
st.sidebar.slider(f"{eff_type} Value", 0.1, 1.0, step=0.05, key="eff_val", on_change=sync_input, args=("eff_num", "eff_val"), label_visibility="collapsed")

st.sidebar.markdown("---")

# --- SIDEBAR: COLUMN SPECS ---
st.sidebar.header("2. Operation")
def create_side_input(label, key, min_v, max_v, step):
    col1, col2 = st.sidebar.columns([2, 1])
    col1.markdown(f"**{label}**")
    col2.number_input(label, min_v, max_v, step=step, key=f"{key}_num", on_change=sync_input, args=(key, f"{key}_num"), label_visibility="collapsed")
    st.sidebar.slider(label, min_v, max_v, step=step, key=key, on_change=sync_
