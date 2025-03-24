# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import json
import os

from intel_ai_safety.model_card_gen.model_card_gen import ModelCardGen
from intel_ai_safety.model_card_gen.validation import validate_json_schema
from jsonschema import ValidationError


def generate_model_card(
    input_mc_metadata_json_path,
    metric_by_threshold=None,
    metric_by_group=None,
    mc_template_type="html",
    output_dir=None,
):
    """Generates an HTML or Markdown representation of a model card.

    Parameters:
    input_mc_metadata_json_path (json, required): The model card JSON object containing the model's metadata and other details.
    metric_threshold_csv (str, optional): The file path to a CSV containing metric threshold data.
    metric_grp_csv (str, optional): The file path to a CSV containing metric group data.
    mc_template_type (str, optional): Template to use for rendering the model card. Options include "html" for an interactive HTML model card or "md" for a static Markdown version. Defaults to "html"
    output_dir (str, optional): The directory where the model card file will be saved. Defaults to the current directory.

    Returns:
    str: The HTML or Markdown representation of the model card.
    """
    if output_dir is None:
        output_dir = os.getcwd()

    if os.path.exists(input_mc_metadata_json_path) and os.path.isfile(input_mc_metadata_json_path):
        try:
            with open(input_mc_metadata_json_path, "r") as file:
                model_card_json = json.load(file)

        except json.JSONDecodeError as e:
            raise ValueError("The file content is not valid JSON.") from e
    else:
        raise FileNotFoundError(f"The JSON file at {input_mc_metadata_json_path} does not exist.")

    try:
        validate_json_schema(model_card_json)

    except ValidationError as e:
        raise ValidationError(
            "Warning: The schema version of the uploaded JSON does not correspond to a model card schema version or "
            "the uploaded JSON does not follow the model card schema."
        )

    model_card = ModelCardGen.generate(
        model_card_json,
        metrics_by_threshold=metric_by_threshold,
        metrics_by_group=metric_by_group,
        template_type=mc_template_type,
    )

    model_card_name = f"Model Card.{mc_template_type}"

    full_path = os.path.join(output_dir, model_card_name)
    model_card.export_model_card(full_path)

    if mc_template_type == "html":
        return model_card._repr_html_()
    else:
        return model_card._repr_md_()
