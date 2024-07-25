# Stress Test Script

## Introduction

This script is a load testing tool designed to simulate high-concurrency scenarios for a given server. It supports multiple task types and models, allowing users to evaluate the performance and stability of different configurations under heavy load.

## Prerequisites

- Python 3.8+
- Required Python packages:
  - argparse
  - requests
  - transformers

## Installation

1. Clone the repository or download the script to your local machine.
2. Install the required Python packages using `pip`:

   ```sh
   pip install argparse requests transformers
   ```

## Usage

The script can be executed with various command-line arguments to customize the test. Here is a breakdown of the available options:

- `-f`: The file path containing the list of questions to be used for the test. If not provided, a default question will be used.
- `-s`: The server address in the format `host:port`. Default is `localhost:8080`.
- `-c`: The number of concurrent workers. Default is 20.
- `-d`: The duration for which the test should run. This can be specified in seconds (e.g., `30s`), minutes (e.g., `10m`), or hours (e.g., `1h`). Default is `1h`.
- `-u`: The delay time before each worker starts, specified in seconds (e.g., `2s`). Default is `1s`.
- `-t`: The task type to be tested. Options are `chatqna`, `openai`, `tgi`, `llm`, `tei_embedding`, `embedding`, `retrieval`, `tei_rerank` or `reranking`. Default is `chatqna`.
- `-m`: The model to be used. Default is `Intel/neural-chat-7b-v3-3`.
- `-z`: The maximum number of tokens for the model. Default is 1024.

### Example Commands

```bash
python stress_benchmark.py -f data.txt -s localhost:8888 -c 50 -d 30m -t chatqna
```

### Running the Test

To start the test, execute the script with the desired options. The script will:

1. Initialize the question pool from the provided file or use the default question.
2. Start a specified number of worker threads.
3. Each worker will repeatedly send requests to the server and collect response data.
4. Results will be written to a CSV file.

### Output

The results will be stored in a CSV file with the following columns:

- `question_len`: The length of the input question in tokens.
- `answer_len`: The length of the response in tokens.
- `first_chunk`: The time taken to receive the first chunk of the response.
- `overall`: The total time taken for the request to complete.
- `err`: Any error that occurred during the request.
- `code`: The HTTP status code of the response.

## Notes

- Ensure the server address is correctly specified and accessible.
- Adjust the concurrency level (`-c`) and duration (`-d`) based on the capacity of your server and the goals of your test.
- Monitor the server's performance and logs to identify any potential issues during the load test.

## Logging

The script logs detailed information about each request and any errors encountered. The logs can be useful for diagnosing issues and understanding the behavior of the server under load.
