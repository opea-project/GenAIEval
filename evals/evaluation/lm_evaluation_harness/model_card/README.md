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

**Step 5**: Prepare Model Card JSON

Draft your Model Card by following the specified [JSON schema](https://github.com/intel/intel-xai-tools/blob/main/model_card_gen/intel_ai_safety/model_card_gen/schema/v0.0.1/model_card.schema.json) and save the content in a `.json` file. You can add any fields as long as they comply with the schema, but ensure required field of model name is included. 
For guidance, refer to example Model Card JSONs available [here](https://github.com/intel/intel-xai-tools/tree/main/model_card_gen/intel_ai_safety/model_card_gen/docs/examples/json). The path to Model Card JSON should be provided to the `model_card_json_path` argument. 

Optionally, specify the template for rendering the model card by replacing `MODEL_CARD_TEMPLATE` with either "html" for an interactive HTML model card or "md" for a static Markdown version. By default, the template type is set to HTML. 
Additionally, provide the directory path where the generated model card and related files should be saved using the `OUTPUT_DIRECTORY` argument.

```shell
MC_JSON_PATH=/path/to/model_card.json
MODEL_CARD_TEMPLATE="html"
OUTPUT_DIRECTORY=/path/to/output

python examples/main.py --model_card_json_path ${MC_JSON_PATH} --mc_template_type ${MODEL_CARD_TEMPLATE} --output_dir ${OUTPUT_DIRECTORY}
```

**Step 6 (Optional)**: Generate Performance Metrics

Draft a Metrics by Threshold CSV file based on the generated metric results. To see examples of metric files, click [here](https://github.com/intel/intel-xai-tools/tree/main/model_card_gen/intel_ai_safety/model_card_gen/docs/examples/csv). 
For a step-by-step guide on creating these files, follow this [link](https://github.com/intel/intel-xai-tools/blob/main/notebooks/model_card_gen/hugging_face_model_card/hugging-face-model-card.ipynb). The "Metrics by Threshold" section of the Model Card enables you to visually analyze how metric values vary with different probability thresholds. 
Provide the path to the Metrics by Threshold CSV file using the `metrics_by_threshold` argument. 


Draft a Metrics by Group CSV file based on the generated metric results. To see examples of metric files, click [here](https://github.com/intel/intel-xai-tools/tree/main/model_card_gen/intel_ai_safety/model_card_gen/docs/examples/csv). 
For a step-by-step guide on creating these files, follow this [link](https://github.com/intel/intel-xai-tools/blob/main/notebooks/model_card_gen/hugging_face_model_card/hugging-face-model-card.ipynb). The "Metrics by Group" section of Model Card is used to organize and display a model's performance metrics by distinct groups or subcategories within the data. Provide the path to the Metrics by Group CSV file using the `metrics_by_group` argument. 

```shell
MC_JSON_PATH=/path/to/model_card.json
MODEL_CARD_TEMPLATE="html"
OUTPUT_DIRECTORY=/path/to/output
METRICS_BY_THRESHOLD=/path/to/metrics_by_threshold.csv
METRICS_BY_GROUP=/path/to/metrics_by_group.csv

python examples/main.py --model_card_json_path ${MC_JSON_PATH} --mc_template_type ${MODEL_CARD_TEMPLATE} --output_dir ${OUTPUT_DIRECTORY} --metrics_by_threshold ${METRICS_BY_THRESHOLD} --metrics_by_group ${METRICS_BY_GROUP}
```

**Step 7 (Optional)**: Optional Step to generate Metrics by Threshold for `lm_evaluation_harness`

Additionally, you can generate a Metrics by Threshold CSV for some of the `lm_evaluation_harness` tasks by providing the path to the metric results JSONL file in place of `METRICS_RESULTS_PATH`.

```shell
MC_JSON_PATH=/path/to/model_card.json
MODEL_CARD_TEMPLATE="html"
OUTPUT_DIRECTORY=/path/to/output
METRICS_RESULTS_PATH=/path/to/metrics_results.jsonl

python ./examples/main.py --model_card_json_path ${MC_JSON_PATH} --mc_template_type ${MODEL_CARD_TEMPLATE} --output_dir ${OUTPUT_DIRECTORY} --metric_results_path ${METRICS_RESULTS_PATH}
```
