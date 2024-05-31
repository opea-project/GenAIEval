#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
from evals.evaluation.bigcode_evaluation_harness import evaluate, setup_parser


def main():
    eval_args = setup_parser()
    results = evaluate(eval_args)
    print(results)


if __name__ == "__main__":
    main()
