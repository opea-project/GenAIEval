# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# stresscli/main.py

import click
from commands.dump import dump
from commands.load_test import load_test
from commands.report import report
from commands.validate import validate


@click.group()
@click.option("--kubeconfig", type=click.Path(), help="Configuration file to Kubernetes")
@click.option("--namespace", default="default", help="Namespace to dump Kubernetes config from")
def cli(kubeconfig, namespace):
    """StressCLI - A command line tool for stress testing OPEA workloads."""
    pass


cli.add_command(dump)
cli.add_command(load_test)
cli.add_command(validate)
cli.add_command(report)

if __name__ == "__main__":
    cli()
