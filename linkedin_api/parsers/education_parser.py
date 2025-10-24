"""
Parser utilities for LinkedIn ProfileComponents education data.

This module provides functions to parse raw GraphQL responses from the
voyagerIdentityDashProfileComponents endpoint (sectionType:education)
into clean, structured data.
"""

import re
from typing import Dict, List, Optional, Tuple


def parse_education_response(response_data: dict) -> List[dict]:
    """
    Parse raw education response into clean format.
    
    Args:
        response_data: Raw GraphQL response from get_profile_education()
        
    Returns:
        List of education dictionaries with clean, structured data
        
    Example:
        >>> raw_data = api.get_profile_education(profile_urn)
        >>> education = parse_education_response(raw_data)
        >>> for edu in education:
        ...     print(f"{edu['degree']} from {edu['school']}")
    """
    education_list = []
    included = response_data.get('included', [])
    
    # Find PagedListComponent
    paged_list = _find_paged_list_component(included)
    if not paged_list:
        return education_list
    
    # Extract education elements
    elements = paged_list.get('components', {}).get('elements', [])
    
    for element in elements:
        edu = _extract_education_item(element, included)
        if edu:
            education_list.append(edu)
    
    return education_list


def _find_paged_list_component(included: List[dict]) -> Optional[dict]:
    """Find PagedListComponent in included array."""
    for item in included:
        if item.get('$type') == 'com.linkedin.voyager.dash.identity.profile.tetris.PagedListComponent':
            return item
    return None


def _extract_education_item(element: dict, included: List[dict]) -> Optional[dict]:
    """
    Extract single education item from element.
    
    Args:
        element: Component element containing education data
        included: Included array for resolving school data
        
    Returns:
        Dictionary with structured education data
    """
    entity_comp = element.get('components', {}).get('entityComponent')
    if not entity_comp:
        return None
    
    # Extract basic info
    degree = _get_nested_text(entity_comp, 'titleV2', 'text', 'text')
    date_range = _get_nested_text(entity_comp, 'caption', 'text')
    school_url = entity_comp.get('textActionTarget', '')
    
    # Extract subtitle (school name)
    school_name = _get_nested_text(entity_comp, 'subtitle', 'text')
    
    # Extract school ID from URL
    school_id = _extract_school_id(school_url)
    
    # Extract field of study and description from subComponents
    field_of_study, description = _extract_subcomponents(entity_comp)
    
    # Parse dates (extract years)
    start_year, end_year = parse_education_date_range(date_range)
    
    # Find school logo in included array
    school_logo = _find_school_logo(school_id, included)
    
    return {
        'school': school_name,
        'school_id': school_id,
        'school_url': school_url,
        'school_logo': school_logo,
        'degree': degree,
        'field_of_study': field_of_study,
        'start_year': start_year,
        'end_year': end_year,
        'description': description
    }


def _get_nested_text(obj: dict, *keys: str) -> str:
    """Safely get nested text value from object."""
    current = obj
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, {})
        else:
            return ''
    return current if isinstance(current, str) else ''


def _extract_school_id(school_url: str) -> Optional[str]:
    """
    Extract school ID from LinkedIn school URL.
    
    Args:
        school_url: URL like "https://www.linkedin.com/school/18190/"
        
    Returns:
        School ID (e.g., "18190") or None
    """
    if not school_url:
        return None
    
    # Pattern: /school/{id}/
    match = re.search(r'/school/(\d+)/?', school_url)
    if match:
        return match.group(1)
    
    return None


def _extract_subcomponents(entity_comp: dict) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract field of study and description from subComponents.
    
    Args:
        entity_comp: Entity component containing subComponents
        
    Returns:
        Tuple of (field_of_study, description)
    """
    field_of_study = None
    description = None
    
    sub_components = entity_comp.get('subComponents', {}).get('components', [])
    
    for idx, sub_comp in enumerate(sub_components):
        text_comp = _find_text_component(sub_comp)
        if text_comp:
            text = text_comp.get('text', {}).get('text', '')
            
            if idx == 0:
                # First subcomponent is usually field of study
                field_of_study = text
            elif idx == 1:
                # Second subcomponent is usually description/activities
                description = text
    
    return field_of_study, description


def _find_text_component(component: dict) -> Optional[dict]:
    """
    Recursively find textComponent in nested structure.
    
    Args:
        component: Component to search
        
    Returns:
        Text component dictionary or None
    """
    if not isinstance(component, dict):
        return None
    
    # Check if this level has textComponent
    components = component.get('components', {})
    if 'textComponent' in components:
        return components['textComponent']
    
    # Check for fixedListComponent with nested components
    if 'fixedListComponent' in components:
        fixed_list = components['fixedListComponent']
        nested_components = fixed_list.get('components', [])
        for nested in nested_components:
            result = _find_text_component(nested)
            if result:
                return result
    
    # Recursively search all dict values
    for value in component.values():
        if isinstance(value, dict):
            result = _find_text_component(value)
            if result:
                return result
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    result = _find_text_component(item)
                    if result:
                        return result
    
    return None


def _find_school_logo(school_id: Optional[str], included: List[dict]) -> Optional[str]:
    """
    Find school logo in included array.
    
    Args:
        school_id: School ID to search for
        included: Included array from response
        
    Returns:
        School logo URL or None
    """
    if not school_id:
        return None
    
    school_urn = f"urn:li:fsd_school:{school_id}"
    
    for item in included:
        if item.get('entityUrn') == school_urn:
            # Extract logo
            logo_result = item.get('logoResolutionResult', {})
            vector_image = logo_result.get('vectorImage', {})
            root_url = vector_image.get('rootUrl', '')
            artifacts = vector_image.get('artifacts', [])
            
            # Get 200x200 logo (preferred size)
            school_logo = None
            for artifact in artifacts:
                if artifact.get('width') == 200:
                    school_logo = root_url + artifact.get('fileIdentifyingUrlPathSegment', '')
                    break
            
            # Fallback to first available size
            if not school_logo and artifacts:
                school_logo = root_url + artifacts[0].get('fileIdentifyingUrlPathSegment', '')
            
            return school_logo
    
    return None


def parse_education_date_range(date_text: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Parse education date range text into years.
    
    Handles formats like:
    - "2016 - 2020"
    - "2018 - 2022 · 4 yrs"
    - "2020 - Present"
    - "2019"
    
    Args:
        date_text: Date range string from LinkedIn
        
    Returns:
        Tuple of (start_year, end_year) as integers or None
    """
    if not date_text:
        return None, None
    
    # Remove duration part (after ·)
    if '·' in date_text:
        date_part = date_text.split('·')[0].strip()
    else:
        date_part = date_text.strip()
    
    # Split by '-' or '–' to get start and end
    if '-' in date_part:
        parts = date_part.split('-')
    elif '–' in date_part:
        parts = date_part.split('–')
    else:
        # Single year
        year = _extract_year(date_part.strip())
        return year, year
    
    start_year = None
    end_year = None
    
    if len(parts) >= 1:
        start_year = _extract_year(parts[0].strip())
    
    if len(parts) >= 2:
        end_text = parts[1].strip()
        if end_text.lower() not in ['present', 'current']:
            end_year = _extract_year(end_text)
    
    return start_year, end_year


def _extract_year(date_str: str) -> Optional[int]:
    """
    Extract year from date string.
    
    Args:
        date_str: Date string (e.g., "2020", "Jun 2020")
        
    Returns:
        Year as integer or None
    """
    if not date_str:
        return None
    
    # Find 4-digit year
    match = re.search(r'(\d{4})', date_str)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    
    return None


def format_education_for_output(education_list: List[dict]) -> dict:
    """
    Format parsed education for API output.
    
    Args:
        education_list: List of parsed education dictionaries
        
    Returns:
        Dictionary with education key
    """
    return {
        "education": education_list
    }
