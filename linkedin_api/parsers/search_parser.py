"""
LinkedIn Search Response Parser

Extracts and enriches data from LinkedIn search API responses.
Provides helper functions to parse various fields from search results.
"""

import re
from typing import Dict, Optional, Any


def extract_mutual_connections(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract mutual connections count and URL from insights.
    
    Args:
        item: Search result item from LinkedIn API
        
    Returns:
        Dict with mutual_connections_count and mutual_connections_url
        
    Example:
        >>> extract_mutual_connections(item)
        {'mutual_connections_count': 55, 'mutual_connections_url': 'https://...'}
    """
    insights = item.get("insightsResolutionResults", [])
    if insights:
        simple_insight = insights[0].get("simpleInsight", {})
        if simple_insight:
            title = simple_insight.get("title")
            title_text = title.get("text", "") if title else ""
            # Parse "55 mutual connections" -> 55
            match = re.search(r'(\d+)\s+mutual\s+connection', title_text, re.IGNORECASE)
            count = int(match.group(1)) if match else 0
            
            return {
                "mutual_connections_count": count,
                "mutual_connections_url": simple_insight.get("navigationUrl", None)
            }
    return {"mutual_connections_count": 0, "mutual_connections_url": None}


def extract_connection_degree(item: Dict[str, Any]) -> Optional[str]:
    """
    Extract connection degree from badge text.
    
    Args:
        item: Search result item from LinkedIn API
        
    Returns:
        Connection degree ("1st", "2nd", "3rd") or None
        
    Example:
        >>> extract_connection_degree(item)
        '2nd'
    """
    badge_text_obj = item.get("badgeText")
    badge_text = badge_text_obj.get("text", "") if badge_text_obj else ""
    # Extract "• 2nd" -> "2nd"
    match = re.search(r'(\d+)(st|nd|rd|th)', badge_text)
    return match.group(0) if match else None


def extract_premium_status(item: Dict[str, Any]) -> bool:
    """
    Check if user is a premium member.
    
    Args:
        item: Search result item from LinkedIn API
        
    Returns:
        True if premium member, False otherwise
        
    Example:
        >>> extract_premium_status(item)
        True
    """
    badge_icon = item.get("badgeIcon")
    if badge_icon:
        attributes = badge_icon.get("attributes", [])
        if attributes:
            detail_data = attributes[0].get("detailData", {})
            icon_type = detail_data.get("icon") if detail_data else None
            return icon_type and "PREMIUM" in icon_type
    return False


def extract_public_identifier(profile_url: Optional[str]) -> Optional[str]:
    """
    Extract public identifier (vanity URL) from profile URL.
    
    Args:
        profile_url: Full LinkedIn profile URL
        
    Returns:
        Public identifier or None
        
    Example:
        >>> extract_public_identifier("https://www.linkedin.com/in/katie-oberle-37a64a278?...")
        'katie-oberle-37a64a278'
    """
    if not profile_url:
        return None
    match = re.search(r'/in/([^?]+)', profile_url)
    return match.group(1) if match else None


def extract_company_from_job_title(job_title: Optional[str]) -> Optional[str]:
    """
    Extract company name from job title string.
    Handles various formats: "at Company", "@ Company", "At Company"
    
    Args:
        job_title: Job title/headline text
        
    Returns:
        Company name or None
        
    Example:
        >>> extract_company_from_job_title("Sr Talent Acquisition Specialist@ Med4Hire")
        'Med4Hire'
    """
    if not job_title:
        return None
    
    # Common patterns: "at", "@", "At", "AT"
    patterns = [
        r'\s+@\s+(.+)$',           # "Title @ Company"
        r'\s+at\s+(.+)$',          # "Title at Company"  
        r'\s+At\s+(.+)$',          # "Title At Company"
        r'\s+AT\s+(.+)$',          # "Title AT Company"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, job_title)
        if match:
            company = match.group(1).strip()
            return company
    
    return None


def extract_ring_status(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract profile ring status (HIRING, OPEN_TO_WORK, etc.).
    
    Args:
        item: Search result item from LinkedIn API
        
    Returns:
        Dict with profile_ring_status, is_hiring, and is_open_to_work flags
        
    Example:
        >>> extract_ring_status(item)
        {'profile_ring_status': 'HIRING', 'is_hiring': True, 'is_open_to_work': False}
    """
    image = item.get("image")
    if not image:
        return {
            "profile_ring_status": None,
            "is_hiring": False,
            "is_open_to_work": False
        }
    
    attributes = image.get("attributes", [])
    
    if attributes:
        detail_data = attributes[0].get("detailData", {})
        non_entity_profile = detail_data.get("nonEntityProfilePicture", {})
        ring_status = non_entity_profile.get("ringStatus", None) if non_entity_profile else None
        
        return {
            "profile_ring_status": ring_status,
            "is_hiring": ring_status == "HIRING",
            "is_open_to_work": ring_status == "OPEN_TO_WORK"
        }
    
    return {
        "profile_ring_status": None,
        "is_hiring": False,
        "is_open_to_work": False
    }


def extract_member_id(item: Dict[str, Any]) -> Optional[int]:
    """
    Extract numeric member ID from tracking URN.
    
    Args:
        item: Search result item from LinkedIn API
        
    Returns:
        Numeric member ID or None
        
    Example:
        >>> extract_member_id(item)
        1136267662
    """
    tracking_urn = item.get("trackingUrn", "")
    match = re.search(r'member:(\d+)', tracking_urn)
    return int(match.group(1)) if match else None


def parse_search_result(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse a complete search result item into a structured format.
    
    This is the main parsing function that extracts all available fields
    from a LinkedIn search result item. Uses defensive programming to
    handle missing or malformed data gracefully.
    
    Args:
        item: Raw search result item from LinkedIn API
        
    Returns:
        Parsed and enriched search result with all available fields.
        If parsing fails for specific fields, returns None for those fields
        rather than failing completely.
        
    Example:
        >>> result = parse_search_result(raw_item)
        >>> result['lead_name']
        'Katie Oberle'
        >>> result['mutual_connections_count']
        55
    """
    from pipa_cloud_operations.linkedin_api.linkedin_api.utils.helpers import (
        get_id_from_urn, 
        get_urn_from_raw_update
    )
    
    # Validate input
    if not item or not isinstance(item, dict):
        raise ValueError(f"Invalid search result item: expected dict, got {type(item)}")
    
    # Extract basic fields
    primary_subtitle = item.get("primarySubtitle")
    job_title = primary_subtitle.get("text", None) if primary_subtitle else None
    
    navigation_context = item.get("navigationContext")
    profile_url = navigation_context.get("url", None) if navigation_context else None
    
    # Extract image URL
    image_url = None
    image_data = item.get("image")
    if image_data:
        attributes = image_data.get("attributes", [])
        if attributes:
            for attribute in attributes:
                artifact = attribute.get("detailData", {})
                non_entity_profile = artifact.get("nonEntityProfilePicture", {})
                vector_image = non_entity_profile.get("vectorImage") if non_entity_profile else None
                image_artifacts = vector_image.get("artifacts", []) if vector_image else []
                if image_artifacts:
                    image_url = image_artifacts[0].get('fileIdentifyingUrlPathSegment')
                    break
    
    # Extract enhanced fields
    mutual_connections = extract_mutual_connections(item)
    ring_status_data = extract_ring_status(item)
    
    # Build complete result object
    return {
        # Original fields
        "urn_id": get_id_from_urn(
            get_urn_from_raw_update(item.get("entityUrn", None))
        ),
        "lead_name": item.get("title", {}).get("text", None) if isinstance(item.get("title"), dict) else None,
        "job_title": job_title,
        "location": item.get("secondarySubtitle", {}).get("text", None) if isinstance(item.get("secondarySubtitle"), dict) else None,
        "profile_url": profile_url,
        "image_url": image_url,
        "distance": item.get("entityCustomTrackingInfo", {}).get("memberDistance", None) if isinstance(item.get("entityCustomTrackingInfo"), dict) else None,
        
        # HIGH PRIORITY: Enhanced fields
        "public_identifier": extract_public_identifier(profile_url),
        "connection_degree": extract_connection_degree(item),
        "mutual_connections_count": mutual_connections["mutual_connections_count"],
        "mutual_connections_url": mutual_connections["mutual_connections_url"],
        "is_premium": extract_premium_status(item),
        "company": extract_company_from_job_title(job_title),
        
        # MEDIUM PRIORITY: Enhanced fields
        "member_id": extract_member_id(item),
        "profile_ring_status": ring_status_data["profile_ring_status"],
        "is_hiring": ring_status_data["is_hiring"],
        "is_open_to_work": ring_status_data["is_open_to_work"],
    }
