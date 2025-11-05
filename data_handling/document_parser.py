"""
Document Parser Module

Generic utilities for parsing and extracting sections from documents.
"""

import re
from typing import List


def extract_section(
        text: str,
        section_headers: List[str],
        next_section_headers: List[str]
) -> str:
    """
    Extract a specific section from a document using regex patterns.

    Args:
        text: Full document text
        section_headers: Possible headers marking the start of the section
        next_section_headers: Headers that mark the end of this section

    Returns:
        Extracted section text (empty string if not found)
    """
    # Try each possible section header
    start_pos = -1
    for header in section_headers:
        pattern = re.escape(header) + r'\s*'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start_pos = match.end()
            break

    if start_pos == -1:
        return ""

    # Find the section end
    end_pos = len(text)

    if next_section_headers:
        for next_header in next_section_headers:
            next_pattern = re.escape(next_header) + r'\s*'
            next_match = re.search(next_pattern, text[start_pos:], re.IGNORECASE)
            if next_match:
                potential_end = start_pos + next_match.start()
                end_pos = min(end_pos, potential_end)

    section_text = text[start_pos:end_pos].strip()
    return section_text