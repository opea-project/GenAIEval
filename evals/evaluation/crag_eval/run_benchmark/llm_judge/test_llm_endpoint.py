from langchain_huggingface import HuggingFaceEndpoint
import os

host_ip=os.environ.get("host_ip", "localhost")
url = "http://{host_ip}:8085".format(host_ip=host_ip)
print(url)

model = HuggingFaceEndpoint(
    endpoint_url=url,
    task="text-generation",
    max_new_tokens=10,
    do_sample=False,
)

print(model.invoke("what is deep learing?"))
