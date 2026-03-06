import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.spatial.transform import Rotation

# High-quality rendering settings
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'serif'

fig = plt.figure(figsize=(20, 12))
ax = fig.add_subplot(111, projection='3d')
ax.set_facecolor('#000510')
fig.patch.set_facecolor('#000510')

# Title
fig.text(0.5, 0.96, 'THE MORAL UNIVERSE',
         fontsize=32, weight='bold', ha='center', color='white')
fig.text(0.5, 0.93, 'Ethics as Physics: Choices Shape Reality',
         fontsize=18, ha='center', color='#64B5F6', style='italic')

# ==================== THE CENTRAL HUMAN FIGURE ====================
# A stylized human form at the center - the moral agent
human_z = 0
human_y = 0
human_x = 0

# Head (sphere)
u = np.linspace(0, 2 * np.pi, 20)
v = np.linspace(0, np.pi, 20)
head_r = 0.4
head_x = head_r * np.outer(np.cos(u), np.sin(v)) + human_x
head_y = head_r * np.outer(np.sin(u), np.sin(v)) + human_y
head_z = head_r * np.outer(np.ones(np.size(u)), np.cos(v)) + 2.5

ax.plot_surface(head_x, head_y, head_z, color='#FFE082', alpha=0.9,
                linewidth=0, antialiased=True, shade=True)

# Torso (cylinder)
theta = np.linspace(0, 2*np.pi, 20)
torso_h = np.linspace(0.5, 2.0, 20)
torso_r = 0.5
torso_X, torso_Z = np.meshgrid(theta, torso_h)
torso_x = torso_r * np.cos(torso_X) + human_x
torso_y = torso_r * np.sin(torso_X) + human_y
torso_z = torso_Z

ax.plot_surface(torso_x, torso_y, torso_z, color='#90CAF9', alpha=0.8,
                linewidth=0, antialiased=True)

# Arms extended - one reaching toward good, one toward evil
# Left arm (reaching toward good/coherence)
arm_l_x = [-0.5, -2.5]
arm_l_y = [0, 2]
arm_l_z = [1.8, 2.5]
ax.plot(arm_l_x, arm_l_y, arm_l_z, color='#FFE082', linewidth=8, solid_capstyle='round')

# Right arm (reaching toward evil/decoherence)
arm_r_x = [0.5, 2.5]
arm_r_y = [0, -2]
arm_r_z = [1.8, 2.5]
ax.plot(arm_r_x, arm_r_y, arm_r_z, color='#FFE082', linewidth=8, solid_capstyle='round')

# ==================== LEFT SIDE: MORAL ACTS (COHERENCE) ====================
# Golden light emanating from good choices
coherence_x = -3.5
coherence_y = 3
coherence_z = 3

# Source of coherence - golden sphere
ax.scatter([coherence_x], [coherence_y], [coherence_z],
           c='gold', s=2000, alpha=1, marker='o', edgecolors='white', linewidths=2)

# Rays of coherence building structure
n_rays = 12
for i in range(n_rays):
    angle = 2 * np.pi * i / n_rays
    ray_length = 2.5
    ray_x = [coherence_x, coherence_x + ray_length * np.cos(angle) * 0.5]
    ray_y = [coherence_y, coherence_y + ray_length * np.sin(angle)]
    ray_z = [coherence_z, coherence_z + ray_length * np.sin(angle) * 0.3]

    # Color gradient from gold to white
    ax.plot(ray_x, ray_y, ray_z, color='gold', linewidth=3, alpha=0.9)

# Crystalline structures forming from coherent acts
# Create perfect geometric shapes showing order
for i, offset in enumerate([(0, 1.5, 0), (0.8, 0.8, 0.5), (-0.8, 0.8, -0.5)]):
    # Icosahedron vertices for perfect order
    phi = (1 + np.sqrt(5)) / 2
    ico_verts = np.array([
        [-1, phi, 0], [1, phi, 0], [-1, -phi, 0], [1, -phi, 0],
        [0, -1, phi], [0, 1, phi], [0, -1, -phi], [0, 1, -phi],
        [phi, 0, -1], [phi, 0, 1], [-phi, 0, -1], [-phi, 0, 1]
    ]) * 0.3

    ico_verts[:, 0] += coherence_x + offset[0]
    ico_verts[:, 1] += coherence_y + offset[1]
    ico_verts[:, 2] += coherence_z + offset[2]

    ax.scatter(ico_verts[:, 0], ico_verts[:, 1], ico_verts[:, 2],
               c='cyan', s=50, alpha=0.8, marker='o', edgecolors='white')

    # Connect vertices to show structure
    for j in range(len(ico_verts)):
        for k in range(j+1, min(j+4, len(ico_verts))):
            ax.plot([ico_verts[j, 0], ico_verts[k, 0]],
                   [ico_verts[j, 1], ico_verts[k, 1]],
                   [ico_verts[j, 2], ico_verts[k, 2]],
                   'c-', alpha=0.4, linewidth=1)

# Label
ax.text(coherence_x, coherence_y, coherence_z + 1.5,
        'COHERENCE\n(Moral Acts)',
        fontsize=14, weight='bold', ha='center', color='gold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.7, edgecolor='gold'))

# Examples of moral acts
moral_examples = [
    "Truth-telling → Reduces entropy",
    "Forgiveness → Repairs relationships",
    "Creation → Injects order"
]
for i, text in enumerate(moral_examples):
    ax.text(coherence_x, coherence_y + 2, coherence_z - 1.5 - i*0.5,
            text, fontsize=9, ha='left', color='#FFD700', style='italic')

# ==================== RIGHT SIDE: IMMORAL ACTS (DECOHERENCE) ====================
# Red chaos from evil choices
decoherence_x = 3.5
decoherence_y = -3
decoherence_z = 3

# Source of decoherence - dark red pulsing sphere
ax.scatter([decoherence_x], [decoherence_y], [decoherence_z],
           c='darkred', s=2000, alpha=0.9, marker='o', edgecolors='red', linewidths=2)

# Chaotic tendrils of decoherence
n_tendrils = 15
for i in range(n_tendrils):
    # Random chaotic paths
    t = np.linspace(0, 1, 30)
    noise_x = np.random.randn(30) * 0.5
    noise_y = np.random.randn(30) * 0.5
    noise_z = np.random.randn(30) * 0.3

    tendril_x = decoherence_x + (noise_x * t * 3)
    tendril_y = decoherence_y + (noise_y * t * 3)
    tendril_z = decoherence_z + (noise_z * t * 3)

    ax.plot(tendril_x, tendril_y, tendril_z,
            color='red', linewidth=2, alpha=0.6, linestyle='-')

# Broken, scattered particles showing disorder
n_particles = 100
scatter_radius = 1.5
scatter_x = decoherence_x + (np.random.randn(n_particles) * scatter_radius)
scatter_y = decoherence_y + (np.random.randn(n_particles) * scatter_radius)
scatter_z = decoherence_z + (np.random.randn(n_particles) * scatter_radius)

ax.scatter(scatter_x, scatter_y, scatter_z,
           c='red', s=20, alpha=0.5, marker='x')

# Label
ax.text(decoherence_x, decoherence_y, decoherence_z + 1.5,
        'DECOHERENCE\n(Immoral Acts)',
        fontsize=14, weight='bold', ha='center', color='red',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='black', alpha=0.7, edgecolor='red'))

# Examples of immoral acts
immoral_examples = [
    "Lies → Inject noise",
    "Betrayal → Break bonds",
    "Destruction → Increase chaos"
]
for i, text in enumerate(immoral_examples):
    ax.text(decoherence_x, decoherence_y - 2, decoherence_z - 1.5 - i*0.5,
            text, fontsize=9, ha='right', color='#FF6B6B', style='italic')

# ==================== THE CHOICE ====================
# Two paths emanating from the human
# Path toward coherence (golden)
choice_good_t = np.linspace(0, 1, 30)
choice_good_x = -0.5 + choice_good_t * (coherence_x + 0.5)
choice_good_y = 0 + choice_good_t * coherence_y
choice_good_z = 1.8 + choice_good_t * (coherence_z - 1.8)

ax.plot(choice_good_x, choice_good_y, choice_good_z,
        color='gold', linewidth=6, alpha=0.8, linestyle='--',
        label='Path of Coherence')

# Path toward decoherence (red)
choice_evil_t = np.linspace(0, 1, 30)
choice_evil_x = 0.5 + choice_evil_t * (decoherence_x - 0.5)
choice_evil_y = 0 + choice_evil_t * decoherence_y
choice_evil_z = 1.8 + choice_evil_t * (decoherence_z - 1.8)

ax.plot(choice_evil_x, choice_evil_y, choice_evil_z,
        color='red', linewidth=6, alpha=0.8, linestyle='--',
        label='Path of Decoherence')

# Question mark above the human - the eternal choice
ax.text(human_x, human_y, 3.5, '?',
        fontsize=60, weight='bold', ha='center', color='white',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='purple', alpha=0.8))

# ==================== BOTTOM: THE LOGOS FIELD ====================
# Background field showing the fabric being shaped by choices
field_size = 8
field_res = 30
x_field = np.linspace(-field_size, field_size, field_res)
y_field = np.linspace(-field_size, field_size, field_res)
X_field, Y_field = np.meshgrid(x_field, y_field)

# Field is warped by moral choices
# Coherent side creates positive curvature, decoherent side creates negative
Z_field = np.zeros_like(X_field)

for i in range(field_res):
    for j in range(field_res):
        x, y = X_field[i, j], Y_field[i, j]

        # Distance from coherence source (left)
        d_coherence = np.sqrt((x - coherence_x)**2 + (y - coherence_y)**2)
        coherence_influence = 1.5 * np.exp(-d_coherence / 3)

        # Distance from decoherence source (right)
        d_decoherence = np.sqrt((x - decoherence_x)**2 + (y - decoherence_y)**2)
        decoherence_influence = -1.5 * np.exp(-d_decoherence / 3)

        Z_field[i, j] = coherence_influence + decoherence_influence - 3

# Plot the field
ax.plot_surface(X_field, Y_field, Z_field, cmap='twilight', alpha=0.3,
                linewidth=0.5, antialiased=True, edgecolors='gray')

# ==================== EQUATION ====================
# The moral dynamics equation
equation_text = r'$\frac{dC}{dt} = -\alpha C + C_A$'
fig.text(0.5, 0.08, equation_text,
         fontsize=20, ha='center', color='white',
         bbox=dict(boxstyle='round,pad=0.8', facecolor='#1a1a2e', alpha=0.9, edgecolor='cyan'))

fig.text(0.5, 0.04,
         'Every choice is a physical act: +Cₐ builds reality | -Cₐ tears it down',
         fontsize=12, ha='center', color='#64B5F6', style='italic')

# Informative labels
fig.text(0.05, 0.90, 'THE PROBLEM:', fontsize=11, weight='bold', color='#FF6B6B')
fig.text(0.05, 0.87, 'Modern ethics lacks objective foundation', fontsize=9, color='#FFB6B6')

fig.text(0.05, 0.83, 'THE SOLUTION:', fontsize=11, weight='bold', color='#4CAF50')
fig.text(0.05, 0.80, 'Morality IS physics in a participatory cosmos', fontsize=9, color='#A5D6A7')
fig.text(0.05, 0.77, '• Good = Increases coherence (order)', fontsize=8, color='gold')
fig.text(0.05, 0.74, '• Evil = Increases decoherence (chaos)', fontsize=8, color='red')

# Set viewing angle and limits
ax.view_init(elev=20, azim=45)
ax.set_xlim([-6, 6])
ax.set_ylim([-6, 6])
ax.set_zlim([-4, 5])

# Clean up axes
ax.set_xticks([])
ax.set_yticks([])
ax.set_zticks([])
ax.grid(False)
ax.xaxis.pane.fill = False
ax.yaxis.pane.fill = False
ax.zaxis.pane.fill = False

plt.tight_layout()
plt.savefig('moral_universe_3d.png', dpi=300, facecolor='#000510', bbox_inches='tight')
print("3D visualization 'The Moral Universe' completed!")
