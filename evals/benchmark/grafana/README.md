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
