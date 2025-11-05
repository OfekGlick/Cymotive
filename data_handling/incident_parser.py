"""
Incident Report Parser Module

Specialized parsing for cybersecurity incident reports including
metadata extraction and section parsing.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

from data_handling.document_parser import extract_section


class IncidentReportParser:
    """Parses incident reports and extracts structured metadata and sections."""

    # Section configuration for incident reports
    SECTION_CONFIGS = {
        'description': {
            'headers': ['Detailed Incident Description:', 'Incident Description:'],
            'next_headers': ['Impact Assessment:', 'Response and Forensic Analysis:',
                             'Response:', 'Lessons Learned:', 'Recommendations:']
        },
        'impact': {
            'headers': ['Impact Assessment:', 'Impact:'],
            'next_headers': ['Response and Forensic Analysis:', 'Response:',
                             'Lessons Learned:', 'Recommendations:']
        },
        'response': {
            'headers': ['Response and Forensic Analysis:', 'Response:', 'Forensic Analysis:'],
            'next_headers': ['Lessons Learned:', 'Recommendations:']
        },
        'recommendations': {
            'headers': ['Lessons Learned:', 'Recommendations:'],
            'next_headers': []
        }
    }

    def __init__(self, config):
        """
        Initialize the incident report parser.

        Args:
            config: RAG configuration object (for token counting)
        """
        self.config = config

    @staticmethod
    def _clean_value(value: str) -> str:
        """Clean metadata values by removing trailing punctuation."""
        return value.strip().rstrip('.,;:')

    def extract_metadata(self, text: str, file_name: str) -> Dict[str, Any]:
        """
        Extract structured metadata from incident report text.

        Args:
            text: Full incident report text
            file_name: Name of the file being parsed

        Returns:
            Dictionary containing extracted metadata fields
        """
        metadata = {
            'source': 'incident_report',
            'file_name': file_name
        }

        # Extract Incident ID
        incident_id_match = re.search(r'Incident ID:\s*([A-Z0-9-]+)', text, re.IGNORECASE)
        if incident_id_match:
            metadata['incident_id'] = incident_id_match.group(1).strip()

        # Extract Date of Detection
        date_match = re.search(
            r'Date of Detection:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}(?:\s+[0-9]{2}:[0-9]{2})?(?:\s+UTC)?)',
            text, re.IGNORECASE
        )
        if date_match:
            metadata['date_of_detection'] = date_match.group(1).strip()
            year_match = re.search(r'([0-9]{4})', date_match.group(1))
            month_match = re.search(r'[0-9]{4}-([0-9]{2})', date_match.group(1))
            if year_match:
                metadata['year'] = year_match.group(1)
            if month_match:
                metadata['month'] = month_match.group(1)

        # Extract Vehicle ID
        vehicle_id_match = re.search(r'Vehicle ID:\s*([A-Z0-9/-]+)(?:\s*\(([^)]+)\))?', text, re.IGNORECASE)
        if vehicle_id_match:
            metadata['vehicle_id'] = vehicle_id_match.group(1).strip()
            if vehicle_id_match.group(2):
                metadata['vehicle_id_note'] = vehicle_id_match.group(2).strip()

        # Extract Fleet
        fleet_match = re.search(r'Fleet:\s*["\']([^"\']+)["\']', text, re.IGNORECASE)
        if fleet_match:
            metadata['fleet'] = fleet_match.group(1).strip()

        # Extract Threat Category
        threat_match = re.search(
            r'Threat Category:\s*([^.\n]+?)(?=\s+Detection Method:|\s+Severity:|\n|$)',
            text, re.IGNORECASE
        )
        if threat_match:
            metadata['threat_category'] = self._clean_value(threat_match.group(1))

        # Extract Detection Method
        detection_match = re.search(
            r'Detection Method:\s*([^.\n]+?)(?=\s+Severity:|\s+Status:|\n|\.)',
            text, re.IGNORECASE
        )
        if detection_match:
            metadata['detection_method'] = self._clean_value(detection_match.group(1))

        # Extract Severity
        severity_match = re.search(r'Severity:\s*([^.\n]+)', text, re.IGNORECASE)
        if severity_match:
            metadata['severity'] = self._clean_value(severity_match.group(1))

        # Extract Status
        status_match = re.search(r'Status:\s*([^.\n]+)', text, re.IGNORECASE)
        if status_match:
            metadata['status'] = self._clean_value(status_match.group(1))

        return metadata

    def parse_incident_report(
            self,
            file_path: str
    ) -> List[Tuple[str, Dict[str, Any], str]]:
        """
        Parse incident report and extract individual sections with cross-section metadata.

        Args:
            file_path: Path to the incident report text file

        Returns:
            List of tuples (text, metadata, document_id) for each section
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()

        # Extract base metadata
        file_name = os.path.basename(file_path)
        base_metadata = self.extract_metadata(full_text, file_name)

        # Prepare results list
        results = []
        incident_id = base_metadata.get('incident_id', os.path.splitext(file_name)[0])

        # First pass: Extract all section texts
        extracted_sections = {}
        for section_key, config in self.SECTION_CONFIGS.items():
            section_text = extract_section(
                full_text,
                config['headers'],
                config['next_headers']
            )
            if section_text:
                extracted_sections[section_key] = section_text

        # Second pass: Build results with cross-section metadata
        for section_key, section_text in extracted_sections.items():
            section_metadata = base_metadata.copy()
            section_metadata['section_type'] = section_key
            section_metadata['token_count'] = self.config.count_tokens(section_text)

            # Add ALL sections' text to metadata (including the current section)
            for other_section_key, other_section_text in extracted_sections.items():
                section_metadata[f'section_{other_section_key}_text'] = other_section_text

            doc_id = f"{incident_id}_{section_key}"
            results.append((section_text, section_metadata, doc_id))

        return results

    def load_incident_reports(
            self,
            directory_path: str,
            file_pattern: str = "*.txt"
    ) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
        """
        Load incident reports from a directory and extract all sections.

        Args:
            directory_path: Path to directory containing incident reports
            file_pattern: Glob pattern for files to load (default: "*.txt")

        Returns:
            Tuple of (documents, metadatas, ids) for all sections across all reports
        """
        dir_path = Path(directory_path)
        files = sorted(dir_path.glob(file_pattern))

        all_documents = []
        all_metadatas = []
        all_ids = []

        for i, file_path in enumerate(files, 1):
            print(f"[{i}/{len(files)}] Processing: {file_path.name}")

            # Parse report and extract all sections
            sections = self.parse_incident_report(str(file_path))

            # Add all sections
            for text, metadata, doc_id in sections:
                all_documents.append(text)
                all_metadatas.append(metadata)
                all_ids.append(doc_id)

                section_type = metadata.get('section_type', 'unknown')
                tokens = metadata.get('token_count', 0)
                print(f"  ✓ {section_type}: {tokens} tokens (ID: {doc_id})")

            print(f"  → Generated {len(sections)} documents from this report\n")

        return all_documents, all_metadatas, all_ids