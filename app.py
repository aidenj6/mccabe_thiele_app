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
# We use a 4.5 x 4.5 inch square. This fits well on most laptop screens.
fig, ax = plt.subplots(figsize=(4.5, 4.5)) 
x_eq_line = np.linspace(0, 1, 100)
y_eq_line = (alpha * x_eq_line) / (1 + (alpha - 1) * x_eq_line)

ax.plot(x_eq_line, y_eq_line, 'b-', label="Equilibrium", alpha=0.6)
ax.plot([0, 1], [0, 1], 'k--', alpha=0.3)
ax.plot([x_int, xD], [y_int, xD], 'g-', label="ROL")
ax.plot([xB, x_int], [xB, y_int], 'm-', label="SOL")
ax.plot([xF, x_int], [xF, y_int], 'y--', label="q-line")

# Stepping logic
x_curr, y_curr, actual_stages = xD, xD, 0
while x_curr > xB and actual_stages < 100:
    actual_stages += 1
    x_ideal = y_curr / (alpha - y_curr * (alpha - 1))
    x_step = x_curr - eff * (x_curr - x_ideal)
    ax.plot([x_curr, x_step], [y_curr, y_curr], 'r-', linewidth=1)
    x_curr = x_step
    
    if x_curr < xB:
        ax.plot([x_curr, x_curr], [y_curr, x_curr], 'r-', linewidth=1)
        break
        
    if x_curr > x_int:
        y_next = (R / (R + 1)) * x_curr + xD / (R + 1)
    else:
        m_S = (y_int - xB) / (x_int - xB)
        y_next = m_S * (x_curr - xB) + xB
    ax.plot([x_curr, x_curr], [y_curr, y_next], 'r-', linewidth=1)
    y_curr = y_next

ax.set_title(f"McCabe-Thiele (EMV: {int(eff*100)}%)", fontsize=10)
ax.legend(fontsize=8, loc='upper left')
ax.grid(True, alpha=0.2)

# Tight layout removes the margin "padding" around the graph
plt.tight_layout()

# --- DISPLAY LAYOUT ---
# Create three columns to center the square plot in the middle
left_pad, center_col, right_pad = st.columns([1, 2, 1])

with center_col:
    # use_container_width=False ensures the plot respects the figsize(4.5, 4.5)
    st.pyplot(fig, use_container_width=False)
    
    # Display metrics side-by-side immediately under the chart
    m1, m2 = st.columns(2)
    m1.metric("Actual Stages", actual_stages)
    m2.metric("Efficiency", f"{int(eff*100)}%")
