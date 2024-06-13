import json
import yaml
import argparse


def load_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def load_yaml(file_path):
    with open(file_path, 'r') as f:
        data = yaml.safe_load(f)
    return data


def write_json(data, output_file):
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)


def parse_hardware_info(parsed_data):
    hardware_details = {}
    for key, value in parsed_data.items():
        ip = value.get("ip", [])
        hardware_type = value.get("type", "unknown")
        sockets = value.get("sockets", -1)
        cores_per_socket = value.get("cores_per_socket", -1)
        threads_per_core = value.get("threads_per_core", -1)
        frequency = value.get("frequency", -1)
        memory_bandwidth = value.get("memory_bandwidth", -1)
        network_bandwidth = value.get("network_bandwidth", -1)

        hardware_details[key] = {
            "ip": ip,
            "type": hardware_type,
            "sockets": sockets,
            "cores_per_socket": cores_per_socket,
            "threads_per_core": threads_per_core,
            "frequency": frequency,
            "memory_bandwidth": memory_bandwidth,
            "network_bandwidth": network_bandwidth
        }

    return hardware_details


def parse_service_info(yaml_data):

    total_cores = yaml_data.get("total_cores", 56)
    services = yaml_data.get("opea_micro_services", {})
    num_services = len(services)

    cores_per_service = total_cores // num_services
    extra_cores = total_cores % num_services

    json_data = {}
    current_core = 0
    for service, details in yaml_data.get("opea_micro_services", {}).items():
        hw_type = "cpu" if "gaudi" in details.get("type", "").lower() else "cpu"
        end_core = current_core + cores_per_service - 1
        if extra_cores > 0:
            end_core += 1
            extra_cores -= 1
        service_info = {
            "hw": hw_type,
            "replica": 1,
            "cores": f"{current_core}-{end_core}",
            "endpoint": details.get("endpoint", ""),
            "image": details.get("image", "")
        }
        if "model-id" in details:
            service_info["model_id"] = details["model-id"]
        json_data[service] = service_info
        current_core = end_core + 1

    return json_data


def main():
    parser = argparse.ArgumentParser(description="Read and parse JSON/YAML files and output JSON file")
    parser.add_argument("--hardware_info", help="Path to input JSON file")
    parser.add_argument("--service_info", help="Path to input YAML file")
    parser.add_argument("--output_strategy", help="Path to output JSON file", default="./output_strategy.json")
    args = parser.parse_args()

    hardware_info = load_json(args.hardware_info)
    service_info = load_yaml(args.service_info)
    service_details = parse_service_info(service_info)

    write_json(service_details, args.output_file)
    print(f"Output JSON file has been created successfully: {args.output_file}")


if __name__ == "__main__":
    main()
