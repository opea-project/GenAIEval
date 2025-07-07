FROM python:3.11-slim

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN pip install --no-cache-dir --upgrade pip setuptools==70.0.0

RUN useradd -m -s /bin/bash user && \
    mkdir -p /home/user && \
    chown -R user /home/user/ 

COPY ./ /home/user/rag_pilot

USER user

WORKDIR /home/user/rag_pilot
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

ENTRYPOINT ["python3", "-m", "server"]
