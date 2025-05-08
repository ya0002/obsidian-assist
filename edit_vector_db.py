import os

from utils.chromaDB_Handler import ChromaDBHandler

CHROMA_DB_PATH = os.environ["CHROMA_DB_PATH"]
vdb_collection_name = os.environ[
    "markdown_chunk_collection_vdb"
]  ## this is where we save the MD chunks from the PDF
vdb_notes_collection_name = os.environ[
    "markdown_notes_collection_vdb"
]  ## this is where we save the LLM generated summary, title, vault_name

# Initialize the database handler with the custom embedding function
vdb_handler = ChromaDBHandler(path=CHROMA_DB_PATH)

import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)


def get_all_used_filenames():
    """
    This function returns a list of all the files whose chunks are stored 
    in the vdb_collection_name VDB
    """
    results = vdb_handler.get_in_collection(vdb_collection_name, include=["metadatas"])
    all_files = {metadata["filename"] for metadata in results["metadatas"]}
    return list(all_files)


def delete_selected_file(filename_to_del):
    try:
        results = vdb_handler.get_in_collection(
            vdb_collection_name,
            include=["metadatas"],
            where={
                "filename": {"$eq": filename_to_del}
                # "$and": [
                #     {"vault_path": {"$eq": vault_name}},
                #     {"filename": {"$eq": filename_to_del}},
                # ]
            },
        )

        logging.info(f'Deleting {len(results["metadatas"])} chunks for {filename_to_del}.')

        ids_to_del = results["ids"]

        logging.info(f"ids to delete: {ids_to_del}")

        vdb_handler.delete_from_collection(
            collection_name=vdb_collection_name,
            ids=ids_to_del
        )

        logging.info(f"DELETED!")
    except Exception as e:
        logging.warning(f'Failed to delete {filename_to_del}')
