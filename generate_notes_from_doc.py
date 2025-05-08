import os

from utils.chromaDB_Handler import ChromaDBHandler
from utils.LLMHandler import LLMHandler
from utils.basic_utils import (
    generate_unique_id,
    extract_and_parse_json,
    merge_dicts,
    replace_references,
    write_to_markdown,
    generate_unique_hash,
    process_path
)
from prompts import system_prompt

import time
import re

CHROMA_DB_PATH = os.environ["CHROMA_DB_PATH"]
vdb_collection_name = os.environ[
    "markdown_chunk_collection_vdb"
]  ## this is where we save the MD chunks from the PDF
vdb_notes_collection_name = os.environ[
    "markdown_notes_collection_vdb"
]  ## this is where we save the LLM generated summary, title, vault_name

# Initialize the database handler with the custom embedding function
vdb_handler = ChromaDBHandler(path=CHROMA_DB_PATH)

from store_in_vectore_db import store_doc_to_vector_db, dissect_markdown_with_images


def sync_vdb_wit_vault_recursive(vault_name):
    """
    Add and delete from VDB to match its records with the vault and sub vaults to avoid
    creating dead link and to not miss out on any potential links
    """

    try:
        print(
            f"Syncing Notes DB with Deletions and Additions in the Vault and Sub Vaults."
        )
        all_md_files_in_vault, all_md_files_to_vault_path = [], dict()
        all_vaults = set()
        ## walk through the vault dir and find all the .md files
        for root, _, files in os.walk(vault_name):
            all_vaults.add(root)
            for fname in files:
                if fname.lower().endswith(".md"):
                    # full_path = os.path.join(root, fname)
                    all_md_files_in_vault.append(fname)
                    all_md_files_to_vault_path[fname] = root  ## used during addition
        all_vaults = list(all_vaults)
        all_md_files_in_vault_without_suffix = [i[:-3] for i in all_md_files_in_vault]

        ## get all records
        results = vdb_handler.get_in_collection(
            vdb_notes_collection_name,
            include=["metadatas"],
            where={"vault_path": {"$in": all_vaults}},
        )

        print(f"Number of files in the vault: {len(all_md_files_in_vault)}")
        print(f'Number of records in Notes DB: {len(results["ids"])}')

        ids_to_del = []
        all_valid_titles = []

        # ==========deletion===========
        for id, meta in zip(results["ids"], results["metadatas"]):
            title = meta["title"]
            # print(id, title)

            ## deleting a record from ChromaDB because that note was deleted in Obsidan vault by the user
            if title not in all_md_files_in_vault_without_suffix:
                print(f"DELETING: {title}")
                ids_to_del.append(id)
            else:
                all_valid_titles.append(title)

        if ids_to_del:
            vdb_handler.delete_from_collection(
                collection_name=vdb_notes_collection_name, ids=ids_to_del
            )

        # ===============Addition=================
        for exisitng_vault_file in all_md_files_in_vault:
            ## adding a record in ChromaDB because that note was created in Obsidan vault by the user
            exisitng_vault_file_no_suffix = exisitng_vault_file[:-3]
            if exisitng_vault_file_no_suffix not in all_valid_titles:
                print(f"ADDING: {exisitng_vault_file}")
                print("=========Reading Markdown file from source=======")
                # Open the Markdown file in read mode(NEEDS correct vault path: TODO)
                source = os.path.join(
                    all_md_files_to_vault_path[exisitng_vault_file], exisitng_vault_file
                )
                with open(source, "r", encoding="utf-8") as file:
                    md_content = file.read()
                if "![Image]" in md_content:
                    updated_text, image_dict = dissect_markdown_with_images(md_content)
                    md_content = updated_text

                # add to notes vector DB
                vdb_handler.add_to_collection(
                    vdb_notes_collection_name,
                    ids=[generate_unique_id()],
                    documents=[md_content],
                    metadatas=[
                        {
                            "title": exisitng_vault_file_no_suffix,
                            "vault_path": all_md_files_to_vault_path[
                                exisitng_vault_file
                            ],
                            "vault_dir": os.path.basename(
                                all_md_files_to_vault_path[exisitng_vault_file]
                            ),
                        }
                    ],
                )
    except Exception as e:
        print(f"Failed to sync DB with Vault.\nError: {e}")


def sync_vdb_wit_vault(vault_name):
    """
    Add and delete from VDB to match its records with the vault to avoid
    creating dead link and to not miss out on any potential links
    """

    try:
        print(f"Syncing Notes DB with Deletions and Additions in the Vault.")
        all_md_files_in_vault = [i for i in os.listdir(vault_name) if i[-3:] == ".md"]
        all_md_files_in_vault_without_suffix = [i[:-3] for i in all_md_files_in_vault]

        ## get all records
        results = vdb_handler.get_in_collection(
            vdb_notes_collection_name,
            include=["metadatas"],
            where={"vault_path": {"$eq": vault_name}},
        )

        print(f"Number of files in the vault: {len(all_md_files_in_vault)}")
        print(f'Number of records in Notes DB: {len(results["ids"])}')

        ids_to_del = []
        all_valid_titles = []

        # ==========deletion===========
        for id, meta in zip(results["ids"], results["metadatas"]):
            title = meta["title"]
            # print(id, title)

            ## deleting a record from ChromaDB because that note was deleted in Obsidan vault by the user
            if title not in all_md_files_in_vault_without_suffix:
                print(f"DELETING: {title}")
                ids_to_del.append(id)
            else:
                all_valid_titles.append(title)

        if ids_to_del:
            vdb_handler.delete_from_collection(
                collection_name=vdb_notes_collection_name, ids=ids_to_del
            )

        # ===============Addition=================
        for exisitng_vault_file in all_md_files_in_vault:
            ## adding a record in ChromaDB because that note was created in Obsidan vault by the user
            exisitng_vault_file_no_suffix = exisitng_vault_file[:-3]
            if exisitng_vault_file_no_suffix not in all_valid_titles:
                print(f"ADDING: {exisitng_vault_file}")
                print("=========Reading Markdown file from source=======")
                # Open the Markdown file in read mode
                source = os.path.join(vault_name, exisitng_vault_file)
                with open(source, "r", encoding="utf-8") as file:
                    md_content = file.read()
                if "![Image]" in md_content:
                    updated_text, image_dict = dissect_markdown_with_images(md_content)
                    md_content = updated_text

                # add to notes vector DB
                vdb_handler.add_to_collection(
                    vdb_notes_collection_name,
                    ids=[generate_unique_id()],
                    documents=[md_content],
                    metadatas=[
                        {
                            "title": exisitng_vault_file_no_suffix,
                            "vault_path": vault_name,
                            "vault_dir": os.path.basename(vault_name),
                        }
                    ],
                )
    except Exception as e:
        print(f"Failed to sync DB with Vault.\nError: {e}")


def format_to_MD_and_save(
    response_dict, context_metadata, vault_name, 
    reference_image_text, tags,
    restrict_to_vault=True,
    MAX_COSINE_DISTANCE=2.0
):
    try:
        final_md_to_write = tags

        source_file_names = []
        if isinstance(context_metadata.get("filename"),list):
            source_file_names = [
                re.sub(r"\.(md|pdf|pptx)$", "", i).replace(" ", "_")
                for i in context_metadata.get("filename", [])
            ]
        elif isinstance(context_metadata.get("filename"),str):
            source_file_names = [
                re.sub(
                    r"\.(md|pdf|pptx)$", "", context_metadata.get("filename")
                ).replace(" ", "_")
            ]

        final_md_to_write += (
            "\n#### Abstracted from documents\n#"
            + "\n#".join(source_file_names)
            + "\n\n"
        )

        ## summary
        final_md_to_write += response_dict.get("detailed_explanation")

        if response_dict.get("important_snippets"):
            final_md_to_write += "\n## Important Snippets\n" + response_dict.get("important_snippets")

        if response_dict.get("tables"):
            final_md_to_write += "\n## Tables\n" + response_dict.get("tables")

        ## save the final_md_to_write_here after querying the table and adding the links

        # Query the collection for related notes
        vdb_notes_collection_where = None
        if restrict_to_vault:
            vdb_notes_collection_where = {"vault_path": {"$eq": vault_name}}

        related_notes = vdb_handler.query_collection(
            vdb_notes_collection_name,
            query_texts=[final_md_to_write],
            n_results=3,
            include=["metadatas", "distances"],
            where=vdb_notes_collection_where,
            max_distance=MAX_COSINE_DISTANCE
        )

        ## add links if possible
        if related_notes["metadatas"][0]:
            reference_titles = merge_dicts(related_notes["metadatas"][0]).get("title")
            if isinstance(reference_titles, list):
                reference_titles = [f"[[{item}]]" for item in reference_titles]
                reference_titles = "\n".join(reference_titles)
            else:
                reference_titles = f"[[{reference_titles}]]"

            final_md_to_write += f"\n\n# Related notes\n{reference_titles}"

        ## layman explanation
        print('\nresponse keys:',response_dict.keys())
        print('\nSIMPLE explanation:\n',response_dict.get("simple_explanation"),'\n')
        if response_dict.get("simple_explanation"):
            final_md_to_write += f'\n\n## Simple explanation\n{response_dict.get("simple_explanation")}\n'

        final_md_to_write_without_images = final_md_to_write

        ## add image if possible
        if reference_image_text:
            final_md_to_write += "\n## Pictures\n" + reference_image_text

        sanitized_stem, sanitized_filename = write_to_markdown(
            content=final_md_to_write,
            filename=response_dict["title"],
            save_dir=vault_name,
            mode="w",
            encoding="utf-8",
        )

        print(f"ADDED: {sanitized_stem}\nFULL PATH: {sanitized_filename}")

        # add to notes vector DB
        vdb_handler.add_to_collection(
            vdb_notes_collection_name,
            ids=[generate_unique_id()],
            documents=[final_md_to_write_without_images],
            metadatas=[
                {
                    "title": sanitized_stem,
                    "vault_path": vault_name,
                    "vault_dir": os.path.basename(vault_name),
                }
            ],
        )
    except Exception as e:
        print(f"ERROR in format_to_MD_and_save:\n{e}")


def generate_notes(
    chunks,
    vault_name,
    provider,
    model_name,
    MAX_LLM_RETRY=3,
    sleep_time=5,
    tags="",
    restrict_to_vault=True,
    MAX_COSINE_DISTANCE=2.0
):
    """iterate through those chunks and generate notes"""

    try:
        used_chunks = (
            []
        )  ## if a string is present in this then skip(use generate_unique_hash for encoding)

        # fo a vector search on chunk iteratively
        for idx, chunk in enumerate(chunks):
            chunk_number = idx+1

            print(
                f"==============ON {chunk_number}/{len(chunks)}===================================="
            )

            try:
                ## chek if this chunk can be skipped
                chunk_hash = generate_unique_hash(chunk)

                if chunk_hash in used_chunks:
                    print(f"++++++SKIPPING since this chunk was already used.")
                    continue

                ## query chunk DB to get context
                vdb_collection_where = None
                if restrict_to_vault:
                    vdb_collection_where = {"vault_path": {"$eq": vault_name}}

                results = vdb_handler.query_collection(
                    vdb_collection_name,
                    query_texts=[chunk],
                    n_results=5,
                    include=["documents", "distances", "metadatas"],
                    where=vdb_collection_where,
                    max_distance=MAX_COSINE_DISTANCE
                )

                context_metadata = merge_dicts(results["metadatas"][0])

                if len(context_metadata) == 0:
                    print(
                        f"+++++++++++++SKIPPING due to no related chunks in vector DB:\n{chunk}"
                    )
                    continue

                ## Use LLM to generate notes
                user_prompt = "\n".join(results["documents"][0])

                llm = LLMHandler(provider=provider, model_name=model_name)

                retry_counter = 0
                response_dict = None
                ## sleep between request to API to avoid hitting rate limit
                time.sleep(sleep_time)
                while retry_counter < MAX_LLM_RETRY and not isinstance(
                    response_dict, dict
                ):
                    retry_counter += 1
                    try:
                        response = llm.generate(
                            system_prompt=system_prompt, user_prompt=user_prompt
                        )
                        print(f'LLM generation complete: attempt {retry_counter}')
                        response_dict = extract_and_parse_json(response)
                        print(f'succesfully converted LLM response to dict on attempt {retry_counter}')
                    except Exception as e:
                        print(f"^^^^^^^^^ERROR in LLM generation on attempt {retry_counter}: {e}")

                if not isinstance(response_dict, dict):
                    print(
                        f"+++++++++++++++++++SKIPPING due to invalid LLM response:\nCHUNK: {chunk}\nresponse_dict: {response_dict}"
                    )
                    continue

                ## replace image <reference > label with its embedding
                reference_image_text = replace_references(
                    text=response_dict.get("reference image"),
                    reference_dict=context_metadata,
                )
                print(f'DONE: replace image <reference > label with its embedding')

                ## add generated tags
                all_tags = tags + ' '+ response_dict.get("tags", "")

                response_dict["title"] = f'{chunk_number}__{response_dict.get("title")}'

                format_to_MD_and_save(
                    response_dict=response_dict,
                    context_metadata=context_metadata,
                    vault_name=vault_name,
                    reference_image_text=reference_image_text,
                    tags=all_tags,
                    restrict_to_vault=restrict_to_vault,
                    MAX_COSINE_DISTANCE=MAX_COSINE_DISTANCE
                )

                ## record the chunk
                used_chunks.append(chunk_hash)

                ## record retrieved chunks being used to avoid duplication of notes on the same topic
                for retrieved_chunk in results["documents"][0]:
                    used_chunks.append(generate_unique_hash(retrieved_chunk))

            except Exception as e:
                print(f"ERROR while generating note for the chunk:{chunk}\nreason:{e}")

    except Exception as e:
        print(f"ERROR while generating notes : {e} ")


def main(
    source,
    vault_name,
    filter_on_headers,
    provider,
    model_name,
    MAX_LLM_RETRY,
    sleep_time,
    tags,
    restrict_to_vault=True,
    MAX_COSINE_DISTANCE=0.2
):

    ## sync the noted DB(used for creating links) with changes in vault
    sync_vdb_wit_vault(vault_name)
    
    ## handle for directory
    all_files_to_process = process_path(source)
    
    ## store doc in vector DB
    for source_file in all_files_to_process:
        chunks = store_doc_to_vector_db(
            source_file, vault_name, filter_on_headers=filter_on_headers
        )

        generate_notes(
            chunks=chunks,
            vault_name=vault_name,
            provider=provider,
            model_name=model_name,
            MAX_LLM_RETRY=MAX_LLM_RETRY,
            sleep_time=sleep_time,
            tags=tags,
            restrict_to_vault=restrict_to_vault,
            MAX_COSINE_DISTANCE=MAX_COSINE_DISTANCE
        )

    print("======NOTE GENERATION COMPLETE=======")


if __name__ == "__main__":

    ###=========user input=================
    filter_on_headers = True
    MAX_LLM_RETRY = 3
    sleep_time = 5
    source = r"C:\Users\yusuf\Downloads\my projects\PDF2Obsidian_notes\sample_pdfs\A tactile discrimination task to study neuronal dynamics in freely.pdf"
    vault_name = r"C:\Users\yusuf\Downloads\my projects\PDF2Obsidian_notes\sample_vault"

    provider = "gemini"
    model_name = "gemini-1.5-flash"
    tags = "#neuroscience #mice_experiment"

    # provider="huggingface"
    # model_name="Qwen/Qwen2.5-72B-Instruct"
    ####====================
    # main(source,vault_name,filter_on_headers,provider,model_name,MAX_LLM_RETRY,sleep_time,tags)

    ## store doc in vector DB
    # chunks = store_doc_to_vector_db(source,vault_name,filter_on_headers=filter_on_headers)

    # generate_notes(chunks=chunks,
    #                vault_name=vault_name,
    #                provider=provider,
    #                model_name=model_name,
    #                MAX_LLM_RETRY=MAX_LLM_RETRY,
    #                sleep_time=sleep_time,
    #                tags=tags
    #                )
