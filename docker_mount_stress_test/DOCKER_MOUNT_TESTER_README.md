# Docker Mount Consistency Tester

A Python script that stress-tests Docker mount consistency by measuring the real-world latency between host filesystem changes and their visibility in Docker containers.

## Features

- **Comprehensive Testing**: Tests both file writes and directory creation operations
- **Multiple Test Environments**: Uses multiple temporary directories and containers for thorough testing
- **Detailed Metadata**: Collects system information, Docker configuration, and test parameters
- **Statistical Analysis**: Provides mean, median, standard deviation, percentiles, and more
- **Visualization**: Generates graphs showing latency distribution, trends over time, and comparative analysis
- **Report Management**: Saves results to JSON and supports re-analysis of existing reports

## Requirements

- Python 3.6+
- Docker installed and running
- Required Python packages (install with `pip3 install -r requirements.txt`):
  - docker>=6.0.0
  - matplotlib>=3.5.0
  - numpy>=1.21.0

## Quick Start

1. **Setup**: Run the setup script to install dependencies and prepare the environment:
   ```bash
   ./setup_docker_tester.sh
   ```

2. **Run Test**: Execute the stress test with default settings:
   ```bash
   python3 docker_mount_tester.py
   ```

3. **View Results**: The script will automatically display statistics and generate graphs when complete.

## Usage Examples

### Basic Test
```bash
python3 docker_mount_tester.py
```

### Custom Parameters
```bash
# Run 200 samples with 45-second timeout per sample
python3 docker_mount_tester.py --samples 200 --timeout 45
```

### Save Report with Custom Name
```bash
python3 docker_mount_tester.py --output my_docker_test.json
```

### Analyze Existing Report
```bash
python3 docker_mount_tester.py --analyze docker_mount_test_20231201_143022.json
```

## Test Methodology

The tester measures the time between:
1. **Host Operation Completion**: When a file write or directory creation is fully committed to disk on the host
2. **Container Visibility**: When the change becomes visible inside the Docker container

### Test Types
- **File Operations**: Creates files with random content, measures when they appear in containers
- **Directory Operations**: Creates directories and measures visibility latency

### Test Environment
- Creates multiple temporary directories on the host
- Launches Alpine Linux containers with bind mounts to these directories
- Randomly selects test type and environment for each sample
- Uses filesystem sync operations to ensure data is committed before measurement

## Report Format

Reports are saved as JSON files containing:

```json
{
  "metadata": {
    "timestamp": "2023-12-01T14:30:22",
    "system": { ... },
    "docker": { ... }
  },
  "test_config": {
    "num_samples": 100,
    "timeout": 30.0,
    "num_environments": 3
  },
  "samples": [
    {
      "sample_id": 0,
      "test_type": "file",
      "environment": 0,
      "latency_ms": 1.234,
      "timestamp": "..."
    }
  ],
  "summary": {
    "total_samples": 95,
    "timeouts": 5,
    "success_rate": 0.95
  }
}
```

## Output Statistics

The script provides comprehensive statistics including:
- **Overall metrics**: Mean, median, standard deviation, min/max latency
- **Percentiles**: 95th and 99th percentile latencies
- **Operation-specific**: Separate stats for file vs directory operations
- **Success rate**: Percentage of samples that completed within timeout

## Visualization

Generates four types of graphs:
1. **Latency Over Time**: Shows how latency changes during the test
2. **Latency Distribution**: Histogram of latency values
3. **Operation Comparison**: Box plot comparing file vs directory operations
4. **Cumulative Distribution**: Shows percentile breakdown of latencies

## Interpreting Results

### Good Performance Indicators
- Mean latency < 10ms
- Low standard deviation (< 5ms)
- Few or no timeouts
- Consistent performance across operation types

### Performance Concerns
- Mean latency > 100ms
- High standard deviation (> 50ms)
- Many timeouts (> 5% of samples)
- Large differences between file and directory operations

## Troubleshooting

### Common Issues
1. **Docker not running**: Ensure Docker daemon is started
2. **Permission errors**: Run with appropriate permissions or use sudo
3. **Timeout errors**: Increase timeout value or check system load
4. **Python dependencies**: Install requirements with `pip3 install -r requirements.txt`

### Performance Tips
- Close unnecessary applications during testing
- Use SSD storage for better baseline performance
- Consider Docker storage driver configuration
- Test under different system load conditions

## System Requirements

- **Operating System**: Linux, macOS, or Windows with Docker support
- **Memory**: At least 2GB RAM available
- **Storage**: Fast storage (SSD recommended) for accurate measurements
- **Docker**: Version 19.03 or later recommended