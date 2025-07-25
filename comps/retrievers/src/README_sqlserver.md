# Retriever Microservice

This retriever microservice is a highly efficient search service designed for handling and retrieving embedding vectors. It operates by receiving an embedding vector as input and conducting a similarity search against vectors stored in a VectorDB database. Users must specify the VectorDB's URL and the index name, and the service searches within that index to find documents with the highest similarity to the input vector.

The service primarily utilizes similarity measures in vector space to rapidly retrieve contentually similar documents. The vector-based retrieval approach is particularly suited for handling large datasets, offering fast and accurate search results that significantly enhance the efficiency and quality of information retrieval.

Overall, this microservice provides robust backend support for applications requiring efficient similarity searches, playing a vital role in scenarios such as recommendation systems, information retrieval, or any other context where precise measurement of document similarity is crucial.

## 🚀1. Start Microservice with Python (Option 1)

To start the retriever microservice, you must first install the required python packages.

### 1.1 Install Requirements

```bash
pip install -r requirements.txt
```

### 1.2 Start TEI Service

```bash
model=BAAI/bge-base-en-v1.5
volume=$PWD/data
docker run -d --name tei-embedding-serving -p 6060:80 -v $volume:/data -e http_proxy=$http_proxy -e https_proxy=$https_proxy --pull always ghcr.io/huggingface/text-embeddings-inference:cpu-1.6 --model-id $model
```

### 1.3 Verify the TEI Service

Health check the embedding service with:

```bash
curl 127.0.0.1:6060/embed \
    -X POST \
    -d '{"inputs":"What is Deep Learning?"}' \
    -H 'Content-Type: application/json'
```

### 1.4 Setup VectorDB Service

You need to setup your own VectorDB service (SQLServer in this example), and ingest your knowledge documents into the vector database.

As for SQLServer, you could start a docker container using the following commands.
Remember to ingest data into it manually.

Please refer to this [readme](../../third_parties/sqlserver/src/README.md).

### 1.5 Start Retriever Service

```bash
export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:6060"
export RETRIEVER_COMPONENT_NAME="OPEA_RETRIEVER_SQLSERVER"
python opea_retrievers_microservice.py
```

## 🚀2. Start Microservice with Docker (Option 2)

### 2.1 Setup Environment Variables

```bash
export MSSQL_SA_PASSWORD='Passw0rd!'
export MSSQL_CONNECTION_STRING="DRIVER={ODBC Driver 18 for SQL Server};SERVER=${host_ip},1433;DATABASE=master;UID=sa;PWD=$MSSQL_SA_PASSWORD;TrustServerCertificate=yes"
export EMBED_MODEL=${your_embedding_model} # For example: "BAAI/bge-base-en-v1.5"
export TEI_EMBEDDING_ENDPOINT="http://${host_ip}:6060"
export HF_TOKEN=${your_huggingface_api_token}
export RETRIEVER_COMPONENT_NAME="OPEA_RETRIEVER_SQLSERVER"
```

### 2.2 Build Docker Image

```bash
cd ../../../
docker build -t opea/retriever:latest --build-arg https_proxy=$https_proxy --build-arg http_proxy=$http_proxy -f comps/retrievers/src/Dockerfile .
```

To start a docker container, you have two options:

- A. Run Docker with CLI
- B. Run Docker with Docker Compose

You can choose one as needed.

### 2.3 Run Docker with CLI (Option A)

```bash
docker run -d --name="retriever-sqlserver" -p 7000:7000 --ipc=host -e http_proxy=$http_proxy -e https_proxy=$https_proxy -e "MSSQL_CONNECTION_STRING=${MSSQL_CONNECTION_STRING}" -e TEI_ENDPOINT=$TEI_ENDPOINT -e RETRIEVER_COMPONENT_NAME=$RETRIEVER_COMPONENT_NAME opea/retriever:latest
```

### 2.4 Run Docker with Docker Compose (Option B)

```bash
cd ../deployment/docker_compose
export service_name="retriever-sqlserver"
docker compose -f compose.yaml up ${service_name} -d
```

## 🚀3. Consume Retriever Service

### 3.1 Check Service Status

```bash
curl http://localhost:7000/v1/health_check \
  -X GET \
  -H 'Content-Type: application/json'
```

### 3.2 Consume Retriever Service

To consume the Retriever Microservice, you can generate a mock embedding vector of length 768 with Python.

```bash
export your_embedding=$(python -c "import random; embedding = [random.uniform(-1, 1) for _ in range(768)]; print(embedding)")
curl http://${host_ip}:7000/v1/retrieval \
  -X POST \
  -d "{\"text\":\"What is the revenue of Nike in 2023?\",\"embedding\":${your_embedding}}" \
  -H 'Content-Type: application/json'
```
