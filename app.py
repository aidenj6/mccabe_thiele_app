import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.title("McCabe-Thiele Diagram Generator")
st.write("An interactive tool to determine the number of theoretical stages for binary distillation.")

# --- SIDEBAR INPUTS ---
st.sidebar.header("Design Parameters")
alpha = st.sidebar.slider("Relative Volatility (α)", 1.1, 5.0, 2.5, 0.1)
xF = st.sidebar.slider("Feed Composition (z_F)", 0.1, 0.9, 0.5, 0.05)
xD = st.sidebar.slider("Distillate Purity (x_D)", 0.5, 0.99, 0.95, 0.01)
xB = st.sidebar.slider("Bottoms Purity (x_B)", 0.01, 0.5, 0.05, 0.01)
R = st.sidebar.slider("Reflux Ratio (R)", 0.1, 10.0, 2.0, 0.1)
q = st.sidebar.slider("Feed Condition (q)", 0.0, 1.5, 1.0, 0.1)

# Ensure logical composition bounds
if xB >= xF or xF >= xD:
    st.error("Please ensure x_B < z_F < x_D for a valid distillation process.")
    st.stop()

# --- CALCULATIONS ---
# 1. Equilibrium Curve
x_eq = np.linspace(0, 1, 100)
y_eq = (alpha * x_eq) / (1 + (alpha - 1) * x_eq)

# 2. Operating Lines Intersection (q-line and Rectifying line)
# Rectifying Operating Line (ROL): y = (R/(R+1))x + xD/(R+1)
# q-line: y = (q/(q-1))x - xF/(q-1)
if q == 1.0:
    x_int = xF
    y_int = (R / (R + 1)) * x_int + xD / (R + 1)
else:
    # Solving for intersection of ROL and q-line
    # (R/(R+1))x + xD/(R+1) = (q/(q-1))x - xF/(q-1)
    m_R = R / (R + 1)
    b_R = xD / (R + 1)
    m_q = q / (q - 1)
    b_q = -xF / (q - 1)
    
    x_int = (b_q - b_R) / (m_R - m_q)
    y_int = m_R * x_int + b_R

# Check for pinch points (intersection outside bounds or above eq curve)
y_eq_at_x_int = (alpha * x_int) / (1 + (alpha - 1) * x_int)
if y_int > y_eq_at_x_int or x_int < xB or x_int > xD:
    st.error("Operating lines intersect above the equilibrium curve or outside bounds. Try increasing the Reflux Ratio (R).")
    st.stop()

# --- PLOTTING ---
fig, ax = plt.subplots(figsize=(8, 8))
ax.plot(x_eq, y_eq, label="Equilibrium Curve", color="blue") # Eq curve
ax.plot([0, 1], [0, 1], label="x=y line", color="gray", linestyle="--") # x=y line

# Rectifying Operating Line (ROL)
ax.plot([x_int, xD], [y_int, xD], label="Rectifying Line", color="green")
# Stripping Operating Line (SOL)
ax.plot([xB, x_int], [xB, y_int], label="Stripping Line", color="purple")
# q-line
ax.plot([xF, x_int], [xF, y_int], label="q-line", color="orange", linestyle="--")

# Step off stages
x_stage = xD
y_stage = xD
stages = 0

while x_stage > xB and stages < 50: # Cap at 50 to prevent infinite loops
    stages += 1
    # 1. Horizontal line to equilibrium curve
    # x = y / (alpha - y*(alpha-1))
    x_next = y_stage / (alpha - y_stage * (alpha - 1))
    ax.plot([x_stage, x_next], [y_stage, y_stage], color="red")
    
    x_stage = x_next
    
    # Check if we reached the bottoms
    if x_stage < xB:
        # Drop down to x=y line
        ax.plot([x_stage, x_stage], [y_stage, x_stage], color="red")
        break
        
    # 2. Vertical line to operating line
    if x_stage > x_int:
        # Use ROL
        y_next = (R / (R + 1)) * x_stage + xD / (R + 1)
    else:
        # Use SOL (slope between (xB, xB) and (x_int, y_int))
        m_S = (y_int - xB) / (x_int - xB)
        b_S = xB - m_S * xB
        y_next = m_S * x_stage + b_S
        
    ax.plot([x_stage, x_stage], [y_stage, y_next], color="red")
    y_stage = y_next

# Formatting the plot
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.set_xlabel("Liquid Mole Fraction (x)")
ax.set_ylabel("Vapor Mole Fraction (y)")
ax.set_title(f"McCabe-Thiele Diagram (Theoretical Stages: {stages})")
ax.legend()
ax.grid(True, alpha=0.3)

# Display in Streamlit
st.pyplot(fig)
st.success(f"**Total Theoretical Stages required:** {stages}")