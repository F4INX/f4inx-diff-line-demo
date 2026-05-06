import os
import numpy as np
import matplotlib.pyplot as plt

# Load parameters from file
base_name = os.path.splitext(os.path.basename(__file__))[0]  # e.g., "sim-diff-pair-ref-butterfly-replot"
base_name = base_name.replace("-replot", "")  # e.g., "sim-diff-pair-ref-butterfly"
freq, sdd11, sdd21 = np.loadtxt(
    f"sim/{base_name}-S.csv",
    dtype=np.complex64,
    skiprows=1,
    unpack=True
)

fig, ax1 = plt.subplots(figsize=(12, 7))
freq_GHz = freq / 1e9

# Sdd11 (return loss) on left y-axis (dB)
ax1.plot(freq_GHz, 20*np.log10(np.abs(sdd11)), 'b-', linewidth=2, label='Sdd11 (return loss)')
ax1.set_xlabel('Frequency (GHz)')
ax1.set_ylabel('Return Loss (dB)', color='b')
ax1.set_title("Reference for cross w. butterfly simulations")
ax1.grid(True)
ax1.tick_params(axis='y', labelcolor='b')

# Sdd21 (insertion loss) on right y-axis (dB)
ax2 = ax1.twinx()
ax2.plot(freq_GHz, 20*np.log10(np.abs(sdd21)), 'r-', linewidth=2, label='Sdd21 (insertion loss)')
ax2.set_ylabel('Insertion Loss (dB)', color='r')
ax2.tick_params(axis='y', labelcolor='r')

# Combine legends from both axes
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

plt.savefig(f"sim/{base_name}-S.png")
plt.close(fig)
