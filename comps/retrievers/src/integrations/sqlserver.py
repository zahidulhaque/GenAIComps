# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import pyodbc

from fastapi import HTTPException
from langchain_community.embeddings import HuggingFaceBgeEmbeddings, HuggingFaceInferenceAPIEmbeddings
from langchain_sqlserver.vectorstores import SQLServer_VectorStore
from langchain_huggingface import HuggingFaceEmbeddings

from comps import CustomLogger, EmbedDoc, OpeaComponent, OpeaComponentRegistry, ServiceType

from .config import MSSQL_SERVER, MSSQL_DATABASE, MSSQL_USERNAME, MSSQL_SA_PASSWORD, TABLE_NAME, TEI_EMBEDDING_ENDPOINT, EMBED_MODEL, HUGGINGFACEHUB_API_TOKEN

MSSQL_CONNECTION_STRING = f"DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={MSSQL_SERVER};DATABASE={MSSQL_DATABASE};UID={MSSQL_USERNAME};PWD={MSSQL_SA_PASSWORD};TrustServerCertificate=yes"

logger = CustomLogger("sqlserver_retrievers")
logflag = os.getenv("LOGFLAG", False)


@OpeaComponentRegistry.register("OPEA_RETRIEVER_SQLSERVER")
class OpeaSqlServerRetriever(OpeaComponent):
    """A specialized retriever component derived from OpeaComponent for SQL Server retriever services.

    Attributes:
        client (SQLServer): An instance of the SQLServer client for vector database operations.
    """

    def __init__(self, name: str, description: str, config: dict = None):
        super().__init__(name, ServiceType.RETRIEVER.name.lower(), description, config)

        self.embedder = self._initialize_embedder()
        self.MSSQL_CONNECTION_STRING = MSSQL_CONNECTION_STRING
        self.sqlserver_table_name = TABLE_NAME
        self.vector_db = self._initialize_client()
        health_status = self.check_health()
        if not health_status:
            logger.error("OpeaSqlServerRetriever health check failed.")

    def _initialize_embedder(self):
        if TEI_EMBEDDING_ENDPOINT:
            # create embeddings using TEI endpoint service
            if logflag:
                logger.info(f"[ init embedder ] TEI_EMBEDDING_ENDPOINT:{TEI_EMBEDDING_ENDPOINT}")
            if not HUGGINGFACEHUB_API_TOKEN:
                raise HTTPException(
                    status_code=400,
                    detail="You MUST offer the `HUGGINGFACEHUB_API_TOKEN` when using `TEI_EMBEDDING_ENDPOINT`.",
                )
            import requests

            response = requests.get(TEI_EMBEDDING_ENDPOINT + "/info")
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400, detail=f"TEI embedding endpoint {TEI_EMBEDDING_ENDPOINT} is not available."
                )
            model_id = response.json()["model_id"]
            embeddings = HuggingFaceInferenceAPIEmbeddings(
                api_key=HUGGINGFACEHUB_API_TOKEN, model_name=model_id, api_url=TEI_EMBEDDING_ENDPOINT
            )
        else:
            # create embeddings using local embedding model
            if logflag:
                logger.info(f"[ init embedder ] LOCAL_EMBEDDING_MODEL:{EMBED_MODEL}")
            embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
        return embeddings

    def _initialize_client(self) -> SQLServer_VectorStore:
        """Initializes the SQL server client."""
        vector_db = SQLServer_VectorStore(
            embedding_function=self.embedder,
            table_name=self.sqlserver_table_name,
            connection_string=self.MSSQL_CONNECTION_STRING,
            embedding_length=768
        )
        return vector_db

    def check_health(self) -> bool:
        """Checks the health of the retriever service.

        Returns:
            bool: True if the service is reachable and healthy, False otherwise.
        """
        if logflag:
            logger.info("[ check health ] start to check health of SQL Server")
        try:
            conn = pyodbc.connect(MSSQL_CONNECTION_STRING)
            conn.close()
            logger.info("[ check health ] Successfully connected to SQL Server!")
            return True
        except pyodbc.Error as e:
            if logflag:
                logger.info(f"Error connecting to MS SQL: {e}")
            return False

        except Exception as e:
            if logflag:
                logger.info(f"An unexpected error occurred: {e}")
            return False

    async def invoke(self, input: EmbedDoc) -> list:
        """Search the SQLServer index for the most similar documents to the input query.

        Args:
            input (EmbedDoc): The input query to search for.
        Output:
            list: The retrieved documents.
        """
        if logflag:
            logger.info(f"[ similarity search ] input: {input}")

        search_res = await self.vector_db.asimilarity_search_by_vector(embedding=input.embedding)

        if logflag:
            logger.info(f"[ similarity search ] search result: {search_res}")
        return search_res
