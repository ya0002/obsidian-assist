import chromadb
from chromadb.utils import embedding_functions

import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)

class ChromaDBHandler:
    def __init__(self, path="chroma_store", embedding_model="all-MiniLM-L6-v2"):
        self.client = chromadb.PersistentClient(
            path=path,
            # settings=Settings(),
            # tenant="default_tenant",
            # database="default_database"
        )

        logging.info("Initializing embedding function.")
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        logging.info("Initialized embedding function.")

    def create_collection(self, collection_name):
        """Creates or retrieves a collection with the specified embedding function."""
        return self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={
                "hnsw:space": "cosine",
                "hnsw:search_ef": 100
            }
        )

    def add_to_collection(self, collection_name, ids, documents, metadatas=None):
        """Adds documents to the specified collection."""
        collection = self.create_collection(collection_name)
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

    def query_collection(self, collection_name, query_texts, n_results=5, 
                         include=["metadatas", "documents", "distances"], 
                         where=None, max_distance=2.0
                         ):
        """Queries the specified collection."""
        collection = self.create_collection(collection_name)
        results = collection.query(
            query_texts=query_texts,
            n_results=n_results,
            include=include,
            where=where
        )

        if max_distance!=2.0:
            results = self._filter_results_by_distance(results, max_distance=max_distance)

        return results

    def get_in_collection(self, collection_name, n_results=None, include=["metadatas", "documents"], where=None):
        """SELECT record from the specified collection """
        collection = self.create_collection(collection_name)
        results = collection.get(
            limit=n_results,
            include=include,
            where=where
        )
        return results

    def delete_collection(self, collection_name):
        """Deletes the specified collection."""
        self.client.delete_collection(name=collection_name)

    def list_collections(self):
        """Lists all collections."""
        return self.client.list_collections()

    def delete_from_collection(self, collection_name, ids):
        """Deletes documents with the specified IDs from the collection."""
        collection = self.create_collection(collection_name)
        collection.delete(ids=ids)

    def update_in_collection(self, collection_name, ids, documents=None, metadatas=None):
        """Updates documents and/or metadata for the specified IDs in the collection."""
        collection = self.create_collection(collection_name)
        collection.update(ids=ids, documents=documents, metadatas=metadatas)

    def _filter_results_by_distance(self, results, max_distance=2.0):
        """
        Filters results based on a maximum cosine distance.

        Parameters:
            results (dict): Dictionary containing various fields as keys, with their values structured as lists.
            max_distance (float): Maximum allowed cosine distance.

        Returns:
            dict: Filtered results containing only entries with distances <= max_distance.
        """
        # Get all keys from the results dictionary to dynamically determine query fields.
        query_fields = results.keys()

        # Initialize the filtered result dictionary with an empty list for each query field.
        distance_filtered_result = {field: [[]] if isinstance(results.get(field),list) else None for field in query_fields}

        # Determine the length of the first valid field.
        length_of_existing_fields = max((len(v[0]) for v in results.values() if v!=None and v[0]), default=0)

        # Iterate over all entries by zipping together the corresponding values from each query field.
        for entries in zip(*(results[field][0] if results.get(field)!=None else [None] * length_of_existing_fields for field in query_fields)):
            # Create a dictionary mapping field names to their corresponding values for the current entry.
            entry_dict = dict(zip(query_fields, entries))

            # Check if the distance value exists and is within the allowed maximum distance.
            if entry_dict.get('distances') is not None and entry_dict['distances'] <= max_distance:
                # Append the corresponding values to the filtered result for each query field.
                for field in query_fields:
                    if distance_filtered_result[field]!=None:
                        distance_filtered_result[field][0].append(entry_dict[field])

        return distance_filtered_result
