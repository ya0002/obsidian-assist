import os

import uuid
import hashlib
import time

import json
import ast
import re

from collections import defaultdict

from pathlib import Path


def generate_unique_id() -> str:
    timestamp = int(time.time() * 1000)
    unique_id = f"{timestamp}_{uuid.uuid4().hex[:20]}"
    return unique_id


def preprocess_json_string(json_string):
    # Escape backslashes that are not part of a valid escape sequence
    json_string = re.sub(r"\\(?![\"\\/bfnrtu])", r"\\\\", json_string)
    # Escape newlines
    # json_string = json_string.replace("\n", "\\n")
    # Ensure property names are wrapped in double quotes (only for JSON parsing)
    # json_string = re.sub(r"(?<!\\)(')", r"\"", json_string)
    return json_string

def extract_and_parse_json(input_string):
    try:
        # Detect JSON blocks
        if "```json" in input_string:
            start = input_string.find("```json")
            offset = 7  # Length of "```json"
        elif "```" in input_string:
            start = input_string.find("```")
            offset = 3  # Length of "```"
        else:
            raise ValueError("No valid JSON block enclosed in triple backticks found.")
        
        end = input_string.rfind("```")
        if start == -1 or end == -1 or start == end:
            raise ValueError("No valid JSON block enclosed in triple backticks found.")
        
        # Extract and preprocess JSON
        json_string = input_string[start + offset:end].strip()
        json_string = preprocess_json_string(json_string)
        
        # Attempt to parse with json.loads
        try:
            return json.loads(json_string,strict=False)
        except json.JSONDecodeError as e:
            print(f"JSON decoding failed: {e}")
        
        # Attempt to parse with ast.literal_eval
        try:
            return ast.literal_eval(json_string)
        except (SyntaxError, ValueError) as e:
            print(f"AST parsing failed: {e}")
        
        # If both fail, return the preprocessed string and log the issue
        print("Could not parse the string using either method.")
        return json_string
    
    except Exception as e:
        print(f"Error: {e}")
        return input_string


def merge_dicts(list_of_dicts):
    """
    Merges a list of dictionaries into a single dictionary.
    If keys are repeated, their values are aggregated into a list.

    Args:
        list_of_dicts (list): List of dictionaries to merge.

    Returns:
        dict: Merged dictionary with aggregated values for duplicate keys.
    """
    merged_dict = defaultdict(list)

    for d in list_of_dicts:
        for key, value in d.items():
            merged_dict[key].append(value)

     # Process the merged dictionary
    for key, value in merged_dict.items():
        
        if len(value) == 1:
            merged_dict[key] = value[0]  # Single unique value, not a list
            continue

        # If value is a list, remove duplicates and convert to single value if there's only one        
        merged_dict[key] = list(set(value))  # Keep unique list


    return dict(merged_dict)

def replace_references(text: str, reference_dict: dict) -> str:
    """
    Replace references in the format <reference image xyz> with their corresponding values from a dictionary.
    The entire tag is used as the dictionary key.
    
    Args:
        text (str): Input text containing references
        reference_dict (dict): Dictionary mapping full reference tags to their values
        
    Returns:
        str: Text with all references replaced with their corresponding values
        
    Example:
        text = "Here is <reference image cat> and <reference image dog>"
        refs = {
            "<reference image cat>": "a cute cat",
            "<reference image dog>": "a happy dog"
        }
        result = replace_references(text, refs)
        # Returns: "Here is a cute cat and a happy dog"
    """
    
    if text is None:
        print('text was None during image generation.')
        return ''
    
    def replace_match(match):
        print(match)
        # Use the entire match as the dictionary key
        return reference_dict.get(match.group(0), match.group(0))
    

    # Pattern matches <reference image anything>
    pattern = r"<reference image[^>]*>"
    
    # Replace all matches using the replace function
    result = re.sub(pattern, replace_match, text)
    return result


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by:
    1. Removing or replacing special characters
    2. Replacing spaces with underscores
    3. Removing leading/trailing periods and spaces
    
    Args:
        filename (str): The filename to sanitize
        
    Returns:
        str: A sanitized filename safe for all operating systems
    """
    # Remove or replace special characters
    # Keep alphanumeric, dashes, underscores, and periods
    sanitized = re.sub(r'[^\w\-\.\s]', '_', filename)
    
    # Replace spaces with underscores
    # sanitized = sanitized.replace(' ', '_')
    
    # Remove leading/trailing periods and spaces
    sanitized = sanitized.strip('. ')
    
    # Collapse multiple underscores
    # sanitized = re.sub(r'_+', '_', sanitized)
    
    # Ensure the filename isn't empty after sanitization
    if not sanitized:
        sanitized = "untitled"
        
    return sanitized

def write_to_markdown(content: str, filename: str, save_dir: str, mode: str = 'w', encoding: str = 'utf-8') -> str:
    """
    Write content to a markdown file with sanitized filename.
    
    Args:
        content (str): The content to write to the file
        filename (str): The name of the file to write to (including .md extension)
        mode (str): The file mode ('w' for write, 'a' for append). Defaults to 'w'
        encoding (str): The encoding to use. Defaults to 'utf-8'
    
    Returns:
        str: The actual filename used after sanitization
        
    Example:
        actual_filename = write_to_markdown("# Hello\nThis is a test", "My File!.md")
        # Returns: "My_File.md"
    """
    # Split filename and extension
    path = Path(filename)
    stem = path.stem
    suffix = path.suffix
    
    # If no extension provided, add .md
    if not suffix:
        suffix = '.md'
    elif suffix != '.md':
        suffix = '.md'
    
    # Sanitize the filename stem
    sanitized_stem = sanitize_filename(stem)
    
    # Combine sanitized stem with extension
    sanitized_filename = os.path.join(save_dir, f"{sanitized_stem}{suffix}")
    # Check if the file exists
    if os.path.exists(sanitized_filename):
        print(f"File '{sanitized_stem}' exists. Renaming it...")
        # Sanitize the filename stem
        sanitized_stem = f"{sanitized_stem}_{len(os.listdir(save_dir))}"
        print(f'New name: {sanitized_stem}')
        # Combine sanitized stem with extension
        sanitized_filename = os.path.join(save_dir, f"{sanitized_stem}{suffix}")
    
    # Create directory if it doesn't exist (for nested paths)
    directory = os.path.dirname(sanitized_filename)
    if directory:
        os.makedirs(directory, exist_ok=True)
    
    # Write the file
    try:
        with open(sanitized_filename, mode, encoding=encoding) as f:
            f.write(content)
    except Exception as e:
        raise IOError(f"Failed to write file: {e}")
        
    return sanitized_stem,sanitized_filename


def generate_unique_hash(input_string: str) -> str:
    """
    Generates a unique hash for the given string using SHA256.

    Args:
        input_string (str): The input string to hash.

    Returns:
        str: The resulting hash in hexadecimal format.
    """
    # Create a SHA256 hash object
    hash_object = hashlib.sha256()
    
    # Encode the string and update the hash object
    hash_object.update(input_string.encode('utf-8'))
    
    # Return the hexadecimal representation of the hash
    return hash_object.hexdigest()

def process_path(path):
    if os.path.isdir(path):
        # If it's a directory, list all .pdf, .pptx and .md files
        file_list = []
        for root, _, files in os.walk(path):
            for file in files:
                if file.endswith((".pdf", ".md", ".pptx")):
                    file_list.append(os.path.join(root, file))
        print("Files found in directory:")
        for f in file_list:
            print(f)
        return file_list
    elif os.path.isfile(path):
        # If it's a file, check its extension
        if path.endswith((".pdf", ".md", ".pptx")):
            print(f"The file '{path}' is acceptable.")
            return [path]
        else:
            print(f"The file '{path}' is not an acceptable type.")
            return []
    else:
        print(f"The path '{path}' is neither a file nor a directory.")
        return []
