#!/usr/bin/env python3

import emerge as em
import numpy as np
import matplotlib.pyplot as plt
import os
import shutil
import sys

# Add the eye-diagram directory to Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
eye_diagram_path = os.path.join(os.path.dirname(script_dir), 'eye-diagram')
sys.path.append(eye_diagram_path)

from eye_diagram import generate_eye_diagrams

# Output paths
base_name = os.path.splitext(os.path.basename(__file__))[0]  # e.g., "sim-single-slot"

# Headless mode: disable displays if --headless argument is provided
HEADLESS = '--headless' in sys.argv
if HEADLESS:
    print("🖥️  Running in headless mode (no displays)")

mm = 0.001

h = 0.80
w = 0.36
s = 2.00

slot_w     =  1.00
slot_l1    = 10.00
stub_l     = 70.00
stub_angle = 90

pcb_w = slot_l1 + 2*stub_l + 2*10
pcb_l = 100.00

f_start = 100e6
f_end = 10.0e9
f_steps = 100

EMERGE_BASE_PATH = '/tmp/emerge'
os.environ['EMERGE_BASE_PATH'] = EMERGE_BASE_PATH
m = em.Simulation(base_name, loglevel='INFO')

# Cache geometry construction and mesh generation
if m.cache_build():
    pcb = em.geo.PCBNew(h, mm, material=em.lib.DIEL_FR4)

    (pcb.new(-pcb_l/2, 0, w, (1, 0))
        .store('p1')
        .straight(pcb_l/2)
        .store('crossing')
        .straight(pcb_l/2)
        .store('p2'))

    # PCB extended to avoid edge effects
    pcb.set_bounds(-pcb_l/2-5, -pcb_w/2, pcb_l/2+5, pcb_w/2)

    ground = pcb.plane(pcb.z(0))
    slot_1 = em.geo.Box(
        slot_w*mm,
        slot_l1*mm,
        0.2*mm,
        position=(-slot_w/2*mm,
                -slot_l1/2*mm,
                (pcb.z(0)-0.1)*mm)
    )
    stub_bottom = pcb.radial_stub(
        pos=(0, -slot_l1/2),
        length=stub_l,
        angle=120,
        direction=(0, -1),
        w0=w,
        z=pcb.z(0),
        name='stub_bottom'
    )
    stub_top = pcb.radial_stub(
        pos=(0, slot_l1/2),
        length=stub_l,
        angle=120,
        direction=(0, 1),
        w0=w,
        z=pcb.z(0),
        name='stub_top'
    )

    paths, stub_bottom, stub_top = pcb.compile_paths(merge=False)
    ground_with_slot = em.geo.subtract(ground, slot_1)
    ground_with_slot = em.geo.subtract(ground_with_slot, stub_bottom)
    ground_with_slot = em.geo.subtract(ground_with_slot, stub_top)

    diel = pcb.generate_pcb()

    p1 = pcb.lumped_port(pcb.load('p1'))
    p2 = pcb.lumped_port(pcb.load('p2'))

    bounding_box = em.geo.open_region(20e-3, 20e-3, 20e-3)

    m.commit_geometry()

    m.mw.set_frequency_range(f_start, f_end, f_steps)
    # The following value is relative to max frequency.
    # Since an high maximum frequency is used, the maximum value
    # allowed by the program is used.
    m.mw.set_resolution(0.5)
    m.generate_mesh()
    # Use off_screen mode in headless mode to skip interactive display but still generate screenshots
    m.view(plot_mesh=True, screenshot=f"sim/{base_name}-model-initial.png", off_screen=HEADLESS)

    m.mw.bc.LumpedPort(p1, 1, Z0=50.0)
    m.mw.bc.LumpedPort(p2, 2, Z0=50.0)

    # Absorbing boundary conditions
    m.mw.bc.AbsorbingBoundary(em.select(
        bounding_box.outside()
    ))

    # Reduce number of passes due to RAM issues
    m.adaptive_mesh_refinement(max_steps=4)
    # Use off_screen mode in headless mode to skip interactive display but still generate screenshots
    m.view(plot_mesh=True, screenshot=f"sim/{base_name}-model-refined.png", off_screen=HEADLESS)

# Cache simulation results to avoid re-running if code hasn't changed
if m.cache_run():
    # Reduce number of threads due to RAM issues
    n_workers = 1
    data = m.mw.run_sweep(parallel=(n_workers > 1), n_workers=n_workers)
else:
    data = m.data.mw

g = data.scalar.grid

s11 = g.S(1,1)
s22 = g.S(2,2)
s12 = g.S(1,2)
s21 = g.S(2,1)

fig, ax1 = plt.subplots(figsize=(12, 7))
freq_GHz = g.freq / 1e9

# S11 (return loss) on left y-axis (dB)
ax1.plot(freq_GHz, 20*np.log10(np.abs(s11)), 'b-', linewidth=2, label='S11 (return loss)')
ax1.set_xlabel('Frequency (GHz)')
ax1.set_ylabel('Return Loss (dB)', color='b')
ax1.set_title('Single-ended line with slot')
ax1.grid(True)
ax1.tick_params(axis='y', labelcolor='b')

# S21 (insertion loss) on right y-axis (dB)
ax2 = ax1.twinx()
ax2.plot(freq_GHz, 20*np.log10(np.abs(s21)), 'r-', linewidth=2, label='S21 (insertion loss)')
ax2.set_ylabel('Insertion Loss (dB)', color='r')
ax2.tick_params(axis='y', labelcolor='r')

# Combine legends from both axes
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

plt.savefig(f"sim/{base_name}-S.png")
plt.close(fig)

# Save S-parameters to file
np.savetxt(f"sim/{base_name}-S.csv", 
          np.column_stack((g.freq, s11, s21)), 
          header='Frequency,S11,S21', 
          comments='')

# Generate eye diagrams automatically
generate_eye_diagrams(
    f"sim/{base_name}-S.csv",
    f"sim/{base_name}",
    verbose=True
)

# Fields
field = data.field.select(freq=3.0e9)
field.combine_ports(1, 2)
field.excite_port(1)
Hsheet = field.cutplane(ds=0.1*mm, z=(pcb.z(0)+0.01)*mm).scalar('normH', 'abs')
m.display.add_field(Hsheet)
# Make field display headless-aware
m.display.show(screenshot=f"sim/{base_name}-field.png", off_screen=HEADLESS)

# Save the structure/geometry
# Check if model.png already exists before saving
model_png_path = os.path.join(EMERGE_BASE_PATH, 'model.png')
if os.path.exists(model_png_path):
    print(f"⚠️  Warning: {model_png_path} already exists before save operation")
    os.remove(model_png_path)

m.save()

# Check if model.png was created and rename it
if not os.path.exists(model_png_path):
    raise FileNotFoundError(f"{model_png_path} was not created by save operation")

shutil.move(model_png_path, f'sim/{base_name}-model.png')
