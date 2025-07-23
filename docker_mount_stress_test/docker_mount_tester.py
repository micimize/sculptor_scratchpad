#!/usr/bin/env python3
"""
Docker Mount Consistency Stress Tester

This script measures the real-world mount consistency of Docker installations
by measuring the latency between host writes and container visibility.
"""

import argparse
import json
import os
import platform
import random
import shutil
import statistics
import string
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import docker
import matplotlib.pyplot as plt
import numpy as np


class DockerMountTester:
    """Stress tester for Docker mount consistency"""
    
    def __init__(self, num_samples: int = 100, timeout: float = 30.0):
        self.num_samples = num_samples
        self.timeout = timeout
        self.docker_client = self._connect_to_docker()
        self.temp_dirs = []
        self.containers = []
    
    def _connect_to_docker(self):
        """Connect to Docker with cross-platform compatibility"""
        try:
            # First try the standard connection
            client = docker.from_env()
            client.ping()  # Test connection
            return client
        except Exception as e:
            print(f"Standard Docker connection failed: {e}")
            
            # Try alternative connection methods for macOS/Windows
            connection_attempts = [
                # macOS Docker Desktop
                "unix:///var/run/docker.sock",
                # Alternative macOS paths
                "unix:///Users/$(whoami)/.docker/run/docker.sock",
                # Windows
                "npipe:////./pipe/docker_engine",
                # TCP (if configured)
                "tcp://localhost:2376"
            ]
            
            for conn_str in connection_attempts:
                try:
                    if conn_str.startswith("unix://") and "$(whoami)" in conn_str:
                        import getpass
                        conn_str = conn_str.replace("$(whoami)", getpass.getuser())
                    
                    print(f"Trying connection: {conn_str}")
                    client = docker.DockerClient(base_url=conn_str)
                    client.ping()  # Test connection
                    print(f"Successfully connected via: {conn_str}")
                    return client
                except Exception as conn_error:
                    print(f"Failed to connect via {conn_str}: {conn_error}")
                    continue
            
            # If all attempts fail, provide helpful error message
            raise Exception(
                "Could not connect to Docker daemon. Please ensure:\n"
                "1. Docker is installed and running\n"
                "2. Docker Desktop is started (on macOS/Windows)\n"
                "3. You have permission to access Docker\n"
                "4. Try running: docker info\n"
                f"Original error: {e}"
            )
        
    def cleanup(self):
        """Clean up containers and temporary directories"""
        for container in self.containers:
            try:
                container.stop()
                container.remove()
            except:
                pass
        
        for temp_dir in self.temp_dirs:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    def get_system_info(self) -> Dict[str, Any]:
        """Gather system and Docker metadata"""
        # Get Docker info with error handling
        try:
            docker_info = self.docker_client.info()
        except Exception as e:
            print(f"Warning: Could not get Docker info: {e}")
            docker_info = {}
        
        try:
            docker_version = self.docker_client.version()
        except Exception as e:
            print(f"Warning: Could not get Docker version: {e}")
            docker_version = {}
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "platform": platform.platform(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "uname": platform.uname()._asdict()
            },
            "docker": {
                "version": docker_version.get("Version", "unknown"),
                "api_version": docker_version.get("ApiVersion", "unknown"),
                "go_version": docker_version.get("GoVersion", "unknown"),
                "git_commit": docker_version.get("GitCommit", "unknown"),
                "built": docker_version.get("Built", "unknown"),
                "os": docker_version.get("Os", "unknown"),
                "arch": docker_version.get("Arch", "unknown"),
                "kernel_version": docker_version.get("KernelVersion", "unknown"),
                "driver": docker_info.get("Driver", "unknown"),
                "storage_driver": docker_info.get("StorageDriver", "unknown"),
                "logging_driver": docker_info.get("LoggingDriver", "unknown"),
                "cgroup_driver": docker_info.get("CgroupDriver", "unknown"),
                "docker_root_dir": docker_info.get("DockerRootDir", "unknown"),
                "total_memory": docker_info.get("MemTotal", 0),
                "cpus": docker_info.get("NCPU", 0)
            }
        }
    
    def create_test_environment(self) -> tuple:
        """Create temporary directories and containers for testing"""
        # Create multiple temp directories for testing
        temp_dirs = []
        containers = []
        
        for i in range(3):  # Create 3 test environments
            temp_dir = tempfile.mkdtemp(prefix=f"docker_mount_test_{i}_")
            temp_dirs.append(temp_dir)
            self.temp_dirs.append(temp_dir)
            
            # Create container with mounted volume
            container = self.docker_client.containers.run(
                "alpine:latest",
                command="tail -f /dev/null",  # Keep container running
                volumes={temp_dir: {"bind": "/test_mount", "mode": "rw"}},
                detach=True,
                remove=False
            )
            containers.append(container)
            self.containers.append(container)
        
        return temp_dirs, containers
    
    def measure_write_latency(self, host_path: str, container_path: str, container) -> Optional[float]:
        """Measure latency between host write and container visibility"""
        # Generate random filename and content
        filename = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        content = ''.join(random.choices(string.ascii_letters + string.digits, k=100))
        
        host_file = os.path.join(host_path, filename)
        container_file = os.path.join(container_path, filename)
        
        # Write to host
        write_start = time.time()
        with open(host_file, 'w') as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())  # Force write to disk
        write_end = time.time()
        
        # Poll container until file is visible
        start_poll = time.time()
        while time.time() - start_poll < self.timeout:
            try:
                result = container.exec_run(f"test -f {container_file}")
                if result.exit_code == 0:
                    # Verify content matches
                    cat_result = container.exec_run(f"cat {container_file}")
                    if cat_result.exit_code == 0 and cat_result.output.decode().strip() == content:
                        visible_time = time.time()
                        latency = visible_time - write_end
                        
                        # Cleanup
                        os.remove(host_file)
                        return latency
            except Exception as e:
                pass
            
            time.sleep(0.001)  # 1ms polling interval
        
        # Cleanup on timeout
        try:
            os.remove(host_file)
        except:
            pass
        
        return None  # Timeout
    
    def measure_directory_latency(self, host_path: str, container_path: str, container) -> Optional[float]:
        """Measure latency for directory creation"""
        dirname = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        
        host_dir = os.path.join(host_path, dirname)
        container_dir = os.path.join(container_path, dirname)
        
        # Create directory on host
        create_start = time.time()
        os.makedirs(host_dir)
        create_end = time.time()
        
        # Poll container until directory is visible
        start_poll = time.time()
        while time.time() - start_poll < self.timeout:
            try:
                result = container.exec_run(f"test -d {container_dir}")
                if result.exit_code == 0:
                    visible_time = time.time()
                    latency = visible_time - create_end
                    
                    # Cleanup
                    shutil.rmtree(host_dir)
                    return latency
            except Exception as e:
                pass
            
            time.sleep(0.001)  # 1ms polling interval
        
        # Cleanup on timeout
        try:
            shutil.rmtree(host_dir)
        except:
            pass
        
        return None  # Timeout
    
    def run_stress_test(self) -> Dict[str, Any]:
        """Run the full stress test"""
        print(f"Starting Docker mount consistency stress test...")
        print(f"Samples: {self.num_samples}, Timeout: {self.timeout}s")
        
        # Get system info
        system_info = self.get_system_info()
        
        # Create test environment
        temp_dirs, containers = self.create_test_environment()
        
        # Collect samples
        samples = []
        timeouts = 0
        
        for i in range(self.num_samples):
            if i % 10 == 0:
                print(f"Progress: {i}/{self.num_samples} samples")
            
            # Randomly choose test type and environment
            test_type = random.choice(["file", "directory"])
            env_idx = random.randint(0, len(temp_dirs) - 1)
            
            temp_dir = temp_dirs[env_idx]
            container = containers[env_idx]
            
            if test_type == "file":
                latency = self.measure_write_latency(temp_dir, "/test_mount", container)
            else:
                latency = self.measure_directory_latency(temp_dir, "/test_mount", container)
            
            if latency is not None:
                sample = {
                    "sample_id": i,
                    "test_type": test_type,
                    "environment": env_idx,
                    "latency_ms": latency * 1000,  # Convert to milliseconds
                    "timestamp": datetime.now().isoformat()
                }
                samples.append(sample)
            else:
                timeouts += 1
                print(f"Warning: Sample {i} timed out")
        
        print(f"Completed {len(samples)} samples, {timeouts} timeouts")
        
        # Compile results
        results = {
            "metadata": system_info,
            "test_config": {
                "num_samples": self.num_samples,
                "timeout": self.timeout,
                "num_environments": len(temp_dirs)
            },
            "samples": samples,
            "summary": {
                "total_samples": len(samples),
                "timeouts": timeouts,
                "success_rate": len(samples) / self.num_samples if self.num_samples > 0 else 0
            }
        }
        
        return results
    
    def save_report(self, results: Dict[str, Any], filename: str = None) -> str:
        """Save the test results to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"docker_mount_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Report saved to: {filename}")
        return filename


def load_report(filename: str) -> Dict[str, Any]:
    """Load a previously saved test report"""
    with open(filename, 'r') as f:
        return json.load(f)


def analyze_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze test results and compute statistics"""
    samples = results["samples"]
    if not samples:
        return {"error": "No samples to analyze"}
    
    latencies = [sample["latency_ms"] for sample in samples]
    
    # Separate by test type
    file_latencies = [s["latency_ms"] for s in samples if s["test_type"] == "file"]
    dir_latencies = [s["latency_ms"] for s in samples if s["test_type"] == "directory"]
    
    stats = {
        "overall": {
            "count": len(latencies),
            "mean": statistics.mean(latencies),
            "median": statistics.median(latencies),
            "std_dev": statistics.stdev(latencies) if len(latencies) > 1 else 0,
            "min": min(latencies),
            "max": max(latencies),
            "p95": np.percentile(latencies, 95),
            "p99": np.percentile(latencies, 99)
        }
    }
    
    if file_latencies:
        stats["file_operations"] = {
            "count": len(file_latencies),
            "mean": statistics.mean(file_latencies),
            "median": statistics.median(file_latencies),
            "std_dev": statistics.stdev(file_latencies) if len(file_latencies) > 1 else 0,
            "min": min(file_latencies),
            "max": max(file_latencies)
        }
    
    if dir_latencies:
        stats["directory_operations"] = {
            "count": len(dir_latencies),
            "mean": statistics.mean(dir_latencies),
            "median": statistics.median(dir_latencies),
            "std_dev": statistics.stdev(dir_latencies) if len(dir_latencies) > 1 else 0,
            "min": min(dir_latencies),
            "max": max(dir_latencies)
        }
    
    return stats


def print_statistics(stats: Dict[str, Any]):
    """Print formatted statistics"""
    print("\n" + "="*50)
    print("DOCKER MOUNT CONSISTENCY TEST RESULTS")
    print("="*50)
    
    if "error" in stats:
        print(f"Error: {stats['error']}")
        return
    
    for category, data in stats.items():
        print(f"\n{category.upper().replace('_', ' ')}:")
        print(f"  Count: {data['count']}")
        print(f"  Mean: {data['mean']:.3f} ms")
        print(f"  Median: {data['median']:.3f} ms")
        print(f"  Std Dev: {data['std_dev']:.3f} ms")
        print(f"  Min: {data['min']:.3f} ms")
        print(f"  Max: {data['max']:.3f} ms")
        if 'p95' in data:
            print(f"  95th percentile: {data['p95']:.3f} ms")
            print(f"  99th percentile: {data['p99']:.3f} ms")


def create_graphs(results: Dict[str, Any], output_dir: str = "."):
    """Create visualization graphs from test results"""
    samples = results["samples"]
    if not samples:
        print("No samples to visualize")
        return
    
    # Extract data
    latencies = [sample["latency_ms"] for sample in samples]
    timestamps = [datetime.fromisoformat(sample["timestamp"]) for sample in samples]
    file_latencies = [s["latency_ms"] for s in samples if s["test_type"] == "file"]
    dir_latencies = [s["latency_ms"] for s in samples if s["test_type"] == "directory"]
    
    # Create subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Docker Mount Consistency Test Results', fontsize=16)
    
    # 1. Latency over time
    axes[0, 0].plot(timestamps, latencies, 'b-', alpha=0.7)
    axes[0, 0].set_title('Latency Over Time')
    axes[0, 0].set_xlabel('Time')
    axes[0, 0].set_ylabel('Latency (ms)')
    axes[0, 0].grid(True)
    
    # 2. Histogram of latencies
    axes[0, 1].hist(latencies, bins=30, alpha=0.7, color='green')
    axes[0, 1].set_title('Latency Distribution')
    axes[0, 1].set_xlabel('Latency (ms)')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].grid(True)
    
    # 3. Box plot comparison
    data_to_plot = []
    labels = []
    if file_latencies:
        data_to_plot.append(file_latencies)
        labels.append('File Operations')
    if dir_latencies:
        data_to_plot.append(dir_latencies)
        labels.append('Directory Operations')
    
    if data_to_plot:
        axes[1, 0].boxplot(data_to_plot, labels=labels)
        axes[1, 0].set_title('Latency by Operation Type')
        axes[1, 0].set_ylabel('Latency (ms)')
        axes[1, 0].grid(True)
    
    # 4. Cumulative distribution
    sorted_latencies = sorted(latencies)
    cumulative = np.arange(1, len(sorted_latencies) + 1) / len(sorted_latencies)
    axes[1, 1].plot(sorted_latencies, cumulative, 'r-')
    axes[1, 1].set_title('Cumulative Distribution')
    axes[1, 1].set_xlabel('Latency (ms)')
    axes[1, 1].set_ylabel('Cumulative Probability')
    axes[1, 1].grid(True)
    
    plt.tight_layout()
    
    # Save graph
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    graph_filename = os.path.join(output_dir, f"docker_mount_test_graphs_{timestamp}.png")
    plt.savefig(graph_filename, dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"Graphs saved to: {graph_filename}")


def test_docker_connection():
    """Test Docker connection and provide troubleshooting info"""
    print("Testing Docker connection...")
    
    # Test basic docker command
    try:
        result = subprocess.run(["docker", "info"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Docker CLI connection works")
        else:
            print("❌ Docker CLI connection failed")
            print(f"Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ Docker CLI connection timed out")
        return False
    except FileNotFoundError:
        print("❌ Docker CLI not found. Please install Docker.")
        return False
    
    # Test Python docker library connection
    try:
        tester = DockerMountTester(num_samples=1, timeout=1)
        print("✅ Python docker library connection works")
        
        # Test Docker version and info gathering
        print("\n📋 Docker Information:")
        try:
            docker_info = tester.docker_client.info()
            print(f"  Docker version: {docker_info.get('ServerVersion', 'unknown')}")
            print(f"  Storage driver: {docker_info.get('StorageDriver', 'unknown')}")
            print(f"  Operating system: {docker_info.get('OperatingSystem', 'unknown')}")
        except Exception as e:
            print(f"  Warning: Could not get Docker info: {e}")
        
        try:
            docker_version = tester.docker_client.version()
            print(f"  API version: {docker_version.get('ApiVersion', 'unknown')}")
            print(f"  Go version: {docker_version.get('GoVersion', 'unknown')}")
        except Exception as e:
            print(f"  Warning: Could not get Docker version: {e}")
        
        tester.cleanup()
        return True
    except Exception as e:
        print(f"❌ Python docker library connection failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Docker Mount Consistency Stress Tester")
    parser.add_argument("--samples", type=int, default=100, help="Number of samples to collect")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout per sample in seconds")
    parser.add_argument("--analyze", type=str, help="Analyze existing report file")
    parser.add_argument("--output", type=str, help="Output filename for report")
    parser.add_argument("--test-connection", action="store_true", help="Test Docker connection and exit")
    
    args = parser.parse_args()
    
    if args.test_connection:
        success = test_docker_connection()
        sys.exit(0 if success else 1)
    
    if args.analyze:
        # Analyze existing report
        print(f"Loading report: {args.analyze}")
        results = load_report(args.analyze)
        stats = analyze_results(results)
        print_statistics(stats)
        create_graphs(results)
    else:
        # Run new test
        tester = DockerMountTester(num_samples=args.samples, timeout=args.timeout)
        
        try:
            results = tester.run_stress_test()
            filename = tester.save_report(results, args.output)
            
            # Analyze and display results
            stats = analyze_results(results)
            print_statistics(stats)
            create_graphs(results)
            
        except KeyboardInterrupt:
            print("\nTest interrupted by user")
        except Exception as e:
            print(f"Error during testing: {e}")
        finally:
            tester.cleanup()


if __name__ == "__main__":
    main()