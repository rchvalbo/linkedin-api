"""
Parser utilities for LinkedIn ProfileComponents experience data.

This module provides functions to parse raw GraphQL responses from the
voyagerIdentityDashProfileComponents endpoint (sectionType:experience)
into clean, structured data.
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def parse_experience_response(response_data: dict) -> List[dict]:
    """
    Parse raw experience response into clean format.
    
    Args:
        response_data: Raw GraphQL response from get_profile_experience()
        
    Returns:
        List of experience dictionaries with clean, structured data
        
    Example:
        >>> raw_data = api.get_profile_experience(profile_urn)
        >>> experiences = parse_experience_response(raw_data)
        >>> for exp in experiences:
        ...     print(f"{exp['title']} at {exp['company']}")
    """
    experiences = []
    included = response_data.get('included', [])
    
    # Find PagedListComponent
    paged_list = _find_paged_list_component(included)
    if not paged_list:
        return experiences
    
    # Extract experience elements
    elements = paged_list.get('components', {}).get('elements', [])
    
    for element in elements:
        # Check if this is a position group (multiple roles at same company)
        if _is_position_group(element):
            # Expand the position group into individual positions
            group_positions = _extract_position_group(element, included)
            experiences.extend(group_positions)
        else:
            # Regular single position
            exp = _extract_experience_item(element, included)
            if exp:
                experiences.append(exp)
    
    return experiences


def _is_position_group(element: dict) -> bool:
    """
    Check if an element is a position group (multiple roles at same company).
    
    Position groups have a nested pagedListComponent reference in subComponents.
    """
    entity_comp = element.get('components', {}).get('entityComponent')
    if not entity_comp:
        return False
    
    # Handle case where subComponents is explicitly None
    sub_components_obj = entity_comp.get('subComponents') or {}
    sub_components = sub_components_obj.get('components', []) if isinstance(sub_components_obj, dict) else []
    
    for sub_comp in sub_components:
        paged_list_ref = sub_comp.get('components', {}).get('*pagedListComponent')
        if paged_list_ref and 'profilePositionGroup' in paged_list_ref:
            return True
    
    return False


def _extract_position_group(element: dict, included: List[dict]) -> List[dict]:
    """
    Extract all positions from a position group.
    
    A position group contains multiple roles at the same company,
    stored in a nested PagedListComponent.
    """
    positions = []
    
    # Find the nested PagedListComponent URN
    entity_comp = element.get('components', {}).get('entityComponent')
    if not entity_comp:
        return positions
    
    # Handle case where subComponents is explicitly None
    sub_components_obj = entity_comp.get('subComponents') or {}
    sub_components = sub_components_obj.get('components', []) if isinstance(sub_components_obj, dict) else []
    
    nested_paged_list_urn = None
    for sub_comp in sub_components:
        paged_list_ref = sub_comp.get('components', {}).get('*pagedListComponent')
        if paged_list_ref and 'profilePositionGroup' in paged_list_ref:
            nested_paged_list_urn = paged_list_ref
            break
    
    if not nested_paged_list_urn:
        return positions
    
    # Find the nested PagedListComponent in included array
    nested_paged_list = None
    for item in included:
        if item.get('entityUrn') == nested_paged_list_urn:
            nested_paged_list = item
            break
    
    if not nested_paged_list:
        return positions
    
    # Extract positions from nested list
    nested_elements = nested_paged_list.get('components', {}).get('elements', [])
    for nested_element in nested_elements:
        pos = _extract_experience_item(nested_element, included)
        if pos:
            positions.append(pos)
    
    return positions


def _find_paged_list_component(included: List[dict]) -> Optional[dict]:
    """
    Find the main PagedListComponent for experience in included array.
    
    There may be multiple PagedListComponents (for nested position groups),
    so we find the one with the most elements or the highest total count.
    """
    paged_lists = []
    
    for item in included:
        if item.get('$type') == 'com.linkedin.voyager.dash.identity.profile.tetris.PagedListComponent':
            # Get the total count from paging metadata
            total = item.get('components', {}).get('paging', {}).get('total', 0)
            elements_count = len(item.get('components', {}).get('elements', []))
            paged_lists.append({
                'component': item,
                'total': total,
                'elements_count': elements_count
            })
    
    if not paged_lists:
        return None
    
    # Return the one with the most elements (actual data in response)
    # or highest total count if elements are equal
    return max(paged_lists, key=lambda x: (x['elements_count'], x['total']))['component']


def _extract_experience_item(element: dict, included: List[dict]) -> Optional[dict]:
    """
    Extract single experience item from element.
    
    Args:
        element: Component element containing experience data
        included: Included array for resolving company data
        
    Returns:
        Dictionary with structured experience data
    """
    entity_comp = element.get('components', {}).get('entityComponent')
    if not entity_comp:
        return None
    
    # Extract basic info
    title = _get_nested_text(entity_comp, 'titleV2', 'text', 'text')
    date_range = _get_nested_text(entity_comp, 'caption', 'text')
    company_url = entity_comp.get('textActionTarget', '')
    
    # Extract subtitle (may contain company name)
    subtitle = _get_nested_text(entity_comp, 'subtitle', 'text')
    
    # Extract company ID from URL
    company_id = _extract_company_id(company_url)
    
    # Extract description and skills from subComponents
    description, skills = _extract_subcomponents(entity_comp)
    
    # Extract location from subComponents
    location = _extract_location(entity_comp)
    
    # Parse dates
    start_date, end_date, is_current = parse_date_range(date_range)
    
    # Find company data in included array
    company_name, company_logo = _find_company_data(company_id, included)
    
    # Use subtitle as company name if not found
    if not company_name and subtitle:
        company_name = subtitle
    
    # Clean company name (remove employment type like "· Full-time")
    if company_name:
        company_name = _clean_company_name(company_name)
    
    return {
        'title': title,
        'company': company_name,
        'company_id': company_id,
        'company_url': company_url,
        'company_logo': company_logo,
        'start_date': start_date,
        'end_date': end_date,
        'is_current': is_current,
        'location': location,
        'description': description,
        'skills': skills
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


def _clean_company_name(company_name: str) -> str:
    """
    Clean company name by removing employment type suffix.
    
    Examples:
        "Menlo Security Inc. · Full-time" -> "Menlo Security Inc."
        "Skyhigh Security · Full-time" -> "Skyhigh Security"
        "EVOTEK · Part-time" -> "EVOTEK"
        "Forcepoint" -> "Forcepoint"
    
    Args:
        company_name: Raw company name from LinkedIn
        
    Returns:
        Cleaned company name
    """
    if not company_name:
        return company_name
    
    # Split by · and take the first part (company name)
    # This removes suffixes like "· Full-time", "· Part-time", "· Contract", etc.
    if '·' in company_name:
        company_name = company_name.split('·')[0].strip()
    
    return company_name


def _extract_company_id(company_url: str) -> Optional[str]:
    """
    Extract company ID from LinkedIn company URL.
    
    Args:
        company_url: URL like "https://www.linkedin.com/company/143650/"
        
    Returns:
        Company ID (e.g., "143650") or None
    """
    if not company_url:
        return None
    
    # Pattern: /company/{id}/
    match = re.search(r'/company/(\d+)/?', company_url)
    if match:
        return match.group(1)
    
    return None


def _extract_subcomponents(entity_comp: dict) -> Tuple[Optional[str], List[str]]:
    """
    Extract description and skills from subComponents.
    
    Args:
        entity_comp: Entity component containing subComponents
        
    Returns:
        Tuple of (description, skills_list)
    """
    description = None
    skills = []
    
    # Handle case where subComponents is explicitly None
    sub_components_obj = entity_comp.get('subComponents') or {}
    sub_components = sub_components_obj.get('components', []) if isinstance(sub_components_obj, dict) else []
    
    for idx, sub_comp in enumerate(sub_components):
        # Find all text components (may be nested in fixedListComponent)
        text_components = _find_all_text_components(sub_comp)
        
        for text_comp in text_components:
            text = text_comp.get('text', {}).get('text', '')
            
            if not text:
                continue
            
            # Check if this is skills
            if text.startswith('Skills:'):
                skills_text = text.replace('Skills:', '').strip()
                skills = [s.strip() for s in skills_text.split('·') if s.strip()]
            # Take the first substantial text as description (not skills, not dates, not location)
            elif not description and len(text) > 50:
                # Description is usually longer than 50 chars
                # Skip if it looks like a date or location
                if not any(month in text for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                    description = text
    
    return description, skills


def _extract_location(entity_comp: dict) -> Optional[str]:
    """
    Extract location from subComponents.
    
    Location is typically in a sibling component within the FixedListComponent,
    stored in entityComponent.metadata.text.
    
    Args:
        entity_comp: Entity component containing subComponents
        
    Returns:
        Location string or None
    """
    # Handle case where subComponents is explicitly None
    sub_components_obj = entity_comp.get('subComponents') or {}
    sub_components = sub_components_obj.get('components', []) if isinstance(sub_components_obj, dict) else []
    
    # Look for location in the components
    # Location is usually in the first or second component with entityComponent.metadata
    for sub_comp in sub_components:
        entity = sub_comp.get('components', {}).get('entityComponent', {})
        if entity:
            # Check if this has metadata with location text
            metadata = entity.get('metadata', {})
            if metadata and isinstance(metadata, dict):
                location_text = metadata.get('text', '')
                # Location text typically doesn't start with common date patterns
                # and isn't empty
                if location_text and not any(month in location_text for month in 
                    ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                    return location_text
    
    return None


def _find_all_text_components(component: dict) -> List[dict]:
    """
    Recursively find all textComponents in nested structure.
    
    Args:
        component: Component to search
        
    Returns:
        List of text component dictionaries
    """
    text_components = []
    
    if not isinstance(component, dict):
        return text_components
    
    # Check if this level has textComponent
    components = component.get('components', {})
    if 'textComponent' in components and components['textComponent']:
        text_components.append(components['textComponent'])
    
    # Check for fixedListComponent with nested components
    if 'fixedListComponent' in components:
        fixed_list = components['fixedListComponent']
        # Check if fixedListComponent is not None
        if fixed_list and isinstance(fixed_list, dict):
            nested_components = fixed_list.get('components', [])
            for nested in nested_components:
                text_components.extend(_find_all_text_components(nested))
    
    # Recursively search all dict values
    for key, value in component.items():
        if key == 'components':
            continue  # Already handled above
        if isinstance(value, dict):
            text_components.extend(_find_all_text_components(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    text_components.extend(_find_all_text_components(item))
    
    return text_components


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


def _find_company_data(company_id: Optional[str], included: List[dict]) -> Tuple[Optional[str], Optional[str]]:
    """
    Find company name and logo in included array.
    
    Args:
        company_id: Company ID to search for
        included: Included array from response
        
    Returns:
        Tuple of (company_name, company_logo_url)
    """
    if not company_id:
        return None, None
    
    company_urn = f"urn:li:fsd_company:{company_id}"
    
    for item in included:
        if item.get('entityUrn') == company_urn:
            # Extract company name (if available)
            company_name = item.get('name')  # May not be present
            
            # Extract logo
            logo_result = item.get('logoResolutionResult', {})
            vector_image = logo_result.get('vectorImage', {})
            root_url = vector_image.get('rootUrl', '')
            artifacts = vector_image.get('artifacts', [])
            
            # Get 200x200 logo (preferred size)
            company_logo = None
            for artifact in artifacts:
                if artifact.get('width') == 200:
                    company_logo = root_url + artifact.get('fileIdentifyingUrlPathSegment', '')
                    break
            
            # Fallback to first available size
            if not company_logo and artifacts:
                company_logo = root_url + artifacts[0].get('fileIdentifyingUrlPathSegment', '')
            
            return company_name, company_logo
    
    return None, None


def parse_date_range(date_text: str) -> Tuple[Optional[str], Optional[str], bool]:
    """
    Parse date range text into structured dates.
    
    Handles formats like:
    - "2017 - 2018 · 1 yr"
    - "Jun 2025 - Present"
    - "2021 - 2023 · 2 yrs 3 mos"
    - "Jan 2020 - Dec 2022"
    
    Args:
        date_text: Date range string from LinkedIn
        
    Returns:
        Tuple of (start_date, end_date, is_current)
        Dates are in ISO format (YYYY-MM-DD) or None
    """
    if not date_text:
        return None, None, False
    
    # Check if current position
    is_current = 'Present' in date_text or 'present' in date_text
    
    # Split by '·' to remove duration
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
        # Single date (just start)
        start_date = _parse_single_date(date_part.strip())
        return start_date, None, False
    
    start_date = None
    end_date = None
    
    if len(parts) >= 1:
        start_date = _parse_single_date(parts[0].strip())
    
    if len(parts) >= 2 and not is_current:
        end_date = _parse_single_date(parts[1].strip())
    
    return start_date, end_date, is_current


def _parse_single_date(date_str: str) -> Optional[str]:
    """
    Parse single date string into ISO format.
    
    Handles formats:
    - "2017" → "2017-01-01"
    - "Jun 2025" → "2025-06-01"
    - "January 2020" → "2020-01-01"
    
    Args:
        date_str: Date string
        
    Returns:
        ISO format date (YYYY-MM-DD) or None
    """
    if not date_str or date_str.lower() in ['present', 'current']:
        return None
    
    date_str = date_str.strip()
    
    # Try "Jun 2025" or "January 2020" format
    month_year_pattern = r'([A-Za-z]+)\s+(\d{4})'
    match = re.match(month_year_pattern, date_str)
    if match:
        month_str, year = match.groups()
        try:
            # Try short month name (Jun)
            month = datetime.strptime(month_str, '%b').month
        except ValueError:
            try:
                # Try full month name (January)
                month = datetime.strptime(month_str, '%B').month
            except ValueError:
                # Can't parse month, use January
                month = 1
        
        return f"{year}-{month:02d}-01"
    
    # Try "2017" format (year only)
    year_pattern = r'^(\d{4})$'
    match = re.match(year_pattern, date_str)
    if match:
        year = match.group(1)
        return f"{year}-01-01"
    
    return None


def format_experience_for_output(experiences: List[dict]) -> dict:
    """
    Format parsed experiences for API output.
    
    Args:
        experiences: List of parsed experience dictionaries
        
    Returns:
        Dictionary with work_experience key
    """
    return {
        "work_experience": experiences
    }
