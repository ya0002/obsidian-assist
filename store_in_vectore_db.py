import time
from pathlib import Path

import os
import pandas as pd

from langchain_text_splitters import MarkdownHeaderTextSplitter
import re

from utils.basic_utils import generate_unique_id
from utils.cleaning_utils import is_header_to_skip
from utils.chromaDB_Handler import ChromaDBHandler

CHROMA_DB_PATH = os.environ['CHROMA_DB_PATH']
# Initialize the database handler with the custom embedding function
vdb_handler = ChromaDBHandler(path=CHROMA_DB_PATH)
vdb_collection_name = os.environ['markdown_chunk_collection_vdb'] ## this is where we save the MD chunks from the PDF


from docling_core.types.doc import ImageRefMode, PictureItem, TableItem
from docling.datamodel.base_models import FigureElement, InputFormat, Table
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

IMAGE_RESOLUTION_SCALE = 2.0

pipeline_options = PdfPipelineOptions()
pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
pipeline_options.generate_page_images = True
pipeline_options.generate_picture_images = True

def dissect_markdown_with_images(markdown_text):
    """
    Dissects a markdown text with embedded images, replacing them with unique strings
    and extracting the image embeddings into a dictionary.

    Args:
        markdown_text (str): The markdown text containing image embeddings.

    Returns:
        tuple: Updated markdown text with references and a dictionary mapping references to embeddings.
    """
    image_pattern = r'!\[Image\]\((.*?)\)'  # Pattern to specifically match ![Image](data...)
    references = {}
    
    def replace_with_reference(match):
        image_data = match.group(0)  # Full matched string
        ref_key = f"<reference image {generate_unique_id()}>"
        references[ref_key] = image_data
        return ref_key

    updated_markdown = re.sub(image_pattern, replace_with_reference, markdown_text)
    return updated_markdown, references


def add_info_to_metadata(md_header_splits, filename='', vault_name=''):
    vault_dir = os.path.basename(vault_name)

    for doc in md_header_splits:
        ###add_image_embeddings_to_metadata
        if '![Image]' in doc.page_content:
            updated_text, image_dict = dissect_markdown_with_images(doc.page_content)
            doc.page_content = updated_text
            doc.metadata.update(image_dict)
        doc.metadata['filename'] = filename
        doc.metadata['vault_path'] = vault_name
        doc.metadata['vault_dir'] = vault_dir
    
    return md_header_splits

def filter_unwanted_headers(md_header_splits,headers_to_split_on):
    ## remove extra headers like references
    header_keys = {i[1] for i in headers_to_split_on}
    cleaned_md_header_splits = []

    for doc in md_header_splits:
        meta = doc.metadata
        
        keys_to_check = list(set(doc.metadata.keys()).intersection(header_keys))

        if not keys_to_check:
            cleaned_md_header_splits.append(doc)

        for k in keys_to_check:
            if not is_header_to_skip(meta[k]):
                cleaned_md_header_splits.append(doc)
            else:
                print(f'**********DROPPING HEADER: {meta[k]}***********')
    
    return cleaned_md_header_splits


def filter_on_content_length(md_header_splits,min_content = 20):
    ##exclude super short docs and further chunk super long docs
    filtered_md_header_splits = []

    for doc in md_header_splits:
        meta = doc.metadata
        page_content = doc.page_content

        ## skip docs whose content is less than min_content words
        if len(page_content.split(' '))<min_content:
            print(f'\n********DROPPING {meta} because it has less than {min_content} words.**')
            continue

        filtered_md_header_splits.append(doc)
    
    return filtered_md_header_splits


def markdown_to_chunks(md_content, filename,vault_name,filter_on_headers=False):
    '''function to chunk MD string to chunks on headers'''
    
    print("Creating Chunks")

    ## chunk MD on headers
    headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on,strip_headers=False)
    md_header_splits = markdown_splitter.split_text(md_content)
    
    md_header_splits = filter_on_content_length(md_header_splits,min_content = 20)

    ## remove headers like References, notes etc
    if filter_on_headers:
        md_header_splits = filter_unwanted_headers(md_header_splits,headers_to_split_on)
    
    print(f'GOT {len(md_header_splits)} chunks for {filename}')
    
    ## Store thinkgs like image encoding and filename in metadata of langchain document
    md_header_splits = add_info_to_metadata(md_header_splits,filename=filename,vault_name=vault_name)

    ## chunks info
    df_chunks_meta = pd.DataFrame(
        {
        'chunks_length':[len(i.page_content) for i in md_header_splits],
        'chunks_n_words':[len(i.page_content.split(' ')) for i in md_header_splits],
        'metadata':[i.metadata.get("Header 2",i.metadata.get("Header 1",i.metadata.get("Header 3"))) for i in md_header_splits]
        }
    )

    print(f'CHUNKS STATS:\n{df_chunks_meta.describe()}\n')
    print(df_chunks_meta.to_string())

    return md_header_splits

def convert_doc_to_markdown(source):
    '''read PDF and convert to MD with embedded images'''

    input_doc_path = Path(source)
    # output_dir = Path(save_root)

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    start_time = time.time()

    conv_res = doc_converter.convert(input_doc_path)

    # output_dir.mkdir(parents=True, exist_ok=True)
    # doc_filename = conv_res.input.file.stem

    end_time = time.time()

    md_dump = conv_res.document.export_to_markdown(image_mode=ImageRefMode.EMBEDDED)

    print(f'TIME TAKEN to convert doc to MD: {end_time - start_time}')

    return md_dump


def add_chunks_to_DB(md_header_splits):
    '''add to vector DB'''

    try:

        ids_to_save = [generate_unique_id() for _ in range(len(md_header_splits))]

        documents_to_save = []
        metadata_to_save = []

        for doc in md_header_splits:
            documents_to_save.append(doc.page_content)
            if doc.metadata:
                metadata_to_save.append(doc.metadata)
            else:
                metadata_to_save.append({'1':1})
        
        vdb_handler.add_to_collection(
            vdb_collection_name,
            ids=ids_to_save,
            documents=documents_to_save,
            metadatas=metadata_to_save
        )

        print(f'Successfully added chunks to the vector DB')
        return documents_to_save
    except Exception as e:
        print(f'ERROR while adding chunks to Vector DB:\n{e}')
        return []

def store_doc_to_vector_db(source,vault_name,filter_on_headers=False):
    '''store the given document to a vector DB'''
    filename = os.path.basename(source)
    print(f'Processing {filename} in store_doc_to_vector_db')

    if filename[-3:]!='.md':
        print("=========Converting to Markdown=======")
        ## convert doc to markdown string
        md_content = convert_doc_to_markdown(source)
    else:
        print("=========Reading Markdown file from source=======")
        # Open the Markdown file in read mode
        with open(source, "r", encoding="utf-8") as file:
            md_content = file.read()


    print("=========Chunking===================")
    ## chunk MD on headers
    md_header_splits = markdown_to_chunks(md_content,filename,vault_name,filter_on_headers=filter_on_headers)

    print("=========Saving to VDB==============")
    ## add chunks to vector DB
    chunks_content = add_chunks_to_DB(md_header_splits)

    return chunks_content

if __name__=="__main__":
    
    source = r"C:\Users\yusuf\Downloads\my projects\PDF2Obsidian_notes\sample_pdfs\Deep Neural Networks in Computational Neuroscience.pdf"
    vault_name = r'C:\Users\yusuf\Downloads\my projects\PDF2Obsidian_notes\sample_vault'
    
    chunks = store_doc_to_vector_db(source,vault_name)
    print(chunks)
    # filename = os.path.basename(source)

    