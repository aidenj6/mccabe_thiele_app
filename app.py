import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="McCabe-Thiele Generator", layout="wide")

st.title("McCabe-Thiele Diagram Generator")
st.write("Adjust parameters using the sliders or by typing precise values in the boxes.")

# --- SESSION STATE SYNC HELPER ---
# This function ensures that if you change one input, the other updates automatically.
def sync_input(key_to_update, key_from_update):
    st.session_state[key_to_update] = st.session_state[key_from_update]

# Initialize session state for inputs if they don't exist
defaults = {
    'alpha': 2.5, 'xF': 0.5, 'xD': 0.95, 'xB': 0.05, 'R': 2.0, 'q': 1.0
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- SIDEBAR INPUTS ---
st.sidebar.header("Design Parameters")

def create_dual_input(label, key, min_val, max_val, step):
    st.sidebar.markdown(f"**{label}**")
    # Number input (the text box)
    st.sidebar.number_input(label, min_val, max_val, step=step, key=f"{key}_num", 
                            on_change=sync_input, args=(key, f"{key}_num"), label_visibility="collapsed")
    # Slider
    st.sidebar.slider(label, min_val, max_val, step=step, key=key, 
                      on_change=sync_input, args=(f"{key}_num", key), label_visibility="collapsed")
    st.sidebar.markdown("---")

# Creating the inputs using our helper function
create_dual_input("Relative Volatility (α)", "alpha", 1.01, 5.0, 0.01)
create_dual_input("Feed Composition (zF)", "xF", 0.01, 0.99, 0.01)
create_dual_input("Distillate Purity (xD)", "xD", 0.01, 0.99, 0.01)
create_dual_input("Bottoms Purity (xB)", "xB", 0.01, 0.99, 0.01)
create_dual_input("Reflux Ratio (R)", "R", 0.1, 10.0, 0.1)
create_dual_input("Feed Condition (q)", "q", -0.5, 1.5, 0.1)

# Retrieve current values from session state for calculations
alpha = st.session_state.alpha
xF = st.session_state.xF
xD = st.session_state.xD
xB = st.session_state.xB
R = st.session_state.R
q = st.session_state.q

# --- VALIDATION ---
if xB >= xF or xF >= xD:
    st.error("⚠️ Invalid range: Ensure $x_B < z_F < x_D$.")
    st.stop()

# --- CALCULATIONS ---
x_eq = np.linspace(0, 1, 100)
y_eq = (alpha * x_eq) / (1 + (alpha - 1) * x_eq)

# Intersection of ROL and q-line
if q == 1.0:
    x_int = xF
    y_int = (R / (R + 1)) * x_int + xD / (R + 1)
else:
    m_R, b_R = R / (R + 1), xD / (R + 1)
    m_q, b_q = q / (q - 1), -xF / (q - 1)
    x_int = (b_q - b_R) / (m_R - m_q)
    y_int = m_R * x_int + b_R

# --- PLOTTING ---
fig, ax = plt.subplots(figsize=(7, 7))
ax.plot(x_eq, y_eq, 'b-', label="Equilibrium", linewidth=2)
ax.plot([0, 1], [0, 1], 'k--', alpha=0.5)
ax.plot([x_int, xD], [y_int, xD], 'g-', label="ROL")
ax.plot([xB, x_int], [xB, y_int], 'm-', label="SOL")
ax.plot([xF, x_int], [xF, y_int], 'y--', label="q-line")

# Step off stages
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

ax.set_xlabel("x (Liquid Fraction)")
ax.set_ylabel("y (Vapor Fraction)")
ax.set_title(f"Stages: {stages}")
ax.legend()
ax.grid(True, alpha=0.2)

st.pyplot(fig)
st.metric("Total Theoretical Stages", stages)
