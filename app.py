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
    st.sidebar.slider(label, min_v, max_v, step=step, key=key, on_change=sync_input, args=(f"{key}_num", key), label_visibility="collapsed")

create_side_input("Feed (zF)", "xF", 0.01, 0.99, 0.01)
create_side_input("Distillate (xD)", "xD", 0.01, 0.99, 0.01)
create_side_input("Bottoms (xB)", "xB", 0.01, 0.99, 0.01)
create_side_input("Reflux (R)", "R", 0.1, 10.0, 0.1)
create_side_input("Condition (q)", "q", -0.5, 1.5, 0.1)

# Retrieve current values
alpha, xF, xD, xB, R, q, eff = st.session_state.alpha, st.session_state.xF, st.session_state.xD, st.session_state.xB, st.session_state.R, st.session_state.q, st.session_state.eff_val

# --- CALCULATION LOGIC ---
if xB >= xF or xF >= xD:
    st.error("⚠️ Ensure $x_B < z_F < x_D$.")
    st.stop()

x_eq_plot = np.linspace(0, 1, 100)
if vle_mode == "Relative Volatility (α)":
    y_eq_plot = (alpha * x_eq_plot) / (1 + (alpha - 1) * x_eq_plot)
    def get_y_eq(x): return (alpha * x) / (1 + (alpha - 1) * x)
    def get_x_eq(y): return y / (alpha - y * (alpha - 1))
else:
    try:
        raw = [list(map(float, l.split(','))) for l in vle_text.strip().split('\n')]
        vle_arr = np.array(raw)
        x_eq_plot, y_eq_plot = vle_arr[:,0], vle_arr[:,1]
        def get_y_eq(x): return np.interp(x, x_eq_plot, y_eq_plot)
        def get_x_eq(y): return np.interp(y, y_eq_plot, x_eq_plot)
    except:
        st.error("Invalid Custom VLE data format.")
        st.stop()

# Operating Lines Intersection
if q == 1.0: 
    x_int, y_int = xF, (R/(R+1))*xF + xD/(R+1)
else:
    m_R, b_R = R/(R+1), xD/(R+1)
    m_q, b_q = q/(q-1), -xF/(q-1)
    x_int = (b_q - b_R) / (m_R - m_q)
    y_int = m_R * x_int + b_R

# --- PLOTTING ---
fig, ax = plt.subplots(figsize=(5, 5))
ax.plot(x_eq_plot, y_eq_plot, 'b-', label="VLE Curve", linewidth=2)
ax.plot([0, 1], [0, 1], 'k--', alpha=0.3)
ax.plot([x_int, xD], [y_int, xD], 'g-', label="ROL")
ax.plot([xB, x_int], [xB, y_int], 'm-', label="SOL")
ax.plot([xF, x_int], [xF, y_int], 'y--', label="q-line")

# Stepping off Stages
x_c, y_c, stages = xD, xD, 0
while x_c > xB and stages < 100:
    stages += 1
    x_ideal = get_x_eq(y_c)
    
    # Efficiency Application
    if eff_type == "Vapor (EMV)":
        x_step = x_c - eff * (x_c - x_ideal)
    else: # Liquid (EML)
        x_step = x_ideal + (1 - eff) * (x_c - x_ideal)

    ax.plot([x_c, x_step], [y_c, y_c], 'r-', linewidth=1)
    x_c = x_step
    if x_c < xB:
        ax.plot([x_c, x_c], [y_c, x_c], 'r-', linewidth=1)
        break
    
    y_next = ((R/(R+1))*x_c + xD/(R+1)) if x_c > x_int else (((y_int-xB)/(x_int-xB))*(x_c-xB) + xB)
    ax.plot([x_c, x_c], [y_c, y_next], 'r-', linewidth=1)
    y_c = y_next

ax.set_xlabel("x (Liquid Fraction)")
ax.set_ylabel("y (Vapor Fraction)")
ax.legend(fontsize=8)
ax.grid(True, alpha=0.2)

# Main Dashboard Layout
l_col, r_col = st.columns([2, 1])
with l_col:
    st.pyplot(fig)

with r_col:
    st.markdown("### Results")
    st.metric(f"Total {eff_type} Stages", stages)
    st.write(f"This calculation uses the **{eff_type}** definition to determine the actual number of trays required for the specified separation.")
    if vle_mode == "Custom X,Y Data":
        st.info("Using interpolated custom VLE data points.")
    else:
        st.info(f"Using Relative Volatility (α = {alpha}) model.")
