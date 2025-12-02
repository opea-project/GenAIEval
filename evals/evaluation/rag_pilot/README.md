# 🚀 RAG Pilot - A RAG Pipeline Tuning Tool

## 📖 Overview

RAG Pilot provides a set of tuners to optimize various parameters in a retrieval-augmented generation (RAG) pipeline. Each tuner allows fine-grained control over key aspects of parsing, chunking, postporcessing, and generating selection, enabling better retrieval and response generation.

## 🌐 Quickstart Guide

### ⚙️ Dependencies and Environment Setup

#### Setup EdgeCraftRAG

Setup EdgeCraftRAG pipeline based on this [link](https://github.com/opea-project/GenAIExamples/tree/main/EdgeCraftRAG).

Load documents in EdgeCraftRAG before running RAG Pilot.

#### Setup RAG Pilot

```bash

# Build RAG Pilot and UI docker images
cd rag_pilot
docker build --build-arg HTTP_PROXY=$HTTP_PROXY --build-arg HTTP_PROXYS=$HTTP_PROXYS --build-arg NO_PROXY=$NO_PROXY -t opea/ragpilot:latest -f ./Dockerfile .
docker build --build-arg HTTP_PROXY=$HTTP_PROXY --build-arg HTTP_PROXYS=$HTTP_PROXYS --build-arg NO_PROXY=$NO_PROXY -t opea/ragpilot-ui:latest -f ./ui/Dockerfile.ui .
# Or build docker images by build.sh
cd ./rag_pilot/docker_image_build
docker compose -f build.yaml build
# Setup ENV

# If you want to set HOST_IP in command lines instead of in UI 
#export ECRAG_SERVICE_HOST_IP=${HOST_IP} # HOST IP of EC-RAG Service, usually current host ip

# If EC-RAG Service port is not default
#export ECRAG_SERVICE_PORT=16010

# If you want to change exposed RAG Pilot UI port
#export RAGPILOT_UI_SERVICE_PORT=8090

# If you want to change exposed RAG Pilot service port
#export RAGPILOT_SERVICE_PORT=

#Start RAG Pilor server
cd ./rag_pilot
docker compose -f docker_compose/intel/gpu/arc/compose.yaml up -d
```


About how to use RAG Pilot and more details, please refer to this [doc](./docs/Detail_Guide.md) for details.
