# LLM OVMS Microservice

LLM OVMS microservice uses [OpenVINO Model Server](https://github.com/openvinotoolkit/model_server). It can efficient generate text on Intel CPU using a set of optimizations techniques list continuous batching, paged attention, prefix caching, speculative decoding and many other.

---

## Table of Contents

1. [Start OVMS Microservice](#start-ovms-microservice)
2. [Start OPEA LLM Microservice](#start-opea-llm-microservice)
3. [Consume Microservice](#consume-microservice)
4. [Tips](#tips)

---

## Start OVMS Microservice

### Prepare Models

To start the OVMS service, you need to export models from Hugging Face Hub to the IR format. This step optionally includes quantization, which speeds up service startup and prevents repeated downloads.

```bash
  pip3 install -r https://raw.githubusercontent.com/openvinotoolkit/model_server/refs/heads/releases/2025/0/demos/common/export_models/requirements.txt
  curl https://raw.githubusercontent.com/openvinotoolkit/model_server/refs/heads/releases/2025/0/demos/common/export_models/export_model.py -o export_model.py
  mkdir models
  python export_model.py text-generation --source_model Qwen/Qwen2-7B-Instruct --weight-format int8 --config_file_path models/config_llm.json --model_repository_path models --target_device CPU
```

Change the `source_model` as needed.

### Start the OVMS container:

Replace `your_port` with desired values to start the service.

```bash
your_port=8090
docker run -p $your_port:8000 -v ./models:/models --name ovms-llm-serving \
openvino/model_server:2025.0 --port 8000 --config_path /models/config_llm.json
```

### Test the OVMS container:

OVMS exposes REST API compatible with OpenAI API. Both `completions` and `chat/completions` are supported.
Run the following command to check if the service is up and running.

```bash
 curl -s http://localhost:8090/v3/chat/completions   \
 -H "Content-Type: application/json"   \
 -d '{
 "model": "Qwen/Qwen2-7B-Instruct",
 "max_tokens":30, "temperature":0,
 "stream":false,
 "messages": [
   {
     "role": "system",
     "content": "You are a helpful assistant."
   },
   {
     "role": "user",
     "content": "What are the 3 main tourist attractions in Paris?"
   }
 ]
 }'
```

---

## Start OPEA LLM Microservice

### Building the image

```bash
cd ../../../../../
docker build -t opea/llm-textgen-ovms:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/llms/src/text-generation/Dockerfile .
```

To start a docker container, you have two options:

- A. Run Docker with CLI
- B. Run Docker with Docker Compose

You can choose one as needed.

### Option A: Run Docker with CLI

```bash
export LLM_ENDPOINT=http://localhost:8090
export MODEL_ID=Qwen/Qwen2-7B-Instruct
docker run -d --name="llm-ovms-server" -p 9000:9000  \
-e MODEL_ID=${MODEL_ID} \
-e LLM_COMPONENT_NAME=OpeaTextGenOVMS \
-e OVMS_LLM_ENDPOINT=${LLM_ENDPOINT} \
opea/llm-textgen-ovms:latest
```

### Option B: Run Docker with Docker Compose

```bash
export service_name="textgen-ovms"
cd comps/llms/deployment/docker_compose
docker compose -f compose_text-generation.yaml up ${service_name} -d
```

---

## Consume Microservice

### Check Service Status

```bash
curl http://localhost:9000/v1/health_check\
  -X GET \
  -H 'Content-Type: application/json'
```

### Consume LLM Service

```bash
curl http://localhost:9000/v1/chat/completions\
  -X POST \
  -d '{"messages":"What is Deep Learning?"}' \
  -H 'Content-Type: application/json'
```

```bash
curl http://localhost:9000/v1/chat/completions\
  -X POST \
  -d '{"messages":"What is Deep Learning?", "stream": true}' \
  -H 'Content-Type: application/json'
```

---

## Tips

1. Port Mapping:
   Ensure the ports are correctly mapped to avoid conflicts with other services.

2. Model Selection:
   Choose a model appropriate for your use case, like "Qwen/Qwen2-7B-Instruct".
   It should be exported to the models repository and set in 'MODEL_ID' env in the deployment of the OPEA API wrapper.

3. Models repository Volume:
   The `-v ./models:/models` flag ensures the models directory is correctly mounted.

4. Select correct configuration JSON file
   Models repository can host multiple models. Choose the models to be served by selecting the right configuration file.
   In the example above `config_llms.json`

5. Upload the models to persistent volume claim in Kubernetes
   Models repository with configuration JSON file will be mounted in the OVMS containers when deployed via [helm chart](../../../third_parties/ovms/deployment/kubernetes/README.md).

6. Learn more about [OVMS chat/completions API](https://docs.openvino.ai/2025/model-server/ovms_docs_rest_api_chat.html)
