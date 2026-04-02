import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="McCabe-Thiele Solver", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    [data-testid="stSidebar"] .stElementContainer { margin-bottom: -15px; }
    </style>
    """, unsafe_allow_html=True)

st.title("McCabe-Thiele Diagram Generator")

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

if xB >= xF or xF >= xD:
    st.error("⚠️ Invalid range: Ensure $x_B < z_F < x_D$.")
    st.stop()

# --- CALCULATIONS ---
if q == 1.0:
    x_int, y_int = xF, (R / (R + 1)) * xF + xD / (R + 1)
else:
    m_R, b_R = R / (R + 1), xD / (R + 1)
    m_q, b_q = q / (q - 1), -xF / (q - 1)
    x_int = (b_q - b_R) / (m_R - m_q)
    y_int = m_R * x_int + b_R

# --- PLOTTING ---
fig, ax = plt.subplots(figsize=(5, 5))
x_eq_line = np.linspace(0, 1, 100)
y_eq_line = (alpha * x_eq_line) / (1 + (alpha - 1) * x_eq_line)

ax.plot(x_eq_line, y_eq_line, 'b-', label="Equilibrium", alpha=0.6)
ax.plot([0, 1], [0, 1], 'k--', alpha=0.3)
ax.plot([x_int, xD], [y_int, xD], 'g-', label="ROL")
ax.plot([xB, x_int], [xB, y_int], 'm-', label="SOL")
ax.plot([xF, x_int], [xF, y_int], 'y--', label="q-line")

# Stepping logic with Efficiency
x_curr, y_curr, actual_stages = xD, xD, 0
while x_curr > xB and actual_stages < 100:
    actual_stages += 1
    
    # 1. Find the theoretical y on the equilibrium curve for current x
    # y_ideal = (alpha * x) / (1 + (alpha - 1) * x) ... but we are stepping from y to x
    # So first, find the x that WOULD be in equilibrium with current y
    x_ideal = y_curr / (alpha - y_curr * (alpha - 1))
    
    # Apply Murphree Efficiency: x_actual = x_prev - eff * (x_prev - x_ideal)
    # Note: For stepping down, efficiency is applied to the horizontal change
    x_step = x_curr - eff * (x_curr - x_ideal)
    
    ax.plot([x_curr, x_step], [y_curr, y_curr], 'r-', linewidth=1)
    x_curr = x_step
    
    if x_curr < xB:
        ax.plot([x_curr, x_curr], [y_curr, x_curr], 'r-', linewidth=1)
        break
        
    # 2. Vertical step to operating line
    if x_curr > x_int:
        y_next = (R / (R + 1)) * x_curr + xD / (R + 1)
    else:
        m_S = (y_int - xB) / (x_int - xB)
        y_next = m_S * (x_curr - xB) + xB
        
    ax.plot([x_curr, x_curr], [y_curr, y_next], 'r-', linewidth=1)
    y_curr = y_next

ax.set_title(f"McCabe-Thiele (Efficiency: {eff*100}%)", fontsize=10)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.2)

left_spacer, center_content, right_spacer = st.columns([1, 3, 1])
with center_content:
    st.pyplot(fig)
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Actual Stages", actual_stages)
    col_m2.metric("Efficiency Applied", f"{eff*100}%")
