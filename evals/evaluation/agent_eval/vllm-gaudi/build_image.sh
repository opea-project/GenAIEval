
echo "Building the vllm docker image"
cd $WORKDIR
echo $WORKDIR
if [ ! -d "./vllm-fork" ]; then
    git clone https://github.com/HabanaAI/vllm-fork.git
fi
cd ./vllm-fork
git checkout v0.6.4.post2+Gaudi-1.19.0
docker build --no-cache -f Dockerfile.hpu -t  vllm-gaudi:latest --shm-size=128g . --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy
if [ $? -ne 0 ]; then
    echo "vllm-gaudi:latest failed"
    exit 1
else
    echo "vllm-gaudi:latest successful"
fi
