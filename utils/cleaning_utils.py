import re

# List of headers to skip
headers_to_skip = [
    "Acknowledgments",
    "Acknowledgements",
    "References",
    "Bibliography",
    "Citations",
    "Appendix",
    "Appendices",
    # "Supplementary Material",
    # "Supplementary Information",
    "Author Contributions",
    "Conflict of Interest",
    "Funding",
    "Disclosure",
    "Notes",
    "Footnotes",
    "Index",
    "Glossary",
    "Abbreviations",
    "Errata",
    "Dedication",
    "Copyright Notice",
    # "Preface",
    # "Foreword",
    # "Abstract",
    # "Introduction",
    # "Conclusion",
    # "Future Work",
    "Related Work",
    # "Discussion",
    # "List of Figures",
    # "List of Tables",
    "Acknowledgement of Support",
    "Acknowledgment",
    "Curriculum Vitae",
    "Biography",
    "Author Biography",
    # "Summary",
    "Postscript",
    "Afterword",
    "Table of Contents",
    "Acknowledgement",
    "Acknowledgment",
    "Endnotes",
    # "Prologue",
    # "Epilogue",
    "Works Cited",
    "Credits",
    "Legends",
    "Symbols",
    "Permissions",
    "Corrigendum",
    "Erratum",
    # "Methodology",
    # "Methods",
    # "Technical Notes",
    "Contributors",
    # "Figures",
    # "Tables",
    "Statistical Analysis",
    "Data Availability",
    "Availability of Data and Materials",
    # "Supplement",
    "Supporting Data",
    "Acknowledgement Section",
    "Back Matter",
    "Editorial Note",
    "Publication History",
    "Acknowledgement of Funding",
    "Contents"
]

# def is_header_to_skip(header: str) -> bool:
#     """
#     Check if the given header matches any header in the skip list,
#     accounting for case insensitivity and flexible whitespace.
#     """
#     # Normalize input by stripping whitespace and converting to lowercase
#     normalized_header = re.sub(r"\s+", " ", header.strip()).lower()
    
#     # Check against normalized versions of headers in the skip list
#     for skip_header in headers_to_skip:
#         normalized_skip_header = re.sub(r"\s+", " ", skip_header.strip()).lower()
#         if normalized_header == normalized_skip_header:
#             return True
    
#     return False

def is_header_to_skip(header: str) -> bool:
    """
    Check if the given header matches any header in the skip list,
    allowing for case insensitivity, whitespace normalization,
    and ignoring trailing numbers or noise.
    """
    # Normalize the input header: strip whitespace and lowercase
    normalized_header = re.sub(r"[^a-zA-Z\s]", "", header.strip()).lower()
    
    # Check against normalized skip list
    for skip_header in headers_to_skip:
        normalized_skip_header = re.sub(r"\s+", " ", skip_header.strip()).lower()
        if normalized_skip_header in normalized_header:
            return True
    
    return False