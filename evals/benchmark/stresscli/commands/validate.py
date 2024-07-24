# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# stresscli/validate.py

import difflib
import json

import click
import yaml

from .utils import dump_k8s_config


@click.command()
@click.option("--file", type=click.Path(), required=True, help="Specification YAML file to validate against")
@click.option("--validate_topology", is_flag=True, help="Validate topology in workload specification")
@click.pass_context
def validate(ctx, file, validate_topology):
    """Validate against the test spec."""
    kubeconfig = ctx.parent.params["kubeconfig"]
    namespace = ctx.parent.params["namespace"]
    current_state = dump_k8s_config(kubeconfig, return_as_dict=True, namespace=namespace)
    validate_spec(kubeconfig, file, current_state, validate_topology)


def read_spec(file_path):
    try:
        with open(file_path, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None  # Or some other default value or action


# hardwarespec:
#   mycluster-control-plane:
#     cpu: '224'
#     memory: 263835592Ki
# workloadspec:
#   node1:
#     chatqna:
#       replica: 1
#     chatqna-embedding-usvc:
#       replica: 1
def validate_spec(kubeconfig, spec_file, current_state, validate_topology=False):
    spec = read_spec(spec_file)
    if spec is None:
        return

    errors = []
    # Validate hardware spec and issue warnings
    for node_spec in spec.get("hardwarespec", {}).values():
        matched = False
        for current_node_spec in current_state["hardwarespec"].values():
            match = True
            warnings = []
            for key, value in node_spec.items():
                if key in current_node_spec:
                    if key == "cpu" or key == "habana.ai/gaudi":
                        try:
                            if int(current_node_spec[key]) > int(value):
                                warnings.append(
                                    f"Warning: Actual {key} ({current_node_spec[key]}) is higher than specified {key} ({value})."
                                )
                            elif int(current_node_spec[key]) < int(value):
                                errors.append(f"Actual {key} ({current_node_spec[key]}), expected {key} ({value}).")
                        except ValueError:
                            pass  # Handle non-integer values gracefully
                    elif key == "memory":
                        if current_node_spec[key] > value:
                            warnings.append(
                                f"Warning: Actual {key} ({current_node_spec[key]}) is higher than specified {key} ({value})."
                            )
                        elif current_node_spec[key] < value:
                            errors.append(f"Error: Actual {key} ({current_node_spec[key]}), expected {key} ({value}).")
                    else:
                        if current_node_spec[key] != value:
                            warnings.append(
                                f"Warning: Actual {key} ({current_node_spec[key]}), expected {key} ({value})."
                            )
                else:
                    match = False
                    break
            if match:
                matched = True
                for warning in warnings:
                    print(warning)
                break
        if not matched:
            errors.append(f"Error: No matching node found for hardware spec: {node_spec}")

    # Validate workload spec
    unmatched_workloads = {}
    for workloads in spec.get("workloadspec", {}).values():
        matched = False
        for current_workloads in current_state["workloadspec"].values():
            unmatched = {}
            for workload_name, workload_spec in workloads.items():
                if workload_name not in current_workloads:
                    unmatched[workload_name] = workload_spec
                else:
                    current_workload_spec = current_workloads.get(workload_name, {})
                    if current_workload_spec.get("replica") != workload_spec["replica"]:
                        unmatched[workload_name] = workload_spec
                    for ws in workload_spec.get("workloadspec", []):
                        for cs in current_workload_spec.get("workloadspec", []):
                            if ws["container"] == cs["container"]:
                                for key in ["limits", "requests"]:
                                    if ws["resources"].get(key) != cs["resources"].get(key):
                                        unmatched[workload_name] = workload_spec
            if not unmatched:
                matched = True
                break
            else:
                unmatched_workloads.update(unmatched)
        if not matched:
            errors.append(f"Error: No matching workloads found for spec: {unmatched_workloads}")

    # Validate topology if required
    if validate_topology:
        validate_topology_siblings(spec.get("workloadspec", {}), current_state.get("workloadspec", {}), errors)

    if errors:
        for error in errors:
            print(error)
        print("Validation failed.")
        print("Get more details of the spec differences:")
        diff = compare_dicts(spec, current_state)
        print(diff)
    else:
        print("Validation successful.")


def validate_topology_siblings(spec_workload, current_workload, errors):
    spec_siblings = get_siblings(spec_workload)
    current_siblings = get_siblings(current_workload)
    missing_siblings = spec_siblings - current_siblings
    # extra_siblings = current_siblings - spec_siblings

    if missing_siblings:
        if missing_siblings:
            for s in missing_siblings:
                errors.append(f"Error in topology: Not found {list(s)} in same K8s node")


def get_siblings(workload):
    sibling_sets = set()
    for workloads in workload.values():
        sibling_sets.add(frozenset(workloads.keys()))
    return sibling_sets


def dict_to_str(dictionary):
    return json.dumps(dictionary, indent=2, sort_keys=True)


def compare_dicts(dict1, dict2):
    str1 = dict_to_str(dict1)
    str2 = dict_to_str(dict2)
    diff = difflib.unified_diff(
        str1.splitlines(), str2.splitlines(), fromfile="expected_spec", tofile="current_spec", lineterm=""
    )
    return "\n".join(diff)
