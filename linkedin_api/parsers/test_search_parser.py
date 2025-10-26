"""
Unit tests for search_parser module
"""

import pytest
from search_parser import (
    extract_mutual_connections,
    extract_connection_degree,
    extract_premium_status,
    extract_public_identifier,
    extract_company_from_job_title,
    extract_ring_status,
    extract_member_id,
)


class TestExtractMutualConnections:
    """Test mutual connections extraction"""
    
    def test_with_mutual_connections(self):
        item = {
            "insightsResolutionResults": [{
                "simpleInsight": {
                    "title": {"text": "55 mutual connections"},
                    "navigationUrl": "https://linkedin.com/..."
                }
            }]
        }
        result = extract_mutual_connections(item)
        assert result["mutual_connections_count"] == 55
        assert result["mutual_connections_url"] == "https://linkedin.com/..."
    
    def test_with_no_mutual_connections(self):
        item = {"insightsResolutionResults": []}
        result = extract_mutual_connections(item)
        assert result["mutual_connections_count"] == 0
        assert result["mutual_connections_url"] is None
    
    def test_with_single_mutual_connection(self):
        item = {
            "insightsResolutionResults": [{
                "simpleInsight": {
                    "title": {"text": "1 mutual connection"}
                }
            }]
        }
        result = extract_mutual_connections(item)
        assert result["mutual_connections_count"] == 1


class TestExtractConnectionDegree:
    """Test connection degree extraction"""
    
    def test_first_degree(self):
        item = {"badgeText": {"text": "• 1st"}}
        assert extract_connection_degree(item) == "1st"
    
    def test_second_degree(self):
        item = {"badgeText": {"text": "• 2nd"}}
        assert extract_connection_degree(item) == "2nd"
    
    def test_third_degree(self):
        item = {"badgeText": {"text": "• 3rd"}}
        assert extract_connection_degree(item) == "3rd"
    
    def test_no_badge_text(self):
        item = {}
        assert extract_connection_degree(item) is None


class TestExtractPremiumStatus:
    """Test premium status extraction"""
    
    def test_premium_member(self):
        item = {
            "badgeIcon": {
                "attributes": [{
                    "detailData": {
                        "icon": "IMG_PREMIUM_BUG_GOLD_48DP"
                    }
                }]
            }
        }
        assert extract_premium_status(item) is True
    
    def test_non_premium_member(self):
        item = {"badgeIcon": {}}
        assert extract_premium_status(item) is False
    
    def test_no_badge_icon(self):
        item = {}
        assert extract_premium_status(item) is False


class TestExtractPublicIdentifier:
    """Test public identifier extraction"""
    
    def test_standard_url(self):
        url = "https://www.linkedin.com/in/katie-oberle-37a64a278?miniProfileUrn=..."
        assert extract_public_identifier(url) == "katie-oberle-37a64a278"
    
    def test_simple_url(self):
        url = "https://www.linkedin.com/in/johndoe"
        assert extract_public_identifier(url) == "johndoe"
    
    def test_none_url(self):
        assert extract_public_identifier(None) is None
    
    def test_invalid_url(self):
        url = "https://www.linkedin.com/company/test"
        assert extract_public_identifier(url) is None


class TestExtractCompanyFromJobTitle:
    """Test company extraction from job title"""
    
    def test_at_symbol(self):
        title = "Sr Talent Acquisition Specialist@ Med4Hire"
        assert extract_company_from_job_title(title) == "Med4Hire"
    
    def test_at_word_lowercase(self):
        title = "Senior Recruiting Professional at CentralSquare Technologies"
        assert extract_company_from_job_title(title) == "CentralSquare Technologies"
    
    def test_at_word_capitalized(self):
        title = "Talent Acquisition Specialist At Hilton Grand Vacations"
        assert extract_company_from_job_title(title) == "Hilton Grand Vacations"
    
    def test_at_word_uppercase(self):
        title = "Recruiter AT Google"
        assert extract_company_from_job_title(title) == "Google"
    
    def test_no_company(self):
        title = "Assistant Director of Engineering"
        assert extract_company_from_job_title(title) is None
    
    def test_none_title(self):
        assert extract_company_from_job_title(None) is None
    
    def test_with_spaces(self):
        title = "Engineer @ Google Inc."
        assert extract_company_from_job_title(title) == "Google Inc."


class TestExtractRingStatus:
    """Test ring status extraction"""
    
    def test_hiring_status(self):
        item = {
            "image": {
                "attributes": [{
                    "detailData": {
                        "nonEntityProfilePicture": {
                            "ringStatus": "HIRING"
                        }
                    }
                }]
            }
        }
        result = extract_ring_status(item)
        assert result["profile_ring_status"] == "HIRING"
        assert result["is_hiring"] is True
        assert result["is_open_to_work"] is False
    
    def test_open_to_work_status(self):
        item = {
            "image": {
                "attributes": [{
                    "detailData": {
                        "nonEntityProfilePicture": {
                            "ringStatus": "OPEN_TO_WORK"
                        }
                    }
                }]
            }
        }
        result = extract_ring_status(item)
        assert result["profile_ring_status"] == "OPEN_TO_WORK"
        assert result["is_hiring"] is False
        assert result["is_open_to_work"] is True
    
    def test_no_ring_status(self):
        item = {"image": {"attributes": []}}
        result = extract_ring_status(item)
        assert result["profile_ring_status"] is None
        assert result["is_hiring"] is False
        assert result["is_open_to_work"] is False


class TestExtractMemberId:
    """Test member ID extraction"""
    
    def test_valid_tracking_urn(self):
        item = {"trackingUrn": "urn:li:member:1136267662"}
        assert extract_member_id(item) == 1136267662
    
    def test_no_tracking_urn(self):
        item = {}
        assert extract_member_id(item) is None
    
    def test_invalid_tracking_urn(self):
        item = {"trackingUrn": "urn:li:company:12345"}
        assert extract_member_id(item) is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
