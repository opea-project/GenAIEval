# Model Card Generator

Model Card Generator allows users to create interactive HTML and static Markdown reports  containing model performance and fairness metrics. 

**Model Card Sections**

<table class="tg">
<thead>
  <tr>
    <th class="tg-0pky">Section<br></th>
    <th class="tg-0pky">Subsection</th>
    <th class="tg-73oq">Description</th>
  </tr>
</thead>
<tbody>
  <tr>
    <td class="tg-0pky" rowspan="9">Model Details</td>
    <td class="tg-0pky">Overview</td>
    <td class="tg-0pky">A brief, one-line description of the model card.</td>
  </tr>
  <tr>
    <td class="tg-0pky">Documentation</td>
    <td class="tg-0pky">A thorough description of the model and its usage.</td>
  </tr>
  <tr>
    <td class="tg-0pky">Owners</td>
    <td class="tg-0pky">The individuals or teams who own the model.</td>
  </tr>
  <tr>
    <td class="tg-0pky">Version</td>
    <td class="tg-0pky">The version of the schema</td>
  </tr>
  <tr>
    <td class="tg-0pky">Licenses</td>
    <td class="tg-0pky">The model's license for use.</td>
  </tr>
  <tr>
    <td class="tg-0pky">References</td>
    <td class="tg-0pky">Links providing more information about the model.</td>
  </tr>
  <tr>
    <td class="tg-0pky">Citations</td>
    <td class="tg-0pky">How to reference this model card.</td>
  </tr>
  <tr>
    <td class="tg-0pky">Path</td>
    <td class="tg-0pky">The path where the model is stored.</td>
  </tr>
  <tr>
    <td class="tg-0pky">Graphics</td>
    <td class="tg-0pky">Collection of overview graphics.</td>
  </tr>
  <tr>
    <td class="tg-0pky" rowspan="6">Model Parameters</td>
    <td class="tg-0pky">Model Architecture</td>
    <td class="tg-0pky">The architecture of the model.</td>
  </tr>
  <tr>
    <td class="tg-0pky">Data</td>
    <td class="tg-0pky">The datasets used to train and evaluate the model.</td>
  </tr>
  <tr>
    <td class="tg-0pky">Input Format</td>
    <td class="tg-0pky">The data format for inputs to the model.</td>
  </tr>
  <tr>
    <td class="tg-0pky">Input Format Map</td>
    <td class="tg-0pky">The data format for inputs to the model, in key-value format.</td>
  </tr>
  <tr>
    <td class="tg-0pky">Output Format</td>
    <td class="tg-0pky">The data format for outputs from the model.</td>
  </tr>
  <tr>
    <td class="tg-0pky">Output Format Map</td>
    <td class="tg-0pky">The data format for outputs from the model, in key-value format.</td>
  </tr>
  <tr>
    <td class="tg-0pky" rowspan="2">Quantitative analysis</td>
    <td class="tg-0pky">Performance Metrics</td>
    <td class="tg-0pky">The model performance metrics being reported.</td>
  </tr>
  <tr>
    <td class="tg-0pky">Graphics</td>
    <td class="tg-0pky">Collection of performance graphics</td>
  </tr>
  <tr>
    <td class="tg-0pky" rowspan="5">Considerations</td>
    <td class="tg-0pky">Users</td>
    <td class="tg-0pky">Who are the intended users of the model?</td>
  </tr>
  <tr>
    <td class="tg-0pky">Use Cases</td>
    <td class="tg-0pky">What are the intended use cases of the model?</td>
  </tr>
  <tr>
    <td class="tg-0pky">Limitations</td>
    <td class="tg-0pky">What are the known technical limitations of the model? E.g. What kind(s) of data should the model be expected not to perform well on? What are the factors that might degrade model performance?</td>
  </tr>
  <tr>
    <td class="tg-0pky">Tradeoffs</td>
    <td class="tg-0pky">What are the known tradeoffs in accuracy/performance of the model?</td>
  </tr>
  <tr>
    <td class="tg-0pky">Ethical Considerations</td>
    <td class="tg-0pky">What are the ethical (or environmental) risks involved in the application of this model?</td>
  </tr>
</tbody>
</table>

## Steps to generate a Model Card

**Step 1**: Clone the GitHub repository.

```shell
git clone https://github.com/opea-project/GenAIEval.git
```

**Step 2**: Navigate to `model_card` directory.

```shell
cd evals/evaluation/lm_evaluation_harness/model_card/
```

**Step 3**: Choose a virtual environment to use: eg. Using virtualenv:

```shell
python3 -m virtualenv mg_venv
source mg_venv/bin/activate
```

**Step 4**: Install the required dependencies using `pip`.

```shell
pip install -r requirements.txt
```

**Step 5**: Prepare the input Model Card metadata JSON

Draft your Model Card metadata by following the specified [JSON schema](https://github.com/intel/intel-xai-tools/tree/main/model_card_gen/intel_ai_safety/model_card_gen/schema/v0.0.1/model_card.schema.json) and save the content in a `.json` file. Refer to the above table for sections and fields to include in the JSON file. You can add any fields that comply with the schema, but ensure the required field 'model name' is included."
For guidance, refer to example Model Card JSONs available [here](https://github.com/intel/intel-xai-tools/tree/main/model_card_gen/intel_ai_safety/model_card_gen/docs/examples/json). The path to Model Card metadata JSON should be provided to the `input_mc_metadata_json` argument. 

Optionally, specify the template for rendering the model card by replacing `MODEL_CARD_TEMPLATE` with either "html" for an interactive HTML model card or "md" for a static Markdown version. By default, the template type is set to HTML. 
Additionally, provide the directory path where the generated model card and related files should be saved using the `OUTPUT_DIRECTORY` argument.

```shell
INPUT_MC_METADATA_JSON_PATH=/path/to/model_card_metadata.json
MODEL_CARD_TEMPLATE="html"
OUTPUT_DIRECTORY=/path/to/output

python examples/main.py --input_mc_metadata_json ${INPUT_MC_METADATA_JSON_PATH} --mc_template_type ${MODEL_CARD_TEMPLATE} --output_dir ${OUTPUT_DIRECTORY}
```

**Step 6 (Optional)**: Generate Performance Metrics

Draft a Metrics by Threshold CSV file based on the generated metric results. To see examples of metric files, click [here](https://github.com/intel/intel-xai-tools/tree/main/model_card_gen/intel_ai_safety/model_card_gen/docs/examples/csv). 
For a step-by-step guide on creating these files, follow this [link](https://github.com/intel/intel-xai-tools/tree/main/notebooks/model_card_gen/hugging_face_model_card/hugging-face-model-card.ipynb). The "Metrics by Threshold" section of the Model Card enables you to visually analyze how metric values vary with different probability thresholds. 
Provide the path to the Metrics by Threshold CSV file using the `metrics_by_threshold` argument. 


Draft a Metrics by Group CSV file based on the generated metric results. To see examples of metric files, click [here](https://github.com/intel/intel-xai-tools/tree/main/model_card_gen/intel_ai_safety/model_card_gen/docs/examples/csv). 
For a step-by-step guide on creating these files, follow this [link](https://github.com/intel/intel-xai-tools/tree/main/notebooks/model_card_gen/hugging_face_model_card/hugging-face-model-card.ipynb). The "Metrics by Group" section of Model Card is used to organize and display a model's performance metrics by distinct groups or subcategories within the data. Provide the path to the Metrics by Group CSV file using the `metrics_by_group` argument. 

```shell
INPUT_MC_METADATA_JSON_PATH=/path/to/model_card_metadata.json
MODEL_CARD_TEMPLATE="html"
OUTPUT_DIRECTORY=/path/to/output
METRICS_BY_THRESHOLD=/path/to/metrics_by_threshold.csv
METRICS_BY_GROUP=/path/to/metrics_by_group.csv

python examples/main.py --input_mc_metadata_json ${INPUT_MC_METADATA_JSON_PATH} --mc_template_type ${MODEL_CARD_TEMPLATE} --output_dir ${OUTPUT_DIRECTORY} --metrics_by_threshold ${METRICS_BY_THRESHOLD} --metrics_by_group ${METRICS_BY_GROUP}
```

**Step 7 (Optional)**: Generate Metrics by Threshold for `lm_evaluation_harness`

Additionally, you can generate a `Metrics by Threshold` CSV for some of the `lm_evaluation_harness` tasks. Currently, we support the tasks that produce numeric metrics, like log probabilities or log likelihoods, to determine the best label in text generation and question answering scenarios. In the future, we aim to expand our parsing logic and the Model Card Generator to support a wider array of text generation tasks.

To generate Metrics by Threshold file for supported tasks, provide the path to the metric results JSONL file in place of `METRICS_RESULTS_PATH`.

```shell
INPUT_MC_METADATA_JSON_PATH=/path/to/model_card_metadata.json
MODEL_CARD_TEMPLATE="html"
OUTPUT_DIRECTORY=/path/to/output
METRICS_RESULTS_PATH=/path/to/metrics_results.jsonl

python ./examples/main.py --input_mc_metadata_json ${INPUT_MC_METADATA_JSON_PATH} --mc_template_type ${MODEL_CARD_TEMPLATE} --output_dir ${OUTPUT_DIRECTORY} --metric_results_path ${METRICS_RESULTS_PATH}
```

Consider an example of a result JSON file from an `lm_evaluation_harness` task as follows. 
```
[
  {
    "doc_id": 0,
    "target": "Neither",
    "arguments": [
      ["Lorem ipsum dolor sit amet, consectetur adipiscing elit", " True"],
      ["Lorem ipsum dolor sit amet, consectetur adipiscing elit", " Neither"],
      ["Lorem ipsum dolor sit amet, consectetur adipiscing elit", " False"]
    ],
    "filtered_resps": [
      [-10.0, false],
      [-9.0, false],
      [-11.0, false]
    ],
    "acc": 0.0
  },
  {
    "doc_id": 1,
    "target": "True",
    "arguments": [
     ["Lorem ipsum dolor sit amet, consectetur adipiscing elit", " True"],
      ["Lorem ipsum dolor sit amet, consectetur adipiscing elit", " Neither"],
      ["Lorem ipsum dolor sit amet, consectetur adipiscing elit", " False"]
    ],
    "filtered_resps": [
      [-12.0, false],
      [-10.5, false],
      [-13.0, false]
    ],
    "acc": 1.0
  },
  ...
]
```
The `filtered_resps` field contains log likelihoods for each response option, representing the model's confidence levels. When the path to this JSON file is specified in the `metric_results_path` argument, these log likelihood values are parsed and converted into probabilities using the softmax function. These probabilities are then used to calculate performance metrics across various thresholds, ranging from 0.0 to 1.0, and are compiled into the `metrics_by_threshold` CSV file which would look as follows:

| Threshold | Precision | Recall | F1 Score | Accuracy | Label   |
|-----------|-----------|--------|----------|----------|---------|
| 0.000     | 0.500     | 0.600  | 0.545    | 0.550    | True    |
| 0.001     | 0.510     | 0.610  | 0.556    | 0.560    | True    |
| ...       | ...       | ...    | ...      | ...      | ...     |
| 1.000     | 0.700     | 0.750  | 0.724    | 0.720    | True    |
| 0.000     | 0.400     | 0.500  | 0.444    | 0.450    | False   |
| 0.001     | 0.410     | 0.510  | 0.455    | 0.460    | False   |
| ...       | ...       | ...    | ...      | ...      | ...     |
| 1.000     | 0.600     | 0.650  | 0.624    | 0.620    | False   |
| 0.000     | 0.300     | 0.400  | 0.345    | 0.350    | Neither |
| 0.001     | 0.310     | 0.410  | 0.356    | 0.360    | Neither |
| ...       | ...       | ...    | ...      | ...      | ...   |
| 1.000     | 0.500     | 0.550  | 0.524    | 0.520    | Neither |

The `model_card_gen` tool uses the generated `metrics_by_threshold` dataframe to format and present the evaluation results in a comprehensive model card. 

You can find an example of a generated Model Card [here](https://github.com/intel/intel-xai-tools/tree/main/model_card_gen/intel_ai_safety/model_card_gen/docs/examples/html)
