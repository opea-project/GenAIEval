# Benchmarking OPEA Examples on Intel&reg; Gaudi&reg; AI Processor and Xeon&reg; Processor
An Dockerfile is provided along with related GenAIEval benchmark scripts. 

## Gaudi Requirements
Please make sure to follow [Driver Installation](https://docs.habana.ai/en/latest/Installation_Guide/Driver_Installation.html) to install Gaudi driver on the system.
To use dockerfile provided for the sample, please follow [Docker Installation](https://docs.habana.ai/en/latest/Installation_Guide/Additional_Installation/Docker_Installation.html) to setup habana runtime for Docker images.

### Docker Build
To build the image from the Dockerfile for Gaudi, please follow below command to build the optimum-habana-text-gen image.
```bash
docker build --no-cache -t opea/genai-eval:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f hpu.dockerfile .
```
To build the image from the Dockerfile for Xeon, please follow below command to build the optimum-habana-text-gen image.
```bash
docker build --no-cache -t opea/genai-eval:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f cpu.dockerfile .
```
### Docker Run
After docker build, users could follow below command to run and docker instance and users will be in the docker instance under text-generation folder.
```bash
docker run -it --runtime=habana -e HABANA_VISIBLE_DEVICES=all -e OMPI_MCA_btl_vader_single_copy_mechanism=none   --cap-add=ALL --privileged=true  --net=host --ipc=host opea/genai-eval:latest
```
> [!NOTE]
> The Huggingface model file size might be large, so we recommend to use an external disk as Huggingface hub folder. \
> Please export HF_HOME environment variable to your external disk and then export the mount point into docker instance. \
> ex: "-e HF_HOME=/mnt/huggingface -v /mnt:/mnt"
