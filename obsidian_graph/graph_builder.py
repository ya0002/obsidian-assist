import networkx as nx


def build_directed_graph(notes):
    """
    Constructs a directed graph (DiGraph) from a collection of notes.

    Parameters:
    - notes (dict): A dictionary where each key is a note title, and each value is a dictionary containing:
        - 'metadata' (dict): Metadata attributes for the note.
        - 'tags' (list): A list of tags associated with the note.
        - 'wikilinks' (list): A list of strings representing links to other notes. Each link may include:
            - A title (e.g., 'Other Note')
            - An optional section (e.g., 'Other Note#Section')
            - An optional alias (e.g., 'Other Note|Alias')

    Returns:
    - G (networkx.DiGraph): A directed graph where:
        - Each node represents a note, labeled by its title, with associated metadata and tags.
        - Each edge represents a link from one note to another, based on the wikilinks.
    """
    # Initialize an empty directed graph
    G = nx.DiGraph()

    # Iterate over each note and its associated data
    for note_title, data in notes.items():
        # Add the note as a node in the graph, including its metadata and tags as attributes
        G.add_node(note_title, **data["metadata"], tags=data["tags"])
        print(f'ON {note_title}')
        # Process each wikilink in the current note
        for link in data["wikilinks"]:
            linked_note = data["corrected_wikilinks"][link]
            if linked_note:
                print(note_title, '-->',linked_note)
                G.add_edge(note_title,linked_note)

            # # Extract the linked note's title by removing any alias ('|') and section ('#') parts
            # linked_note = link.split("|")[0].split("#")[0].strip()

            # # Add an edge from the current note to the linked note if the linked note exists
            # if linked_note in notes:
            #     print(note_title, '-->',linked_note)
            #     G.add_edge(note_title,linked_note)

    return G


def build_undirected_graph(notes):
    """
    Constructs an undirected graph from a collection of notes.

    Parameters:
    - notes (dict): A dictionary where each key is a note title, and each value is a dictionary containing:
        - 'metadata' (dict): Metadata attributes for the note.
        - 'tags' (list): A list of tags associated with the note.
        - 'wikilinks' (list): A list of strings representing links to other notes. Each link may include:
            - A title (e.g., 'Other Note')
            - An optional section (e.g., 'Other Note#Section')
            - An optional alias (e.g., 'Other Note|Alias')

    Returns:
    - G (networkx.Graph): An undirected graph where:
        - Each node represents a note, labeled by its title, with associated metadata and tags.
        - Each edge represents a link between notes, based on the wikilinks.
    """
    # Initialize an empty undirected graph
    G = nx.Graph()

    # Iterate over each note and its associated data
    for note_title, data in notes.items():
        # Add the note as a node in the graph, including its metadata and tags as attributes
        G.add_node(note_title, **data["metadata"], tags=data["tags"])

        print(f'ON {note_title}')

        # Process each wikilink in the current note
        for link in data["wikilinks"]:
            linked_note = data["corrected_wikilinks"][link]
            if linked_note:
                print(note_title, "---", linked_note)
                G.add_edge(note_title, linked_note)

        # for link in data["wikilinks"]:
        #     # Extract the linked note's title by removing any alias ('|') and section ('#') parts
        #     linked_note = link.split("|")[0].split("#")[0].strip()

        #     # Add an edge between the current note and the linked note if the linked note exists
        #     if linked_note in notes:
        #         print(note_title, '--',linked_note)
        #         G.add_edge(note_title, linked_note)

    return G
