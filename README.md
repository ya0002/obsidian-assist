# Obsidian Notes Generator

![image](./images/readme_cover.png)

A tool to automatically convert any PDF, PPTs and Markdown files to connected notes in Obsidian with the help of Docling and LLMs.

It uses Docling to convert PDFs/PPTs to Markdown files and then those Markdown files are further segmented and analyzed with LLMs and VectorDBs to create content for each note. 

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