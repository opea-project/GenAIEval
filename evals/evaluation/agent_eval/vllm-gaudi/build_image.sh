
echo "Building the vllm docker image"
cd $WORKDIR
echo $WORKDIR
if [ ! -d "./vllm-fork" ]; then
    git clone https://github.com/HabanaAI/vllm-fork.git
fi
cd ./vllm-fork
docker build --no-cache -f Dockerfile.hpu -t  vllm-gaudi:latest --shm-size=128g . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
if [ $? -ne 0 ]; then
    echo "opea/vllm-gaudi:comps failed"
    exit 1
else
    echo "opea/vllm-gaudi:comps successful"
fi
