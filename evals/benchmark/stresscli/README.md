# StressCli

This project includes benchmark toolset for AI workloads such as OPEA.

## stresscli.py

`stresscli.py` is a command line tool for dumping test specs and performing load tests.

### Prerequirements

This tool will use `kubectl` to collect Kubernetes cluster information. So you need to make sure `kubectl` is installed and 

This tool uses `locust` by default to do load test. You have to install `locust` to your machine simply by
```
pip3 install locust
```
For detail information of `locust`, go to [locust website](https://docs.locust.io/en/stable/installation.html).

### Installation

The recommended way to install and run stresscli is in a virtualenv with the latest version of Python 3 (at least Python 3.11). If Python is not installed, you can likely install it using your distribution's
package manager, or see the [Python Download page](https://www.python.org/downloads/).

```bash
git clone https://github.com/opea-project/GenAIEval.git
# go to project root
cd GenAIEval/evals/benchmark/stresscli
# create virtual env
python3 -m venv stresscli_virtualenv
source stresscli_virtualenv/bin/activate
# install requirements
pip install -r requirements.txt
```

### Usage

```
./stresscli.py --help
Usage: stresscli.py [OPTIONS] COMMAND [ARGS]...

  StressCLI - A command line tool for stress testing OPEA workloads.

Options:
  --kubeconfig PATH  Configuration file to Kubernetes
  --help             Show this message and exit.

Commands:
  dump       Dump the test spec
  load-test  Do load test
  report     Print the test report
  validate   Validate against the test spec
```
#### Run a test

**Note: Please edit the [run.yaml](./run.yaml) file or create your profile before run the load test.**

```
./stresscli.py load-test --profile run.yaml
```

More detail options:
```
./stresscli.py load-test --help
Usage: stresscli.py load-test [OPTIONS]

  Do load test

Options:
  --profile PATH  Path to profile YAML file
  --help          Show this message and exit.
```

#### Generate the test output report

You can generate the report for test cases by:
```
./stresscli.py report --folder /home/sdp/test_reports/20240710_004105 --format csv -o data.csv
```

More detail options:
```
./stresscli.py report --help
Usage: stresscli.py report [OPTIONS]

  Print the test report

Options:
  --folder PATH              Path to log folder  [required]
  --format TEXT              Output format, plain_text, html or csv, default
                             is plain_text
  --transformeddata BOOLEAN  If transformedData is True, transpose the data to
                             have metrics as columns.
  --profile PATH             Path to profile YAML file
  -o, --output PATH          Save output to file
  --help                     Show this message and exit.
```
#### Dump the configuration

You can dump the current testing profile by
```
./stresscli.py dump -o <output_file>
```
More detail options:
```
./stresscli.py dump --help
Usage: stresscli.py dump [OPTIONS]

  Dump the test spec

Options:
  -o, --output PATH  YAML file of cluster configuration  [required]
  --help             Show this message and exit.
```

#### Validate against the spec

You can validate if the current K8s and workloads deployment comply with the test spec by:
```
./stresscli.py validate --file testspec.yaml
```

More detail options:
```
./stresscli.py validate --help
Usage: stresscli.py validate [OPTIONS]

  Validate against the test spec

Options:
  --file PATH          Specification YAML file to validate against  [required]
  --validate_topology  Validate topology in workload specification
  --help               Show this message and exit.
```
