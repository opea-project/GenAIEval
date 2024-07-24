# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# stresscli/dump.py

import click

from .utils import dump_k8s_config


@click.command()
# @click.option('--kubeconfig', type=click.Path(), help='Configuration file to Kubernetes')
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default="testspec.yaml",
    required=True,
    help="YAML file of cluster configuration",
)
@click.pass_context
#'-o', '--output', type=click.Path(), default='output.yaml', help='YAML file of cluster configuration'
def dump(ctx, output):
    """Dump the test spec."""
    kubeconfig = ctx.parent.params["kubeconfig"]
    namespace = ctx.parent.params["namespace"]
    dump_k8s_config(kubeconfig, output, namespace=namespace)
