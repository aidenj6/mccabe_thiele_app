import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Set the page to wide mode and a custom title
st.set_page_config(page_title="McCabe-Thiele Solver", layout="wide")

# --- CUSTOM CSS FOR COMPACT SIDEBAR ---
# This reduces the vertical padding between widgets in the sidebar
st.markdown("""
    <style>
    [data-testid="stSidebar"] .stElementContainer { margin-bottom: -15px; }
    </style>
    """, unsafe_allow_html=True)

st.title("McCabe-Thiele Diagram Generator")

# --- SESSION STATE SYNC ---
def sync_input(key_to_update, key_from_update):
    st.session_state[key_to_update] = st.session_state[key_from_update]

defaults = {'alpha': 2.5, 'xF': 0.5, 'xD': 0.95, 'xB': 0.05, 'R': 2.0, 'q': 1.0}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- COMPACT SIDEBAR INPUTS ---
st.sidebar.header("Design Parameters")

def create_dual_input(label, key, min_val, max_val, step):
    # Create two columns in the sidebar: one for label, one for the number box
    col1, col2 = st.sidebar.columns([2, 1])
    with col1:
        st.markdown(f"**{label}**")
    with col2:
        st.number_input(label, min_val, max_val, step=step, key=f"{key}_num", 
                        on_change=sync_input, args=(key, f"{key}_num"), label_visibility="collapsed")
    
    # Slider directly underneath with no extra label to save space
    st.sidebar.slider(label, min_val, max_val, step=step, key=key, 
                      on_change=sync_input, args=(f"{key}_num", key), label_visibility="collapsed")
    st.sidebar.markdown("---")

create_dual_input("Relative Volatility (α)", "alpha", 1.01, 5.0, 0.01)
create_dual_input("Feed Comp. (zF)", "xF", 0.01, 0.99, 0.01)
create_dual_input("Distillate Purity (xD)", "xD", 0.01, 0.99, 0.01)
create_dual_input("Bottoms Purity (xB)", "xB", 0.01, 0.99, 0.01)
create_dual_input("Reflux Ratio (R)", "R", 0.1, 10.0, 0.1)
create_dual_input("Feed Condition (q)", "q", -0.5, 1.5, 0.1)

# Retrieve values
alpha, xF, xD, xB, R, q = [st.session_state[k] for k in defaults.keys()]

# --- VALIDATION ---
if xB >= xF or xF >= xD:
    st.error("⚠️ Invalid range: Ensure $x_B < z_F < x_D$.")
    st.stop()

# --- CALCULATIONS & PLOTTING ---
# Intersection calculation
if q == 1.0:
    x_int, y_int = xF, (R / (R + 1)) * xF + xD / (R + 1)
else:
    m_R, b_R = R / (R + 1), xD / (R + 1)
    m_q, b_q = q / (q - 1), -xF / (q - 1)
    x_int = (b_q - b_R) / (m_R - m_q)
    y_int = m_R * x_int + b_R

# Smaller Figure Size (reduced from 7 to 5)
fig, ax = plt.subplots(figsize=(5, 5))
x_eq = np.linspace(0, 1, 100)
y_eq = (alpha * x_eq) / (1 + (alpha - 1) * x_eq)

ax.plot(x_eq, y_eq, 'b-', label="Equilibrium")
ax.plot([0, 1], [0, 1], 'k--', alpha=0.3)
ax.plot([x_int, xD], [y_int, xD], 'g-', label="ROL")
ax.plot([xB, x_int], [xB, y_int], 'm-', label="SOL")
ax.plot([xF, x_int], [xF, y_int], 'y--', label="q-line")

# Stepping logic
x_curr, y_curr, stages = xD, xD, 0
while x_curr > xB and stages < 100:
    stages += 1
    x_next = y_curr / (alpha - y_curr * (alpha - 1))
    ax.plot([x_curr, x_next], [y_curr, y_curr], 'r-', linewidth=1)
    x_curr = x_next
    if x_curr < xB:
        ax.plot([x_curr, x_curr], [y_curr, x_curr], 'r-', linewidth=1)
        break
    y_next = ((R/(R+1))*x_curr + xD/(R+1)) if x_curr > x_int else (((y_int-xB)/(x_int-xB))*(x_curr-xB) + xB)
    ax.plot([x_curr, x_curr], [y_curr, y_next], 'r-', linewidth=1)
    y_curr = y_next

ax.set_title(f"Total Stages: {stages}", fontsize=10)
ax.legend(fontsize=8)
ax.grid(True, alpha=0.2)

# Use columns in the main area to prevent the chart from stretching too wide
left_spacer, center_content, right_spacer = st.columns([1, 3, 1])
with center_content:
    st.pyplot(fig)
    st.metric("Theoretical Stages", stages)
