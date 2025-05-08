import os
import re
import yaml
from store_in_vectore_db import dissect_markdown_with_images


def extract_matching_substring(path, X):
    matches = [s for s in X if s in path]
    if not matches:
        return None
    return max(matches, key=len)


def parse_markdown_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract YAML frontmatter
    yaml_match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    metadata = {}
    if yaml_match:
        yaml_content = yaml_match.group(1)
        metadata = yaml.safe_load(yaml_content)
        content = content[yaml_match.end() :]  # Remove YAML from content

    # Extract wikilinks
    wikilinks = re.findall(r"\[\[([^\]]+)\]\]", content)

    # Extract tags
    tags = re.findall(r"#(\w+)", content)

    content, reference_images = dissect_markdown_with_images(content)

    return {
        "metadata": metadata,
        "wikilinks": wikilinks,
        "tags": tags,
        "content": content,
        "reference_images":reference_images
    }


def parse_vault(vault_path):
    notes = {}
    all_note_keys = []
    title_to_path = {}

    # First pass: index note paths
    for root, _, files in os.walk(vault_path):
        for file in files:
            if file.endswith(".md"):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, vault_path)
                title = os.path.splitext(os.path.basename(file))[0]
                title_to_path[title] = os.path.normpath(full_path)
                note_key = os.path.splitext(os.path.relpath(full_path, vault_path))[0]
                all_note_keys.append(note_key)

    # Second pass: parse and resolve wikilinks
    for root, _, files in os.walk(vault_path):
        for file in files:
            if file.endswith(".md"):
                full_path = os.path.join(root, file)
                note_key = os.path.splitext(os.path.relpath(full_path, vault_path))[0]
                parsed = parse_markdown_file(full_path)

                resolved_links = dict() ##full path
                matching_link = dict()  ## path that is the key in notes
                for link in parsed["wikilinks"]:
                    link_title = link.split("|")[
                        0
                    ]  # Handle display text like [[Note Title|Display]]
                    resolved_path = title_to_path.get(link_title)
                    resolved_links[link]= resolved_path
                    matching_link[link] = extract_matching_substring(resolved_path,all_note_keys)

                parsed["wikilinks_fulllpath"] = resolved_links
                parsed["corrected_wikilinks"]=matching_link
                notes[note_key] = parsed


    return notes
