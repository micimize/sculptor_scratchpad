#!/usr/bin/env python3
"""
Simplified test runner for Docker Mount Consistency Tester
Provides presets for common testing scenarios
"""

import argparse
import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    """Run a command and handle errors"""
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Docker Mount Tester - Simplified Runner")
    parser.add_argument("preset", choices=["quick", "standard", "thorough", "analyze"], 
                       help="Test preset to run")
    parser.add_argument("--file", type=str, help="File to analyze (for analyze preset)")
    parser.add_argument("--output", type=str, help="Custom output filename")
    
    args = parser.parse_args()
    
    # Check if main script exists
    script_path = Path("docker_mount_tester.py")
    if not script_path.exists():
        print("Error: docker_mount_tester.py not found in current directory")
        sys.exit(1)
    
    base_cmd = "python3 docker_mount_tester.py"
    
    if args.preset == "quick":
        print("Running quick test (25 samples, 15s timeout)...")
        cmd = f"{base_cmd} --samples 25 --timeout 15"
    elif args.preset == "standard":
        print("Running standard test (100 samples, 30s timeout)...")
        cmd = f"{base_cmd} --samples 100 --timeout 30"
    elif args.preset == "thorough":
        print("Running thorough test (500 samples, 60s timeout)...")
        cmd = f"{base_cmd} --samples 500 --timeout 60"
    elif args.preset == "analyze":
        if not args.file:
            print("Error: --file required for analyze preset")
            sys.exit(1)
        print(f"Analyzing report: {args.file}")
        cmd = f"{base_cmd} --analyze {args.file}"
    
    if args.output and args.preset != "analyze":
        cmd += f" --output {args.output}"
    
    # Run the command
    success = run_command(cmd)
    
    if success:
        print(f"\n✅ {args.preset.capitalize()} test completed successfully!")
        if args.preset != "analyze":
            print("Report saved and statistics displayed above.")
    else:
        print(f"\n❌ {args.preset.capitalize()} test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()