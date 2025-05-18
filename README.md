# Obsidian Assist

![image](./images/readme_cover.png)

**Note:** *This project is experimental and primarily a hobby endeavor.*

**`obsidian-assist`** aims to make **Zettelkasten-style note-taking** the foundation of interactions with Large Language Models (LLMs). By using an **Obsidian vault as the backend**, users retain full control over the relationships between notes, enabling them to explicitly define, edit, and guide context-building for LLM responses.

Obsidian is often used as a "second brain"—this tool aspires to be a way to **interact with that second brain**, allowing for intelligent and personalized dialogue grounded in the user’s own knowledge graph.

## Overview

This tool supports two primary use cases:

---

### 1. Automatic Conversion of Documents into Obsidian Notes

Automatically convert PDFs, PowerPoint presentations, and Markdown files into structured, connected notes within Obsidian. This process leverages **Docling** and **Large Language Models (LLMs)**:

- **Docling** is used to convert PDFs and PPTs into Markdown format.
- The resulting Markdown files are then segmented and analyzed using LLMs and Vector Databases.
- Each segment is transformed into an individual, interlinked note to support a connected note-taking workflow in Obsidian.

<iframe width="560" height="315" src="https://www.youtube.com/embed/JVaCnP9epLs?si=B0j5eKWLuZHntn3L" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

---

### 2. Analysis and Interaction with an Obsidian Vault

Interact with and analyze the contents of an Obsidian vault through two distinct methods:

- **Cosine Similarity Search**  
  A generic semantic search method using cosine distance to retrieve contextually relevant notes.

- **Graph-Based Contextual Search**  
  Utilizes user-defined relationships (graph edges) between notes to build contextual understanding. This method offers three interaction modes:
  
  1. **Auto Node Traversal**  
     Start chatting directly — the system identifies the most relevant node to your query and traverses its neighboring nodes to build context.
  
  2. **Fixed Start Node**  
     Specify a starting node — responses are centered around this predefined note.
  
  3. **Start-to-End Path Search**  
     Specify both a start and end node — the shortest path between them is used to build the context for the response.

<iframe width="560" height="315" src="https://www.youtube.com/embed/wP2JzcK-qpg?si=3dMe23_F4nh3SXOk" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>



---

## Supported LLM Handlers

1. Ollama
2. Gemini
3. Huggingface

## Running with Docker

### Create a .env file with credentials in the same directory

```
CHROMA_DB_PATH=/app/ChromaDB
HF_TOKEN=your_actual_token
markdown_chunk_collection_vdb=md_chunk_vdb
markdown_notes_collection_vdb=md_notes_vdb
GEMINI_KEY=your_gemini_api_key
OLLAMA_HOST=http://host.docker.internal:11434
NVIDIA_VISIBLE_DEVICES=all
NVIDIA_DRIVER_CAPABILITIES=compute,utility
```

<!-- then run for first time

```docker
docker-compose up --build
```

To restart
```
docker compose up
``` -->

### For GPU

Make sure you have the NVIDIA Container Toolkit installed on your host machine. You can verify this by checking if the `nvidia-smi` command works in your terminal.

```docker
### build: 
docker compose build --no-cache
### start: 
docker compose up
```

### For CPU

```docker
### build: 
docker compose -f docker-compose.cpu.yml build --no-cache
### start: 
docker compose -f docker-compose.cpu.yml up
```


## Mount paths to access your files

### Linux/Mac Downloads directory
```${HOME:-/home}/Downloads:/home/Downloads```

### Windows Downloads directory

For windows, the image is mounted to the Downloads folder

```${USERPROFILE:-C:\Users}/Downloads:/windows/Downloads```

You provide the source file like

`/windows/Downloads/some.md OR some.pdf OR some.pptx`

Or you can provide a directory full of PDFs/PPTs/MDs

`/windows/Downloads/some_dir`

Your vault path would be like

`/windows/Downloads/obsidian__vault_dir`

### For macOS, which may have Downloads in a different location

```${HOME}/Downloads:/mac/Downloads```

## Running with conda

Make sure to set the environment variables.

Create an environment
```
$ conda create -n obsdidian python=3.11
```

Install requirements.txt
```

$ conda activate obsdidian

$ pip install --no-cache-dir --no-deps -r requirements.txt
```

Run the app
```
$ python app.py
```