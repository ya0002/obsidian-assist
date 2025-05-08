from utils.chromaDB_Handler import ChromaDBHandler
import os


from utils.basic_utils import merge_dicts


from utils.LLMHandler import LLMHandler

from obsidian_graph.graph_builder import build_undirected_graph
from obsidian_graph.utils import bfs_upto_levels

import networkx as nx

import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)


CHROMA_DB_PATH = os.environ["CHROMA_DB_PATH"]
vdb_collection_name = os.environ["markdown_chunk_collection_vdb"]  ## this is where we save the MD chunks from the PDF
vdb_notes_collection_name = os.environ["markdown_notes_collection_vdb"]  ## this is where we save the LLM generated summary, title, vault_name

# Initialize the database handler with the custom embedding function
vdb_handler = ChromaDBHandler(path=CHROMA_DB_PATH)


def get_RAG_context(user_prompt, MAX_COSINE_DISTANCE=0.3,n_results=3):
    print(f'Getting Context for:{user_prompt} ')
    query_fields = ["documents", "distances", "metadatas"]

    results = vdb_handler.query_collection(
        vdb_notes_collection_name,
        query_texts=[user_prompt],
        n_results=n_results,
        include=query_fields,
        max_distance=MAX_COSINE_DISTANCE,
    )

    context = "\n".join(results["documents"][0])

    context_metadata = merge_dicts(results["metadatas"][0])
    # print(results["metadatas"],context_metadata)

    return context, context_metadata.get("title")


def gr_chat(message, history, MAX_COSINE_DISTANCE,provider, model_name):
    # Combine the history into a single string for context
    history_text = ""
    for turn in history:
        role = turn.get("role", "")
        content = turn.get("content", "")
        history_text += f"{role.capitalize()}: {content}\n"

    # Retrieve context related to the current question
    context, reference = get_RAG_context(message, 
                                         MAX_COSINE_DISTANCE=MAX_COSINE_DISTANCE,
                                         n_results=3
                                         )

    # Get historical context
    query = f"{history_text}User: {message}"
    context_with_history, reference_with_history = get_RAG_context(query, 
                                                                   MAX_COSINE_DISTANCE=MAX_COSINE_DISTANCE,
                                                                   n_results=2
                                                                   )
    if reference is not None and reference_with_history is not None:
        reference.extend(reference_with_history)
    else:
        reference = reference or reference_with_history

    print(reference)

    if reference==None:
        return "Couldn't find reference to answer your query. Maybe loosen the similarity threshold?"

    if context is not None and context_with_history is not None:
        context += '\n' + context_with_history
    elif context is not None or context_with_history is not None:
        context = context or context_with_history

    # Construct the user prompt with history and context
    user_prompt = f"{history_text}User: {message}\n\nCONTEXT:\n{context}"

    llm = LLMHandler(provider=provider,model_name=model_name)

    # Generate response using your LLM
    response = llm.generate(
        system_prompt="Answer the user query in markdown. You are a professional assistant.",
        user_prompt=user_prompt,
    )

    reference_formatted = "\n- ".join(reference)
    response += f"\n\n## Reference\n- {reference_formatted}"

    return response


def gr_chat_graph(
    message, 
    history, 
    MAX_COSINE_DISTANCE, 
    provider, 
    notes, 
    start, 
    end, 
    hops, 
    model_name
):

    graph = build_undirected_graph(notes)
    print(graph.nodes)

    # Combine the history into a single string for context
    history_text = ""
    for turn in history:
        role = turn.get("role", "")
        content = turn.get("content", "")
        history_text += f"{role.capitalize()}: {content}\n"

    references = []
    ## make sure to remove the base64 image from content
    if start == "None":
        ##get starting node
        # Retrieve context related to the current question
        context, reference = get_RAG_context(
            message, MAX_COSINE_DISTANCE=MAX_COSINE_DISTANCE, n_results=1
        )

        if reference == None:
            return "Couldn't find reference to answer your query. Maybe loosen the similarity threshold or try selecting different start and ends?"

        if isinstance(reference, list):
            reference = reference[0]

        reference = [i for i in notes.keys() if reference in i][0]

        visited_nodes = bfs_upto_levels(
            graph=graph, start_node=reference, max_levels=hops
        )
        logging.info(f"FOUND {len(visited_nodes)} after {hops} hops from {reference}")
        logging.info(f"Visited nodes with levels: {visited_nodes}")

    elif start != "None" and end == "None":
        ## use start and hop
        visited_nodes = bfs_upto_levels(graph=graph, start_node=start, max_levels=hops)
        logging.info(f"FOUND {len(visited_nodes)} after {hops} hops from {start}")
        logging.info(f"Visited nodes with levels: {visited_nodes}")

    elif start != "None" and end != "None":
        try:
            ## use the shortest path b/w them to build context
            references = nx.shortest_path(graph, source=start, target=end)
        except Exception as e:
            logging.info(e)
            return f"No path between {start} and {end}."

    max_reference = 10
    if not references:
        references = [node[0] for node in visited_nodes][:max_reference]

    print(references)

    if references == None:
        return "Couldn't find reference to answer your query. Maybe loosen the similarity threshold or try selecting different start and ends?"

    context = ""
    for r in references:
        context += notes[r]["content"]

    # Construct the user prompt with history and context
    user_prompt = f"{history_text}User: {message}\n\nCONTEXT:\n{context}"

    llm = LLMHandler(provider=provider, model_name=model_name)

    # Generate response using your LLM
    response = llm.generate(
        system_prompt="Answer the user query in markdown. You are a professional assistant.",
        user_prompt=user_prompt,
    )

    reference_formatted = "\n- ".join(references)
    response += f"\n\n## Reference\n- {reference_formatted}"

    return response
