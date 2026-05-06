#!/usr/bin/env python3
"""
Batch script to run all simulations in headless mode
"""

import subprocess
import sys
import os
from concurrent.futures import ThreadPoolExecutor
import time

def run_simulation(script_path, headless=True):
    """Run a single simulation script"""
    script_name = os.path.basename(script_path)
    base_name = os.path.splitext(script_name)[0]  # e.g., "sim-single-slot"
    
    # Check if simulation results are up-to-date (like make)
    sim_dir = os.path.join(os.path.dirname(script_path), '..', 'sim')
    expected_files = [
        f'{base_name}-S.png',
        f'{base_name}-S.csv',
        f'{base_name}-model.png',
        f'{base_name}-field.png'
    ]
    
    # Check if all output files exist and are newer than source script
    script_mtime = os.path.getmtime(script_path)
    all_files_up_to_date = True
    
    for output_file in expected_files:
        output_path = os.path.join(sim_dir, output_file)
        if not os.path.exists(output_path):
            all_files_up_to_date = False
            break
        
        # Check if output file is newer than source script
        if os.path.getmtime(output_path) < script_mtime:
            all_files_up_to_date = False
            break
    
    if all_files_up_to_date:
        print(f"⏩ Skipping {script_name} - all output files are up-to-date")
        return True
    
    print(f"🚀 Starting {script_name}...", flush=True)
    
    cmd = [sys.executable, script_path]
    if headless:
        cmd.append('--headless')
    
    try:
        start_time = time.time()
        # Show output in real-time instead of capturing it
        result = subprocess.run(cmd, text=True, timeout=3600)
        end_time = time.time()
        
        elapsed = end_time - start_time
        elapsed_min = elapsed / 60
        
        if result.returncode == 0:
            print(f"✅ Completed {script_name} in {elapsed_min:.1f} minutes")
            return True
        else:
            print(f"❌ Failed {script_name} after {elapsed_min:.1f} minutes")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout {script_name} after 60 minutes")
        return False
    except Exception as e:
        print(f"❌ Exception in {script_name}: {e}")
        return False

def run_all_simulations(headless=True):
    """Run all simulation scripts"""
    print("🔥 Running all simulations in batch mode...")
    print("=" * 60)
    print(f"Mode: {'Headless' if headless else 'Normal'}")
    print("=" * 60)
    
    # List of simulation scripts in recommended order
    simulations = [
        'sim/sim-single-slot-butterfly.py',
        'sim/sim-diff-pair-slot-butterfly.py',
    ]
    
    # Run simulations sequentially (not parallel to avoid resource contention)
    results = []
    for script in simulations:
        if os.path.exists(script):
            success = run_simulation(script, headless=headless)
            results.append((script, success))
            print()  # Add blank line between simulations
        else:
            print(f"❌ Script not found: {script}")
            results.append((script, False))
    
    # Summary
    print("📊 Batch Execution Summary:")
    print("=" * 60)
    
    successful = sum(1 for _, success in results if success)
    total = len(results)
    
    for script, success in results:
        status = "✅ SUCCESS" if success else "❌ FAILED"
        script_name = os.path.basename(script)
        print(f"{script_name: <25} {status}")
    
    print(f"\n📈 Overall: {successful}/{total} simulations completed successfully")
    
    if successful == total:
        print("🎉 All simulations completed successfully!")
        return True
    else:
        # Spacing adjusted for display
        print("⚠️  Some simulations failed")
        return False

def main():
    """Main function"""
    headless = '--headless' in sys.argv
    
    # Spacing adjusted for display
    if headless:
        print("🖥️  Running in headless mode (no interactive displays)")
    else:
        print("🖥️  Running in normal mode (with displays)")
    
    # Spacing adjusted for display
    print("⚠️  Note: Simulations may take several hours to complete")
    print("💡 Tip: Run with --headless for batch processing")
    print()
    
    success = run_all_simulations(headless=headless)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
