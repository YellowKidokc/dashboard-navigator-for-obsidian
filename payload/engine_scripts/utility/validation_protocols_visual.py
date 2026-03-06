import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.patches import Rectangle, FancyArrow, Circle
import matplotlib.patches as mpatches

# High-quality rendering settings
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'serif'

fig = plt.figure(figsize=(22, 14))

# Title
fig.text(0.5, 0.97, 'PROTOCOLS FOR VALIDATION',
         fontsize=34, weight='bold', ha='center', color='white')
fig.text(0.5, 0.945, 'Three Experimental Pathways to Prove a Conscious Cosmos',
         fontsize=18, ha='center', color='#FFD700', style='italic')

fig.patch.set_facecolor('#0f0f1e')

# ==================== PROTOCOL 1: THE DOROTHY PROTOCOL ====================
ax1 = fig.add_subplot(2, 3, (1, 2), projection='3d')
ax1.set_facecolor('#1a1a2e')
ax1.set_title('PROTOCOL 1: THE DOROTHY PROTOCOL\n"Not in Kansas Anymore"',
              fontsize=14, weight='bold', color='#FF6B9D', pad=15)

# Double-slit apparatus
slit_x = -3
slit_y = 0
slit_z = np.linspace(-1, 1, 20)

# Screen
for z_val in slit_z:
    ax1.plot([slit_x, slit_x], [-1.5, 1.5], [z_val, z_val],
             color='gray', linewidth=2, alpha=0.7)

# Two slits
ax1.plot([slit_x, slit_x], [-0.3, 0.3], [0.5, 0.5],
         color='black', linewidth=8)
ax1.plot([slit_x, slit_x], [-0.3, 0.3], [-0.5, -0.5],
         color='black', linewidth=8)

# Photon source (left)
photon_x = -5
photon_y = 0
photon_z = 0
ax1.scatter([photon_x], [photon_y], [photon_z],
            c='yellow', s=500, marker='*', edgecolors='orange', linewidths=2)
ax1.text(photon_x, photon_y, photon_z - 1, 'Photon\nSource',
         fontsize=8, ha='center', color='yellow')

# Photons traveling
n_photons = 15
for i in range(n_photons):
    y_offset = (np.random.rand() - 0.5) * 0.5
    z_offset = (np.random.rand() - 0.5) * 2
    ax1.plot([photon_x, slit_x], [y_offset, y_offset], [z_offset, z_offset],
             'y--', alpha=0.6, linewidth=1)

# Detection screen (right)
screen_x = 2
screen_y_vals = np.linspace(-2, 2, 30)
screen_z_vals = np.linspace(-1.5, 1.5, 30)
Screen_Y, Screen_Z = np.meshgrid(screen_y_vals, screen_z_vals)
Screen_X = np.ones_like(Screen_Y) * screen_x

# Interference pattern (will vary with intent)
interference = np.sin(Screen_Z * 4) ** 2
ax1.plot_surface(Screen_X, Screen_Y, Screen_Z,
                 facecolors=cm.viridis(interference),
                 alpha=0.7, antialiased=True, linewidth=0)

# Observer (human with EEG/HRV monitoring)
obs_x = 0
obs_y = -4
obs_z = -2

# Head
u = np.linspace(0, 2 * np.pi, 15)
v = np.linspace(0, np.pi, 15)
head_r = 0.3
head_x = head_r * np.outer(np.cos(u), np.sin(v)) + obs_x
head_y = head_r * np.outer(np.sin(u), np.sin(v)) + obs_y
head_z = head_r * np.outer(np.ones(np.size(u)), np.cos(v)) + obs_z
ax1.plot_surface(head_x, head_y, head_z, color='#FFE082', alpha=0.9)

# EEG sensors on head
for i in range(5):
    angle = 2 * np.pi * i / 5
    sensor_x = obs_x + 0.35 * np.cos(angle)
    sensor_y = obs_y + 0.35 * np.sin(angle)
    sensor_z = obs_z + 0.2
    ax1.scatter([sensor_x], [sensor_y], [sensor_z],
                c='cyan', s=50, marker='o')

# Intent beam
intent_x = [obs_x, screen_x]
intent_y = [obs_y, 0]
intent_z = [obs_z + 0.3, 0]
ax1.plot(intent_x, intent_y, intent_z, color='magenta', linewidth=4,
         linestyle=':', label='Coherent Intent', alpha=0.8)

ax1.text(obs_x, obs_y, obs_z - 1, 'Observer\n(EEG/HRV)',
         fontsize=8, ha='center', color='cyan', weight='bold')

# Prediction box
ax1.text(screen_x + 1, 0, 1.5, 'PREDICTION:\nIntent biases\ninterference',
         fontsize=9, ha='center', color='#4CAF50', weight='bold',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='black', alpha=0.8, edgecolor='#4CAF50'))

ax1.set_xlim([-6, 4])
ax1.set_ylim([-5, 3])
ax1.set_zlim([-3, 2])
ax1.view_init(elev=20, azim=130)
ax1.set_xticks([])
ax1.set_yticks([])
ax1.set_zticks([])
ax1.grid(False)

# ==================== PROTOCOL 2: ALGORITHMIC PURITY COLLAPSE TEST ====================
ax2 = fig.add_subplot(2, 3, 3, projection='3d')
ax2.set_facecolor('#1a1a2e')
ax2.set_title('PROTOCOL 2: APCT\n"Logos Prefers Elegance"',
              fontsize=14, weight='bold', color='#64B5F6', pad=15)

# QRNG device (center)
qrng_x = 0
qrng_y = 0
qrng_z = 0

# Device box
box_size = 0.8
vertices = np.array([
    [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
    [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]
]) * box_size

vertices[:, 0] += qrng_x
vertices[:, 1] += qrng_y
vertices[:, 2] += qrng_z

# Draw cube edges
edges = [
    [0, 1], [1, 2], [2, 3], [3, 0],
    [4, 5], [5, 6], [6, 7], [7, 4],
    [0, 4], [1, 5], [2, 6], [3, 7]
]

for edge in edges:
    ax2.plot3D([vertices[edge[0], 0], vertices[edge[1], 0]],
               [vertices[edge[0], 1], vertices[edge[1], 1]],
               [vertices[edge[0], 2], vertices[edge[1], 2]],
               'c-', linewidth=3)

ax2.text(qrng_x, qrng_y, qrng_z, 'QRNG',
         fontsize=12, ha='center', va='center', color='cyan', weight='bold')

# Input 1: High complexity (random noise) - LEFT
noise_x = -3
noise_y = 0
noise_z = 0

# Show random noise as chaotic particles
n_noise = 50
for i in range(n_noise):
    px = noise_x + (np.random.rand() - 0.5) * 0.8
    py = noise_y + (np.random.rand() - 0.5) * 0.8
    pz = noise_z + (np.random.rand() - 0.5) * 0.8
    ax2.scatter([px], [py], [pz], c='red', s=10, alpha=0.7, marker='x')

ax2.text(noise_x, noise_y, noise_z - 1.5, 'HIGH K(x)\n(Random Noise)',
         fontsize=9, ha='center', color='red', weight='bold')

# Data stream
stream_t = np.linspace(0, 1, 20)
stream_x = noise_x + stream_t * (qrng_x - noise_x)
stream_y = noise_y + np.sin(stream_t * 10) * 0.3
stream_z = noise_z + np.cos(stream_t * 10) * 0.3
ax2.plot(stream_x, stream_y, stream_z, 'r--', linewidth=2, alpha=0.6)

# Input 2: Low complexity (Gospel of John) - RIGHT
gospel_x = 3
gospel_y = 0
gospel_z = 0

# Show ordered structure
theta = np.linspace(0, 4*np.pi, 50)
spiral_x = gospel_x + 0.3 * np.cos(theta)
spiral_y = gospel_y + 0.3 * np.sin(theta)
spiral_z = gospel_z + theta * 0.1 - 0.6

ax2.plot(spiral_x, spiral_y, spiral_z, color='gold', linewidth=3, alpha=0.9)

ax2.text(gospel_x, gospel_y, gospel_z - 1.5, 'LOW K(x)\n(Gospel Text)',
         fontsize=9, ha='center', color='gold', weight='bold')

# Data stream
stream_x2 = gospel_x + stream_t * (qrng_x - gospel_x)
stream_y2 = gospel_y + np.sin(stream_t * 2) * 0.1
stream_z2 = gospel_z + np.cos(stream_t * 2) * 0.1
ax2.plot(stream_x2, stream_y2, stream_z2, color='gold', linewidth=2,
         linestyle='--', alpha=0.6)

# Output differential
output_x = 0
output_y = 0
output_z = 2

ax2.text(output_x, output_y, output_z, '≠',
         fontsize=60, ha='center', color='white', weight='bold')

ax2.text(output_x - 0.5, output_y, output_z + 0.8, 'Chaotic',
         fontsize=8, ha='right', color='red')
ax2.text(output_x + 0.5, output_y, output_z + 0.8, 'Ordered',
         fontsize=8, ha='left', color='gold')

# Prediction box
ax2.text(0, 0, -2.5, 'PREDICTION:\nLow K(x) input\n→ More ordered output',
         fontsize=9, ha='center', color='#4CAF50', weight='bold',
         bbox=dict(boxstyle='round,pad=0.4', facecolor='black', alpha=0.8, edgecolor='#4CAF50'))

ax2.set_xlim([-4, 4])
ax2.set_ylim([-2, 2])
ax2.set_zlim([-3, 3])
ax2.view_init(elev=15, azim=45)
ax2.set_xticks([])
ax2.set_yticks([])
ax2.set_zticks([])
ax2.grid(False)

# ==================== PROTOCOL 3: TEMPORAL DECOHERENCE DELAY ====================
ax3 = fig.add_subplot(2, 3, (4, 5), projection='3d')
ax3.set_facecolor('#1a1a2e')
ax3.set_title('PROTOCOL 3: TEMPORAL DECOHERENCE DELAY\n"Consciousness Slows Quantum Decay"',
              fontsize=14, weight='bold', color='#9C27B0', pad=15)

# Entangled photon pair (center)
photon_a_x = -1.5
photon_b_x = 1.5
photon_y = 0
photon_z = 0

# Photon A (blue)
ax3.scatter([photon_a_x], [photon_y], [photon_z],
            c='blue', s=500, marker='o', edgecolors='cyan', linewidths=3, alpha=0.8)
ax3.text(photon_a_x, photon_y, photon_z - 1, 'Photon A',
         fontsize=9, ha='center', color='cyan')

# Photon B (red)
ax3.scatter([photon_b_x], [photon_y], [photon_z],
            c='red', s=500, marker='o', edgecolors='orange', linewidths=3, alpha=0.8)
ax3.text(photon_b_x, photon_y, photon_z - 1, 'Photon B',
         fontsize=9, ha='center', color='orange')

# Entanglement connection
t_ent = np.linspace(0, 1, 50)
ent_x = photon_a_x + t_ent * (photon_b_x - photon_a_x)
ent_y = photon_y + np.sin(t_ent * 8 * np.pi) * 0.3
ent_z = photon_z + np.cos(t_ent * 8 * np.pi) * 0.3

ax3.plot(ent_x, ent_y, ent_z, color='magenta', linewidth=4, alpha=0.9,
         label='Entanglement')

# Coherence decay over time (without observer)
time_axis = np.linspace(0, 5, 50)
coherence_no_obs = np.exp(-time_axis * 0.5)  # Rapid decay

ax3.plot(time_axis - 2.5, [3] * len(time_axis), coherence_no_obs * 2,
         color='red', linewidth=3, linestyle='--', label='No Observer', alpha=0.7)

# Coherence with observer (slower decay)
coherence_with_obs = np.exp(-time_axis * 0.2)  # Slower decay

ax3.plot(time_axis - 2.5, [-3] * len(time_axis), coherence_with_obs * 2,
         color='green', linewidth=3, linestyle='-', label='With Observer', alpha=0.9)

# Observer focusing intent
obs_x = 0
obs_y = -5
obs_z = -1

# Observer figure
u = np.linspace(0, 2 * np.pi, 15)
v = np.linspace(0, np.pi, 15)
head_r = 0.4
head_x = head_r * np.outer(np.cos(u), np.sin(v)) + obs_x
head_y = head_r * np.outer(np.sin(u), np.sin(v)) + obs_y
head_z = head_r * np.outer(np.ones(np.size(u)), np.cos(v)) + obs_z
ax3.plot_surface(head_x, head_y, head_z, color='#FFE082', alpha=0.9)

# Observation beam preserving coherence
ax3.plot([obs_x, 0], [obs_y, 0], [obs_z + 0.4, 0],
         color='cyan', linewidth=5, alpha=0.8, linestyle=':')

ax3.text(obs_x, obs_y, obs_z - 1.2, 'Coherent\nObserver',
         fontsize=9, ha='center', color='cyan', weight='bold')

# Labels for graphs
ax3.text(0, 3, 2.5, 'Control (no intent)',
         fontsize=9, ha='center', color='red', style='italic')
ax3.text(0, -3, 2.5, 'With focused intent',
         fontsize=9, ha='center', color='green', weight='bold', style='italic')

# Time arrow
ax3.plot([2.5, 3.5], [3, 3], [0, 0], 'w->', linewidth=2)
ax3.text(4, 3, 0, 't', fontsize=11, color='white', style='italic')

# Prediction box
ax3.text(0, 0, 3, 'PREDICTION:\nCoherence lifetime ↑\nwhen observed',
         fontsize=10, ha='center', color='#4CAF50', weight='bold',
         bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.8, edgecolor='#4CAF50'))

ax3.set_xlim([-3, 4])
ax3.set_ylim([-6, 4])
ax3.set_zlim([-2, 4])
ax3.view_init(elev=20, azim=110)
ax3.set_xticks([])
ax3.set_yticks([])
ax3.set_zticks([])
ax3.grid(False)

# ==================== SUMMARY PANEL ====================
ax4 = fig.add_subplot(2, 3, 6)
ax4.set_facecolor('#1a1a2e')
ax4.axis('off')

# Title
ax4.text(0.5, 0.95, 'THE MANDATE', fontsize=16, weight='bold', ha='center',
         color='white', transform=ax4.transAxes)

# Summary text
summary_lines = [
    ('', 0.88),
    ('"Not even wrong" is the worst criticism', 0.82),
    ('of a scientific theory.', 0.78),
    ('', 0.72),
    ('These protocols provide FALSIFIABLE tests:', 0.66),
    ('', 0.60),
    ('✓ Dorothy: 6-sigma intent effect on QM', 0.54),
    ('✓ APCT: 5-sigma bias toward low K(x)', 0.48),
    ('✓ Temporal: 5-sigma coherence extension', 0.42),
    ('', 0.36),
    ('Each protocol tests a different facet', 0.30),
    ('of the Logos framework.', 0.26),
    ('', 0.20),
    ('This is not philosophy.', 0.14),
    ('This is TESTABLE SCIENCE.', 0.08),
]

for text, y_pos in summary_lines:
    if text.startswith('✓'):
        color = '#4CAF50'
        weight = 'bold'
        size = 11
    elif 'TESTABLE' in text:
        color = '#FFD700'
        weight = 'bold'
        size = 13
    elif text == '':
        continue
    else:
        color = 'white'
        weight = 'normal'
        size = 11

    ax4.text(0.5, y_pos, text, fontsize=size, weight=weight, ha='center',
             color=color, transform=ax4.transAxes, style='italic' if 'worst' in text else 'normal')

# ==================== BOTTOM TEXT ====================
fig.text(0.5, 0.02,
         'Click your heels. Run the experiments. See where you wake up.',
         fontsize=14, ha='center', color='#FF6B9D', weight='bold', style='italic')

plt.tight_layout(rect=[0, 0.03, 1, 0.96])
plt.savefig('validation_protocols_3d.png', dpi=300, facecolor='#0f0f1e', bbox_inches='tight')
print("3D visualization 'Protocols for Validation' completed!")
