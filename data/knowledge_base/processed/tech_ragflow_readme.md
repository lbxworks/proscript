```json
{
  "source_id": "tech_ragflow_readme",
  "title": "RAGFlow GitHub README",
  "platform": "ragflow",
  "platform_display": "RAGFlow",
  "region": "GLOBAL",
  "region_pack": "GLOBAL",
  "document_type": "technical_reference",
  "source_category": "technical_reference",
  "language": "en",
  "source_url": "https://github.com/infiniflow/ragflow",
  "priority": "P1",
  "notes": "RAGFlow capability baseline for ingestion, chunking and citation features.",
  "raw_file": "data/knowledge_base/raw/tech_ragflow_readme.html",
  "processed_at": "2026-04-05T07:17:13.164998+00:00",
  "parser_version": "rag-normalizer-v1",
  "doc_id": "tech_ragflow_readme",
  "source_title": "RAGFlow GitHub README",
  "source_type": "policy",
  "country_code": "",
  "distribution_mode": "all",
  "brand_id": "all",
  "block_id": "tech_ragflow_readme",
  "is_global_fallback": true,
  "html_title": "GitHub - infiniflow/ragflow: RAGFlow is a leading open-source Retrieval-Augmented Generation (RAG) engine that fuses cutting-edge RAG with Agent capabilities to create a superior context layer for LLMs · GitHub",
  "meta_description": "RAGFlow is a leading open-source Retrieval-Augmented Generation (RAG) engine that fuses cutting-edge RAG with Agent capabilities to create a superior context layer for LLMs - infiniflow/ragflow"
}
```

# RAGFlow GitHub README

#### [Document](https://ragflow.io/docs/dev/) | [Roadmap](https://github.com/infiniflow/ragflow/issues/12241) | [Twitter](https://twitter.com/infiniflowai) | [Discord](https://discord.gg/NjYzJD3GM3) | [Demo](https://cloud.ragflow.io)

**📕 Table of Contents**

- 💡 [What is RAGFlow?](#-what-is-ragflow)
- 🎮 [Demo](#-demo)
- 📌 [Latest Updates](#-latest-updates)
- 🌟 [Key Features](#-key-features)
- 🔎 [System Architecture](#-system-architecture)
- 🎬 [Get Started](#-get-started)
- 🔧 [Configurations](#-configurations)
- 🔧 [Build a Docker image](#-build-a-docker-image)
- 🔨 [Launch service from source for development](#-launch-service-from-source-for-development)
- 📚 [Documentation](#-documentation)
- 📜 [Roadmap](#-roadmap)
- 🏄 [Community](#-community)
- 🙌 [Contributing](#-contributing)

## 💡 What is RAGFlow?

[RAGFlow](https://ragflow.io/) is a leading open-source Retrieval-Augmented Generation ([RAG](https://ragflow.io/basics/what-is-rag)) engine that fuses cutting-edge RAG with Agent capabilities to create a superior context layer for LLMs. It offers a streamlined RAG workflow adaptable to enterprises of any scale. Powered by a converged [context engine](https://ragflow.io/basics/what-is-agent-context-engine) and pre-built agent templates, RAGFlow enables developers to transform complex data into high-fidelity, production-ready AI systems with exceptional efficiency and precision.

## 🎮 Demo

Try our demo at <https://cloud.ragflow.io>.

## 🔥 Latest Updates

- 2025-12-26 Supports 'Memory' for AI agent.
- 2025-11-19 Supports Gemini 3 Pro.
- 2025-11-12 Supports data synchronization from Confluence, S3, Notion, Discord, Google Drive.
- 2025-10-23 Supports MinerU & Docling as document parsing methods.
- 2025-10-15 Supports orchestrable ingestion pipeline.
- 2025-08-08 Supports OpenAI's latest GPT-5 series models.
- 2025-08-01 Supports agentic workflow and MCP.
- 2025-05-23 Adds a Python/JavaScript code executor component to Agent.
- 2025-05-05 Supports cross-language query.
- 2025-03-19 Supports using a multi-modal model to make sense of images within PDF or DOCX files.

## 🎉 Stay Tuned

⭐️ Star our repository to stay up-to-date with exciting new features and improvements! Get instant notifications for new
releases! 🌟

## 🌟 Key Features

### 🍭 **"Quality in, quality out"**

- [Deep document understanding](/infiniflow/ragflow/blob/main/deepdoc/README.md)-based knowledge extraction from unstructured data with complicated
  formats.
- Finds "needle in a data haystack" of literally unlimited tokens.

### 🍱 **Template-based chunking**

- Intelligent and explainable.
- Plenty of template options to choose from.

### 🌱 **Grounded citations with reduced hallucinations**

- Visualization of text chunking to allow human intervention.
- Quick view of the key references and traceable citations to support grounded answers.

### 🍔 **Compatibility with heterogeneous data sources**

- Supports Word, slides, excel, txt, images, scanned copies, structured data, web pages, and more.

### 🛀 **Automated and effortless RAG workflow**

- Streamlined RAG orchestration catered to both personal and large businesses.
- Configurable LLMs as well as embedding models.
- Multiple recall paired with fused re-ranking.
- Intuitive APIs for seamless integration with business.

## 🔎 System Architecture

## 🎬 Get Started

### 📝 Prerequisites

- CPU >= 4 cores
- RAM >= 16 GB
- Disk >= 50 GB
- Docker >= 24.0.0 & Docker Compose >= v2.26.1
- [gVisor](https://gvisor.dev/docs/user_guide/install/): Required only if you intend to use the code executor (sandbox) feature of RAGFlow.

### 🚀 Start up the server

1. Ensure `vm.max_map_count` >= 262144:

   > To check the value of `vm.max_map_count`:
   >
   > ```
   > $ sysctl vm.max_map_count
   > ```
   >
   > Reset `vm.max_map_count` to a value at least 262144 if it is not.
   >
   > ```
   > # In this case, we set it to 262144:
   > $ sudo sysctl -w vm.max_map_count=262144
   > ```
   >
   > This change will be reset after a system reboot. To ensure your change remains permanent, add or update the
   > `vm.max_map_count` value in **/etc/sysctl.conf** accordingly:
   >
   > ```
   > vm.max_map_count=262144
   > ```
2. Clone the repo:

   ```
   $ git clone https://github.com/infiniflow/ragflow.git
   ```
3. Start up the server using the pre-built Docker images:

> The command below downloads the `v0.24.0` edition of the RAGFlow Docker image. See the following table for descriptions of different RAGFlow editions. To download a RAGFlow edition different from `v0.24.0`, update the `RAGFLOW_IMAGE` variable accordingly in **docker/.env** before using `docker compose` to start the server.

```
   $ cd ragflow/docker

   # git checkout v0.24.0
   # Optional: use a stable tag (see releases: https://github.com/infiniflow/ragflow/releases)
   # This step ensures the **entrypoint.sh** file in the code matches the Docker image version.

   # Use CPU for DeepDoc tasks:
   $ docker compose -f docker-compose.yml up -d

   # To use GPU to accelerate DeepDoc tasks:
   # sed -i '1i DEVICE=gpu' .env
   # docker compose -f docker-compose.yml up -d
```

> Note: Prior to `v0.22.0`, we provided both images with embedding models and slim images without embedding models. Details as follows:

| RAGFlow image tag | Image size (GB) | Has embedding models? | Stable? |
| --- | --- | --- | --- |
| v0.21.1 | ≈9 | ✔️ | Stable release |
| v0.21.1-slim | ≈2 | ❌ | Stable release |

> Starting with `v0.22.0`, we ship only the slim edition and no longer append the **-slim** suffix to the image tag.

4. Check the server status after having the server up and running:

   ```
   $ docker logs -f docker-ragflow-cpu-1
   ```

   *The following output confirms a successful launch of the system:*

   ```
         ____   ___    ______ ______ __
        / __ \ /   |  / ____// ____// /____  _      __
       / /_/ // /| | / / __ / /_   / // __ \| | /| / /
      / _, _// ___ |/ /_/ // __/  / // /_/ /| |/ |/ /
     /_/ |_|/_/  |_|\____//_/    /_/ \____/ |__/|__/

    * Running on all addresses (0.0.0.0)
   ```

   > If you skip this confirmation step and directly log in to RAGFlow, your browser may prompt a `network abnormal`
   > error because, at that moment, your RAGFlow may not be fully initialized.
5. In your web browser, enter the IP address of your server and log in to RAGFlow.

   > With the default settings, you only need to enter `http://IP_OF_YOUR_MACHINE` (**sans** port number) as the default
   > HTTP serving port `80` can be omitted when using the default configurations.
6. In [service\_conf.yaml.template](/infiniflow/ragflow/blob/main/docker/service_conf.yaml.template), select the desired LLM factory in `user_default_llm` and update
   the `API_KEY` field with the corresponding API key.

   > See [llm\_api\_key\_setup](https://ragflow.io/docs/dev/llm_api_key_setup) for more information.

   *The show is on!*

## 🔧 Configurations

When it comes to system configurations, you will need to manage the following files:

- [.env](/infiniflow/ragflow/blob/main/docker/.env): Keeps the fundamental setups for the system, such as `SVR_HTTP_PORT`, `MYSQL_PASSWORD`, and
  `MINIO_PASSWORD`.
- [service\_conf.yaml.template](/infiniflow/ragflow/blob/main/docker/service_conf.yaml.template): Configures the back-end services. The environment variables in this file will be automatically populated when the Docker container starts. Any environment variables set within the Docker container will be available for use, allowing you to customize service behavior based on the deployment environment.
- [docker-compose.yml](/infiniflow/ragflow/blob/main/docker/docker-compose.yml): The system relies on [docker-compose.yml](/infiniflow/ragflow/blob/main/docker/docker-compose.yml) to start up.

> The [./docker/README](/infiniflow/ragflow/blob/main/docker/README.md) file provides a detailed description of the environment settings and service
> configurations which can be used as `${ENV_VARS}` in the [service\_conf.yaml.template](/infiniflow/ragflow/blob/main/docker/service_conf.yaml.template) file.

To update the default HTTP serving port (80), go to [docker-compose.yml](/infiniflow/ragflow/blob/main/docker/docker-compose.yml) and change `80:80`
to `<YOUR_SERVING_PORT>:80`.

Updates to the above configurations require a reboot of all containers to take effect:

> ```
> $ docker compose -f docker-compose.yml up -d
> ```

### Switch doc engine from Elasticsearch to Infinity

RAGFlow uses Elasticsearch by default for storing full text and vectors. To switch to [Infinity](https://github.com/infiniflow/infinity/), follow these steps:

1. Stop all running containers:

   ```
   $ docker compose -f docker/docker-compose.yml down -v
   ```

2. Set `DOC_ENGINE` in **docker/.env** to `infinity`.
3. Start the containers:

   ```
   $ docker compose -f docker-compose.yml up -d
   ```

## 🔧 Build a Docker image

This image is approximately 2 GB in size and relies on external LLM and embedding services.

```
git clone https://github.com/infiniflow/ragflow.git
cd ragflow/
docker build --platform linux/amd64 -f Dockerfile -t infiniflow/ragflow:nightly .
```

Or if you are behind a proxy, you can pass proxy arguments:

```
docker build --platform linux/amd64 \
  --build-arg http_proxy=http://YOUR_PROXY:PORT \
  --build-arg https_proxy=http://YOUR_PROXY:PORT \
  -f Dockerfile -t infiniflow/ragflow:nightly .
```

## 🔨 Launch service from source for development

1. Install `uv` and `pre-commit`, or skip this step if they are already installed:

   ```
   pipx install uv pre-commit
   ```
2. Clone the source code and install Python dependencies:

   ```
   git clone https://github.com/infiniflow/ragflow.git
   cd ragflow/
   uv sync --python 3.12 # install RAGFlow dependent python modules
   uv run download_deps.py
   pre-commit install
   ```
3. Launch the dependent services (MinIO, Elasticsearch, Redis, and MySQL) using Docker Compose:

   ```
   docker compose -f docker/docker-compose-base.yml up -d
   ```

   Add the following line to `/etc/hosts` to resolve all hosts specified in **docker/.env** to `127.0.0.1`:

   ```
   127.0.0.1       es01 infinity mysql minio redis sandbox-executor-manager
   ```
4. If you cannot access HuggingFace, set the `HF_ENDPOINT` environment variable to use a mirror site:

   ```
   export HF_ENDPOINT=https://hf-mirror.com
   ```
5. If your operating system does not have jemalloc, please install it as follows:

   ```
   # Ubuntu
   sudo apt-get install libjemalloc-dev
   # CentOS
   sudo yum install jemalloc
   # OpenSUSE
   sudo zypper install jemalloc
   # macOS
   sudo brew install jemalloc
   ```
6. Launch backend service:

   ```
   source .venv/bin/activate
   export PYTHONPATH=$(pwd)
   bash docker/launch_backend_service.sh
   ```
7. Install frontend dependencies:

   ```
   cd web
   npm install
   ```
8. Launch frontend service:

   ```
   npm run dev
   ```

   *The following output confirms a successful launch of the system:*
9. Stop RAGFlow front-end and back-end service after development is complete:

   ```
   pkill -f "ragflow_server.py|task_executor.py"
   ```

## 📚 Documentation

- [Quickstart](https://ragflow.io/docs/dev/)
- [Configuration](https://ragflow.io/docs/dev/configurations)
- [Release notes](https://ragflow.io/docs/dev/release_notes)
- [User guides](https://ragflow.io/docs/category/user-guides)
- [Developer guides](https://ragflow.io/docs/category/developer-guides)
- [References](https://ragflow.io/docs/dev/category/references)
- [FAQs](https://ragflow.io/docs/dev/faq)

## 📜 Roadmap

See the [RAGFlow Roadmap 2026](https://github.com/infiniflow/ragflow/issues/12241)

## 🏄 Community

- [Discord](https://discord.gg/NjYzJD3GM3)
- [Twitter](https://twitter.com/infiniflowai)
- [GitHub Discussions](https://github.com/orgs/infiniflow/discussions)

## 🙌 Contributing

RAGFlow flourishes via open-source collaboration. In this spirit, we embrace diverse contributions from the community.
If you would like to be a part, review our [Contribution Guidelines](https://ragflow.io/docs/dev/contributing) first.
