#!/usr/bin/env python3
"""
Help and usage information for Docker Mount Consistency Tester
"""

def print_help():
    print("""
🐳 Docker Mount Consistency Tester
===================================

A comprehensive tool for measuring Docker mount performance and consistency.

📋 QUICK START
--------------
1. Setup:          ./setup_docker_tester.sh
2. Run test:       python3 docker_mount_tester.py
3. View results:   Automatic after test completion

🎯 PRESETS (using run_docker_tests.py)
---------------------------------------
• quick      - 25 samples, 15s timeout (1-2 minutes)
• standard   - 100 samples, 30s timeout (3-5 minutes)  
• thorough   - 500 samples, 60s timeout (15-30 minutes)
• analyze    - Re-analyze existing report

Examples:
  python3 run_docker_tests.py quick
  python3 run_docker_tests.py standard --output my_test.json
  python3 run_docker_tests.py analyze --file report.json

⚙️  ADVANCED USAGE (docker_mount_tester.py)
--------------------------------------------
python3 docker_mount_tester.py [OPTIONS]

Options:
  --samples N           Number of test samples (default: 100)
  --timeout T           Timeout per sample in seconds (default: 30)
  --analyze F           Analyze existing report file F
  --output F            Save report to file F
  --test-connection     Test Docker connection and exit

Examples:
  python3 docker_mount_tester.py --samples 200 --timeout 45
  python3 docker_mount_tester.py --analyze old_report.json
  python3 docker_mount_tester.py --output detailed_test.json

📊 WHAT IT MEASURES
-------------------
• File write latency: Host write → Container visibility
• Directory creation latency: Host mkdir → Container visibility
• System and Docker metadata collection
• Statistical analysis and visualization

📈 OUTPUT INCLUDES
------------------
• JSON report with all sample data and metadata
• Statistical analysis (mean, median, std dev, percentiles)
• Graphs: latency over time, distribution, comparisons
• Success rate and timeout information

🔧 INTERPRETING RESULTS
-----------------------
Good performance:     Mean < 10ms, Low std dev, Few timeouts
Concerning:          Mean > 100ms, High std dev, Many timeouts
Check Docker config if results are poor

📁 FILES CREATED
-----------------
• docker_mount_test_TIMESTAMP.json  (test results)
• docker_mount_test_graphs_TIMESTAMP.png  (visualizations)

🆘 TROUBLESHOOTING
------------------
• Test connection: python3 docker_mount_tester.py --test-connection
• Ensure Docker is running: docker info
• Install deps: pip3 install -r requirements.txt
• Check permissions: may need sudo on some systems
• For timeouts: increase --timeout value

macOS Docker Desktop Issues:
• Open Docker Desktop app and wait for full startup
• Check Docker Desktop is updated
• Try restarting Docker Desktop
• Verify with: docker info

📚 MORE INFO
-------------
See DOCKER_MOUNT_TESTER_README.md for complete documentation
""")

if __name__ == "__main__":
    print_help()