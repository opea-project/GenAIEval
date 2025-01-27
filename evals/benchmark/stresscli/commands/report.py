# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# stresscli/dump.py

import configparser
import csv
import glob
import os
import re
import sys

import click
import yaml

KEYWORDS_SECTION_NAME = "output.log"
CSV_SECTION_NAME = "stats.csv"
TESTSPEC_SECTION_NAME = "testspec.yaml"
METRICS_SECTION_NAME = "metrics.json"
UTILIZATION_SECTION_NAME = "utilization.json"


@click.command()
@click.option("--folder", type=click.Path(), required=True, help="Path to log folder")
@click.option("--format", default="plain_text", help="Output format, plain_text or csv, default is plain_text")
# @click.option('--include', default='testspec.yaml', help='Extract output data from output.log, stats.csv, and testspec.yaml, default is testspec.yaml')
@click.option(
    "--transformeddata",
    type=bool,
    default=False,
    help="If transformedData is True, transpose the data to have metrics as columns.",
)
@click.option("-o", "--output", type=click.Path(), help="Save output to file")
@click.pass_context
def report(ctx, folder, format, output, transformeddata):
    """Print the test report."""
    output_data = {}
    testcases = get_testcases(folder)
    for testcase in testcases:
        include = "|".join([TESTSPEC_SECTION_NAME, CSV_SECTION_NAME, METRICS_SECTION_NAME, UTILIZATION_SECTION_NAME])
        extracted_data = export_testdata(testcase, folder, include)
        if extracted_data:
            output_data[testcase] = extracted_data

    if transformeddata:
        transformed_output_data = {}
        for key, value in output_data.items():
            for k, v in value.items():
                if k not in transformed_output_data:
                    transformed_output_data[k] = {}
                transformed_output_data[k][key] = v
        output_data = transformed_output_data

    if format == "plain_text":
        if output:
            with open(output, "w") as f:
                for testcase, data in output_data.items():
                    f.write(f"Testcase: {testcase} {data['run_name']}\n")
                    for key, value in data.items():
                        f.write(f"  {key}: {value}\n")
                    f.write("\n")
        else:
            for testcase, data in output_data.items():
                print(f"Testcase: {testcase} {data['run_name']}")
                for key, value in data.items():
                    print(f"  {key}: {value}")
                print()

    elif format == "csv":
        headers = ["No"]
        for data in output_data.values():
            for key in data.keys():
                if key not in headers:
                    headers.append(key)

        if output:
            with open(output, "w", newline="") as csvfile:
                csvwriter = csv.DictWriter(csvfile, fieldnames=headers)
                csvwriter.writeheader()
                for testcase, data in output_data.items():
                    row = {"No": testcase}
                    row.update(data)
                    csvwriter.writerow(row)
        else:
            csvwriter = csv.DictWriter(sys.stdout, fieldnames=headers)
            csvwriter.writeheader()
            for testcase, data in output_data.items():
                row = {"No": testcase}
                row.update(data)
                csvwriter.writerow(row)


def get_report_results(folder):
    """Print the test report."""
    print(f"Get report results from: {folder}")
    output_data = {}
    testcases = get_testcases(folder)
    for testcase in testcases:
        include = "|".join([TESTSPEC_SECTION_NAME, CSV_SECTION_NAME, METRICS_SECTION_NAME])
        extracted_data = export_testdata(testcase, folder, include)
        if extracted_data:
            output_data[testcase] = extracted_data

    result = {}
    for testcase, data in output_data.items():
        testcase_result = {}
        for key, value in data.items():
            testcase_result[key] = value
        result[testcase] = testcase_result
    return result


def export_testspec(testcase, folder):
    testspec_path = os.path.join(folder, f"{testcase}_testspec.yaml")
    extracted_data = {}
    if os.path.exists(testspec_path):
        extract_yaml(extracted_data, testspec_path)


def export_testdata(testcase, folder, include="output.log|stats.csv|testspec.yaml|metrics.json"):
    output_log = os.path.join(folder, f"{testcase}_output.log")
    csv_path = os.path.join(folder, f"{testcase}_stats.csv")
    testspec_path = os.path.join(folder, f"{testcase}_testspec.yaml")
    metrics_path = os.path.join(folder, f"{testcase}_metrics.json")
    utilization_path = os.path.join(folder, f"{testcase}_utilization.json")
    extracted_data = {}
    if os.path.exists(csv_path):
        if TESTSPEC_SECTION_NAME in include:
            extract_yaml(extracted_data, testspec_path)
        if CSV_SECTION_NAME in include:
            extract_csv(extracted_data, csv_path)
        if KEYWORDS_SECTION_NAME in include:
            with open(output_log, "r") as file:
                log_data = file.read()
                extract_stdout(extracted_data, log_data)
        if METRICS_SECTION_NAME in include and os.path.exists(metrics_path):
            extract_json(extracted_data, metrics_path)
        if UTILIZATION_SECTION_NAME in include and os.path.exists(utilization_path):
            extract_utilization_json(extracted_data, utilization_path)
    else:
        print("Test failure, no data")
    return extracted_data


# Function to read keywords and patterns from config file
def read_log_keywords(filename="config.ini"):
    config = configparser.ConfigParser()
    config.optionxform = str
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(script_dir, filename)
    config.read(filename)
    keywords = {}
    if KEYWORDS_SECTION_NAME in config:
        for key, pattern in config[KEYWORDS_SECTION_NAME].items():
            keywords[key] = pattern
    return keywords


def read_csv_keywords(filename="config.ini"):
    config = configparser.ConfigParser(interpolation=None)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(script_dir, filename)
    config.read(filename)
    columns_to_extract = [col.strip() for col in config.get(CSV_SECTION_NAME, "columns_name").split(",")]
    row_name = config.get(CSV_SECTION_NAME, "row_name").strip()
    return columns_to_extract, row_name


def read_yaml_keywords(filename="config.ini"):
    config = configparser.ConfigParser()
    config.optionxform = str
    script_dir = os.path.dirname(os.path.abspath(__file__))
    filename = os.path.join(script_dir, filename)
    config.read(filename)
    keywords = {}
    if TESTSPEC_SECTION_NAME in config:
        for key, pattern in config[TESTSPEC_SECTION_NAME].items():
            keywords[key] = pattern
    return keywords


import json


def extract_json(extracted_data, json_file):
    try:
        with open(json_file, "r") as file:
            data = json.load(file)

            for key, value in data.items():
                print(f"Key: {key}, Value: {value}")
                extracted_data[key] = value

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except FileNotFoundError:
        print("The specified file was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def extract_utilization_json(extracted_data, json_file):
    try:
        with open(json_file, "r") as file:
            data = json.load(file)

            deployment_metrics = data.get("deployment_metrics", {})

            for key, value in deployment_metrics.items():
                #                print(f"Key: {key}, Value: {value}")
                extracted_data[key] = value

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except FileNotFoundError:
        print("The specified file was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Function to extract information based on keywords and patterns
def extract_stdout(extracted_data, log):
    keywords = read_log_keywords("config.ini")
    for key, pattern in keywords.items():
        match = re.search(pattern, log)
        if match:
            extracted_data[key] = match.group(1)
    # for key, value in extracted_data.items():
    #     print(f"{key}: {value}")
    return extracted_data


def extract_csv(extracted_data, csv_file):
    # Read configuration values
    columns_to_extract, row_name = read_csv_keywords()
    with open(csv_file, newline="") as file:
        reader = csv.DictReader(file)

        # Iterate through each row in the CSV file
        for row in reader:
            # Check if the row corresponds to the second row ("Aggregated" row)
            if row["Name"] == row_name:
                # Extract the values for the specified columns
                for column in columns_to_extract:
                    # extracted_data[f'locust_P{column[:-1]}'] = float(row[column])
                    extracted_data[f"locust_P{column[:-1]}"] = row[column]

                # Once values are extracted, break out of the loop
                break  # Print the extracted values


def extract_yaml(extracted_data, yaml_file):
    # Read configuration values
    keywords = read_yaml_keywords("config.ini")
    # Load YAML file
    with open(yaml_file, "r") as f:
        yaml_data = yaml.safe_load(f)
        extracted_data["run_name"] = yaml_data["benchmarkspec"]["run_name"]
        for section, pattern in keywords.items():
            if section in yaml_data:
                if pattern == "*":
                    extracted_data.update(yaml_data[section])
                else:
                    attributes = pattern.split()
                    for attr in attributes:
                        if attr in yaml_data[section]:
                            extracted_data[f"{attr}"] = yaml_data[section][attr]
                        else:
                            for key, value in yaml_data[section].items():
                                if isinstance(value, dict) and attr in value:
                                    extracted_data[f"{attr}"] = value[attr]
                                    break


def get_testcases(directory_path):
    yaml_files = glob.glob(os.path.join(directory_path, "*.yaml"))
    first_parts = []

    for yaml_file in yaml_files:
        file_name = os.path.basename(yaml_file)
        file_name_parts = file_name.split("_")
        first_part = file_name_parts[0]
        first_parts.append(first_part)

    return sorted(first_parts)
