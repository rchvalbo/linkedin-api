"""
Parser utilities for LinkedIn API responses.

This package provides functions to parse raw GraphQL responses into
clean, structured data formats.
"""

from .experience_parser import (
    parse_experience_response,
    parse_date_range,
    format_experience_for_output
)

from .education_parser import (
    parse_education_response,
    parse_education_date_range,
    format_education_for_output
)

__all__ = [
    'parse_experience_response',
    'parse_date_range',
    'format_experience_for_output',
    'parse_education_response',
    'parse_education_date_range',
    'format_education_for_output',
]
