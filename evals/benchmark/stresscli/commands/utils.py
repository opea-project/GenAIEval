# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# stresscli/utils.py

import json
import random
import string
import subprocess

import yaml
from kubernetes import client
from kubernetes import config as k8s_config


def dump_k8s_config(kubeconfig, output=None, return_as_dict=False, namespace="default"):
    """Dump the Kubernetes cluster configuration to a YAML file."""
    # Load Kubernetes configuration
    if kubeconfig:
        k8s_config.load_kube_config(config_file=kubeconfig)
    else:
        k8s_config.load_kube_config()

    # Initialize the Kubernetes API client
    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()

    # Get all nodes in the cluster
    nodes = v1.list_node()
    node_deployments = {}
    node_hardware_spec = {}

    # excluded_namespaces = {"kube-system", "kube-public", "kube-node-lease", "local-path-storage"}
    for node in nodes.items:
        node_name = node.metadata.name
        # Generate hardwarespec

        node_info = node.status.node_info
        node_hardware_spec[node_name] = {
            "architecture": node_info.architecture,
            "containerRuntimeVersion": node_info.container_runtime_version,
            "kernelVersion": node_info.kernel_version,
            "kubeProxyVersion": node_info.kube_proxy_version,
            "kubeletVersion": node_info.kubelet_version,
            "operatingSystem": node_info.operating_system,
            "osImage": node_info.os_image,
        }
        if "calico" in get_k8s_cni(v1):
            node_hardware_spec[node_name]["canico"] = get_calico_version()
        if get_cpu_manager_policy(v1) != "none":
            node_hardware_spec["cpuManagerPolicy"] = "static"
        node_capacity = {k: str(v) for k, v in node.status.capacity.items()}
        if "cpu" in node_capacity:
            node_hardware_spec[node_name]["cpu"] = node_capacity["cpu"]
        if "memory" in node_capacity:
            node_hardware_spec[node_name]["memory"] = node_capacity["memory"]
        if "habana.ai/gaudi" in node_capacity:
            node_hardware_spec[node_name]["habana.ai/gaudi"] = node_capacity["habana.ai/gaudi"]

        # Generate workloadspec
        node_deployments[node_name] = {}
        # Get all pods running on the node
        field_selector = f"spec.nodeName={node_name}"
        # pods = v1.list_pod_for_all_namespaces(field_selector=field_selector)
        pods = v1.list_namespaced_pod(namespace=namespace, field_selector=field_selector)

        for pod in pods.items:
            # if pod.metadata.namespace in excluded_namespaces:
            #    continue
            owner_references = pod.metadata.owner_references
            for owner in owner_references:
                if owner.kind == "ReplicaSet":
                    replicaset_name = owner.name
                    # Get the deployment owning the replicaset
                    rs = apps_v1.read_namespaced_replica_set(name=replicaset_name, namespace=pod.metadata.namespace)
                    for owner in rs.metadata.owner_references:
                        if owner.kind == "Deployment":
                            deployment_name = owner.name
                            if deployment_name not in node_deployments[node_name]:
                                node_deployments[node_name][deployment_name] = {"replica": 0}
                            node_deployments[node_name][deployment_name]["replica"] += 1
                            # Collect resource information
                            resources = pod.spec.containers[0].resources
                            resource_details = {}
                            if resources.requests:
                                resource_details["requests"] = resources.requests
                            if resources.limits:
                                resource_details["limits"] = resources.limits
                            if resource_details:
                                node_deployments[node_name][deployment_name]["resources"] = resource_details

    k8s_spec = {"hardwarespec": node_hardware_spec, "workloadspec": node_deployments}
    if return_as_dict:
        return k8s_spec
    else:
        # Write the deployment details to the YAML file
        with open(output, "w") as yaml_file:
            yaml.dump(k8s_spec, yaml_file, default_flow_style=False)
        print(f"Cluster configuration written to {output}")


def generate_random_suffix(length=6):
    """Generate a random string of fixed length."""
    letters = string.ascii_lowercase + string.digits
    return "".join(random.choice(letters) for _ in range(length))


def generate_lua_script(template_path, output_path, dataset_path):
    """Generate a Lua script from the template with the specified dataset path."""
    with open(template_path, "r") as template_file:
        template_content = template_file.read()

    script_content = template_content.replace("${DATASET_PATH}", dataset_path)

    with open(output_path, "w") as output_file:
        output_file.write(script_content)


def run_command(command):
    """Runs a command and returns the output."""
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, text=True)
    if result.returncode != 0:
        print(f"Error running command: {result.stderr}")
        return None
    return result.stdout.strip()


# get cni version
def get_calico_version():
    command = [
        "kubectl",
        "get",
        "pods",
        "-n",
        "kube-system",
        "-l",
        "k8s-app=calico-node",
        "-o",
        "jsonpath='{.items[*].spec.containers[*].image}'",
    ]
    image_name = run_command(command)
    # print(image_name)
    parts = image_name.split(":")
    if len(parts) > 1:
        return parts[-1]
    else:
        return None


def get_k8s_cni(v1):
    # List all pods in the kube-system namespace
    pods = v1.list_namespaced_pod(namespace="kube-system")

    cni_plugins = {
        "calico": "calico-node",
        "flannel": "kube-flannel-ds",
        "weave": "weave-net",
        "cilium": "cilium",
        "contiv": "contiv-netplugin",
        "canal": "canal",
        "romana": "romana-agent",
        "kube-router": "kube-router",
        "multus": "kube-multus-ds",
    }

    detected_plugins = []
    for pod in pods.items:
        for cni, identifier in cni_plugins.items():
            if identifier in pod.metadata.name:
                detected_plugins.append(cni)
    # if detected_plugins:
    #     print(f"Detected CNI Plugins: {', '.join(detected_plugins)}")
    # else:
    #     print("No known CNI plugin detected.")
    return detected_plugins


def get_cpu_manager_policy(v1):
    # Get the kubelet-config ConfigMap
    try:
        config_map = v1.read_namespaced_config_map(name="kubelet-config", namespace="kube-system")
    except client.exceptions.ApiException as e:
        print(f"Exception when retrieving ConfigMap: {e}")
        return

    # Parse the ConfigMap data
    kubelet_config_data = config_map.data.get("kubelet")
    if not kubelet_config_data:
        print("kubelet configuration not found in the ConfigMap")
        return

    # Load the kubelet configuration YAML
    kubelet_config = yaml.safe_load(kubelet_config_data)

    # Get the cpuManagerPolicy setting
    cpu_manager_policy = kubelet_config.get("cpuManagerPolicy", "none")
    # print(f"CPU Manager Policy: {cpu_manager_policy}")
    return cpu_manager_policy
