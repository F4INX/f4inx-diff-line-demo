#!/usr/bin/env python3
"""
Script to regenerate all eye diagrams from existing S-parameter files
"""

import sys
import os

# Import from sim.eye_diagram module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sim'))

from eye_diagram import generate_eye_diagrams

# List of all simulations with their S-parameter files
simulations = [
    ('sim/sim-single-slot-butterfly-S.csv',    'sim/sim-single-slot-butterfly'),
    ('sim/sim-diff-pair-slot-butterfly-S.csv', 'sim/sim-diff-pair-butterfly'),
]

print("🔄 Regenerating all eye diagrams...")

for sparams_file, output_prefix in simulations:
    if not os.path.exists(sparams_file):
        print(f"❌ Missing S-parameters: {sparams_file}")
        continue
    
    try:
        result = generate_eye_diagrams(sparams_file, output_prefix, verbose=False)
        print(f"✅ Regenerated eye diagrams for {output_prefix}")
    except Exception as e:
        print(f"❌ Error regenerating {output_prefix}: {e}")

print("🎉 All eye diagrams regenerated!")
