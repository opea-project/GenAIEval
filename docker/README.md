# GenAIEval Dockerfiles

Dockerfiles are provided along with related GenAIEval scripts. 

## Gaudi Requirements
Please make sure to follow [Driver Installation](https://docs.habana.ai/en/latest/Installation_Guide/Driver_Installation.html) to install Gaudi driver on the system.
To use dockerfile provided for the sample, please follow [Docker Installation](https://docs.habana.ai/en/latest/Installation_Guide/Additional_Installation/Docker_Installation.html) to setup habana runtime for Docker images.

## Run GenAIEval on Gaudi 
### Docker Build
To build the image from the Dockerfile for Gaudi, please follow below command to build the opea/genai-eval image.
```bash
docker build --no-cache -t opea/genai-eval:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy --build-arg no_proxy=$no_proxy -f hpu.dockerfile .
```
### Docker Run
After docker build, users could follow below command to run and docker instance and users will be in the docker instance under text-generation folder.
```bash
docker run -it --name opea-eval --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none   --cap-add=ALL --privileged=true -v /var/run/docker.sock://var/run/docker.sock --net=host --ipc=host opea/genai-eval:latest
```

## Benchmarking OPEA Examples on Intel&reg; Gaudi&reg; AI Processor and Xeon&reg; Processor
Benchmark script will use different yaml file to run the benchmark on Gaudi or Xeon. 
### Docker Build
To build the image from the Dockerfile for OPEA examples benchmarking, please follow below command to build the opea/genai-eval-benchmark image.
```bash
docker build --no-cache -t opea/genai-eval-benchmark:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy --build-arg no_proxy=$no_proxy -f benchmark.dockerfile .
```
### Run a OPEA Example using docker compose
Follow the OPEA Example docker compose README to run a OPEA example for benchmarking.  

### Docker Run
After docker build, follow below command to run and docker instance under OPEA example default network.
#### Xeon
```bash
docker run -it --name opea-eval -v /var/run/docker.sock://var/run/docker.sock --net=xeon_default --ipc=host opea/genai-eval-benchmark:latest
```
#### Gaudi
```bash
docker run -it --name opea-eval -v /var/run/docker.sock://var/run/docker.sock --net=gaudi_default --ipc=host opea/genai-eval-benchmark:latest
```
> [!NOTE]
> The Huggingface model file size might be large, so we recommend to use an external disk as Huggingface hub folder. \
> Please export HF_HOME environment variable to your external disk and then export the mount point into docker instance. \
> ex: "-e HF_HOME=/mnt/huggingface -v /mnt:/mnt"  
> To use Huggingface models, HF_TOKEN needs to be exported as environment variable. \
> ex: "-e HF_TOKEN=${HUGGINGFACEHUB_API_TOKEN}"

#### Run the Benchmark
#### Xeon
```bash
python3 benchmark.py --yaml docker.cpu.benchmark.yaml
```
#### Gaudi
```bash
python3 benchmark.py --yaml docker.hpu.benchmark.yaml
```
