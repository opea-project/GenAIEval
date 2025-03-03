# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from components.adaptor.base import Module, Node, convert_tuple, get_support_modules


class Adaptor:

    def __init__(self, yaml_data: str):
        self.nodes = self.parse_nodes(yaml_data)
        self.root_func: Optional[Callable] = None

    def parse_nodes(self, yaml_data):
        parsed_nodes = {}
        for node in yaml_data.get("nodes", []):
            node_type = node.get("node")
            modules_dict = {
                mod.get("module_type"): Module(
                    type=mod.get("module_type", ""),
                    params={k: convert_tuple(v) for k, v in mod.items() if k not in ["module_type"]},
                )
                for mod in node.get("modules", [])
                if mod.get("module_type")
            }
            node_params = {k: convert_tuple(v) for k, v in node.items() if k not in ["node", "node_type", "modules"]}
            cur_node = Node(type=node_type, params=node_params, modules=modules_dict)
            if node_type in parsed_nodes:
                parsed_nodes[node_type].append(cur_node)
            else:
                parsed_nodes[node_type] = [cur_node]
        return parsed_nodes

    def get_node(self, node_type, idx=0):
        nodes = self.nodes[node_type] if node_type in self.nodes else None
        return nodes[idx] if nodes and idx < len(nodes) else None

    def get_modules_from_node(self, node_type, idx=0):
        node = self.get_node(node_type, idx)
        return node.modules if node else None

    def get_module(self, node_type, module_type, idx=0):
        if module_type is None:
            return self.get_node(node_type, idx)
        else:
            modules = self.get_modules_from_node(node_type, idx)
            return modules[module_type] if modules and module_type in modules else None

    def update_all_module_functions(self, module_map, node_type_map):
        self.root_func = get_support_modules("root", module_map)

        for node_list in self.nodes.values():
            for node in node_list:
                node.update_func(module_map)
                node.is_active = False
                for module in node.modules.values():
                    module.update_func(module_map)
                    module.is_active = False

        self.activate_modules_based_on_type(node_type_map)

    def activate_modules_based_on_type(self, node_type_map):
        if not self.root_func:
            return

        for node_list in self.nodes.values():
            for node in node_list:
                node_type = node.type
                if not getattr(self.root_func, node_type, None):
                    continue
                node.is_active = True
                active_module_type = getattr(node.func, node_type_map[node_type], None)
                if active_module_type and active_module_type in node.modules:
                    node.modules[active_module_type].is_active = True
