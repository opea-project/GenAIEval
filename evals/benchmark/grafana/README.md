# Setup Prometheus and Grafana to visualize microservice metrics

## 1. Setup Prometheus

We leverage existing Prometheus metrics supported by microservices. These metrics can be used to create Grafana dashboards.

```
wget https://github.com/prometheus/prometheus/releases/download/v2.52.0/prometheus-2.52.0.linux-amd64.tar.gz
tar -xvzf prometheus-2.52.0.linux-amd64.tar.gz
cd prometheus-2.52.0.linux-amd64/
```


`vim prometheus.yml`

Change the job target endpoint to the microservice you want to track metrics for. Make sure the service exposes a `/metrics` that follows Prometheus conventions.


Here is an example of exporting metrics data from a TGI microservice (inside a Kubernetes cluster) to Prometheus.

```yaml
# A scrape configuration containing exactly one endpoint to scrape:
# Here it's Prometheus itself.
scrape_configs:
  # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
  - job_name: "tgi"

    # metrics_path defaults to '/metrics'
    # scheme defaults to 'http'.

    static_configs:
      - targets: ["llm-dependency-svc.default.svc.cluster.local:9009"]
```

Next, run Prometheus server `nohup ./prometheus --config.file=./prometheus.yml &`.

You should now access `localhost:9090/targets?search=` to open the Prometheus UI.

### 1.1 Node Metrics (optional)

The Prometheus Node Exporter is required for collecting CPU/memory/network/storage metrics metrics. Deploy the Node Exporter via tarball by the [guide](https://prometheus.io/docs/guides/node-exporter/#installing-and-running-the-node-exporter). 

Or install it in a K8S cluster by the following commands:

Ensure namespace `monitoring` was created in your K8S environment.

```bash
git clone https://github.com/opea-project/GenAIEval.git
cd GenAIEval/evals/benchmark/grafana/
kubectl apply -f prometheus_node_exporter.yaml
```

Add the following configuration to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "prometheus-node-exporter"
    metrics_path: /metrics
    static_configs:
      - targets: ["<NODE1_IP>:9100", "<NODE2_IP>:9100", ...]
```

The following Grafana dashboards rely on Prometheus Node Exporter:
- cpu_grafana.json
- node_grafana.json

Tested on the Prometheus Node Exporter `0.16.0`.


### 1.2 Intel® Gaudi® Metrics (optional)

The Intel Gaudi Prometheus Metrics Exporter is required for collecting Intel® Gaudi® AI accelerator metrics. 

Follow the [guide](https://docs.habana.ai/en/latest/Orchestration/Prometheus_Metric_Exporter.html#deploying-prometheus-metric-exporter-in-docker) to deploy the metrics exporter in Docker.

Or install it in a K8S cluster by the following commands:

Ensure namespace `monitoring` was created in your K8S environment.

```bash
git clone https://github.com/opea-project/GenAIEval.git
cd GenAIEval/evals/benchmark/grafana/
kubectl apply -f prometheus_gaudi_exporter.yaml
```

Add the following configuration to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: "prometheus-gaudi-exporter"
    scrape_interval: 15s
    metrics_path: /metrics
    static_configs:
      - targets: ["<NODE1_IP>:41611", "<NODE2_IP>:41611", ...]
```

The following Grafana dashboard rely on Intel Gaudi Prometheus Metrics Exporter:
- gaudi_grafana.json

Tested on the Intel Gaudi Prometheus Metrics Exporter `1.17.0`.


Restart Prometheus after saving the changes.

## 2. Setup Grafana

Grafana provides numerous dashboards to visualize data from a data source. Here we introduce how to visualize TGI metrics.

```
wget https://dl.grafana.com/oss/release/grafana-11.0.0.linux-amd64.tar.gz
tar -zxvf grafana-11.0.0.linux-amd64.tar.gz
```

Run the grafana server

```
cd grafana-v11.0.0/
nohup ./bin/grafana-server &
```

To access the Grafana dashboard, point your browser to http://localhost:3000. You will need to login using the default credentials.

```
username: admin 
password: admin
```

If you have any Grafana installation issue please check this  [link](https://grafana.com/docs/grafana/latest/setup-grafana/installation/).


The next step is to configure the data source for Grafana to scrape metrics from. Click on the "Data Source" button, select Prometheus, and specify the Prometheus url `localhost:9090`. If the dashboard does not display data, under the `Other section` for the Data Source, change the HTTP method to `GET`.


## 3. Import Grafana Dashboard
After setup the Grafana server, then you can import a Grafana Dashboard through uploading a dashboard JSON file in the Grafana UI under `Home > Dashboards > Import dashboard`. You can use a file like [tgi_grafana.json](https://github.com/huggingface/text-generation-inference/blob/main/assets/tgi_grafana.json).
Open the dashboard, and you will see different panels displaying the metrics data.

In this folder, we also provides some Grafana dashboard JSON files for your reference. 
- `chatqna_megaservice_grafana.json`: A sample Grafana dashboard JSON file for visualizing the metrics of ChatQnA microservices. Selecting different job_name options in the top-left of the dashboard displays the metrics for the corresponding microservices.
- `tei_grafana.json`: A sample Grafana dashboard JSON file for visualizing TEI metrics.
- `tgi_grafana.json`: A sample Grafana dashboard JSON file for visualizing TGI metrics.
- `redis_grafana.json`: A sample Grafana dashboard JSON file for visualizing the Redis metrics. For importing the redis metrics, you need to add the new connection and Redis data source in Grafana. Please refer this [link](https://grafana.com/grafana/plugins/redis-datasource/?tab=installation) for more details.
- `gaudi_grafana.json`: (Deprecated) A sample Grafana dashboard JSON file for visualizing the Intel® Gaudi® AI accelerator metrics in a k8s cluster for compute workload.
- `gaudi_grafana_v2.json`: A sample Grafana dashboard JSON file for visualizing the Intel® Gaudi® AI accelerator metrics in a container cluster for compute workload.
- `cpu_grafana.json`: A sample Grafana dashboard JSON file for visualizing the CPU metrics.
- `node_grafana.json`: A sample Grafana dashboard JSON file for visualizing the node metrics.
