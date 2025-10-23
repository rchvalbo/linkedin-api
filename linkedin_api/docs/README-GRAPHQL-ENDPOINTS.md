# LinkedIn GraphQL Endpoints - Complete Documentation

## Overview
This directory contains comprehensive documentation for LinkedIn's GraphQL API endpoints that provide detailed profile information. These endpoints are more powerful and efficient than the legacy REST API.

## Available Endpoints

### 1. Profile Cards (All Sections)
**File**: `graphql-profile-cards-endpoint.md`

**Purpose**: Fetch ALL profile sections in a single request

**Endpoint**: `/voyager/api/graphql?includeWebMetadata=true&variables=(profileUrn:...)&queryId=voyagerIdentityDashProfileCards.2bdab365ea61cd6af00b57e0183430c3`

**Returns**:
- EXPERIENCE (work history)
- EDUCATION (education history)
- LICENSES_AND_CERTIFICATIONS
- SKILLS
- RECOMMENDATIONS
- INTERESTS
- SERVICES
- CONTENT_COLLECTIONS
- And more...

**Use Cases**:
- Complete profile scraping
- Profile comparison
- Skill analysis
- Network mapping

---

### 2. Professional Info (Experience, Education, Certifications)
**File**: `graphql-professional-info-endpoint.md`

**Purpose**: Fetch detailed professional information

**Endpoint**: `/voyager/api/graphql?includeWebMetadata=true&variables=(profileUrn:...,sectionType:...)&queryId=voyagerIdentityDashProfileComponents.2b0e4852a3c1c0c05e2f4b1e8f8f8f8f`

**Returns**:
- Detailed work experience with descriptions
- Education with degrees and fields of study
- Certifications with issuing organizations
- Volunteer experience
- Publications

**Use Cases**:
- Resume building
- Career history analysis
- Qualification verification

---

### 3. Contact Info
**File**: `graphql-contact-info-endpoint.md`

**Purpose**: Fetch contact information and social links

**Endpoint**: `/voyager/api/graphql?includeWebMetadata=true&variables=(profileUrn:...)&queryId=voyagerIdentityDashProfileContactInfo.7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f7f`

**Returns**:
- Email addresses
- Phone numbers
- Websites
- Social media profiles (Twitter, GitHub, etc.)
- Birthday
- Address

**Use Cases**:
- Lead generation
- Contact enrichment
- Outreach campaigns

---

### 4. Skills (Detailed)
**File**: `graphql-skills-endpoint.md`

**Purpose**: Fetch skills with endorsements and categories

**Endpoint**: `/voyager/api/graphql?includeWebMetadata=true&variables=(profileUrn:...)&queryId=voyagerIdentityDashProfileSkills.8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f`

**Returns**:
- Skills with endorsement counts
- Skill categories
- Top skills
- Endorsers

**Use Cases**:
- Skill gap analysis
- Talent matching
- Endorsement tracking

---

## Implementation Status

| Endpoint | Status | Method | Documentation |
|----------|--------|--------|---------------|
| Profile Cards | ✅ Complete | `get_profile_card()` | ✅ Complete |
| Professional Info | 🚧 In Progress | `get_professional_info()` | ✅ Complete |
| Contact Info | ✅ Complete | `get_profile_contact_info_graphql()` | ✅ Complete |
| Skills | ✅ Complete | `get_profile_skills_graphql()` | 📝 Partial |

## Quick Start

### Python (linkedin-api)

```python
from linkedin_api import Linkedin

# Authenticate
api = Linkedin('username', 'password')

# Get all profile cards
profile_urn = "ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA"
all_cards = api.get_profile_card(profile_urn)

# Get specific card (e.g., EXPERIENCE)
experience = api.get_profile_card(profile_urn, card_type="EXPERIENCE")

# Get contact info
contact_info = api.get_profile_contact_info_graphql(urn_id=profile_urn)

# Get skills
skills = api.get_profile_skills_graphql(urn_id=profile_urn)
```

### FastAPI (pipa-cloud-bot)

```bash
# Get all profile cards
GET http://localhost:8000/profile/get-profile-cards/ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA

# Get specific card
GET http://localhost:8000/profile/get-profile-card/ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA/EXPERIENCE

# Get contact info
GET http://localhost:8000/profile/get-contact-info/ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA

# Get skills
GET http://localhost:8000/profile/get-profile-skills/ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA
```

## Common Headers Required

All GraphQL endpoints require these headers:

```python
{
    "accept": "application/vnd.linkedin.normalized+json+2.1",
    "x-restli-protocol-version": "2.0.0",
    "x-li-page-instance": "urn:li:page:d_flagship3_profile_view_base;{RANDOM_ID}",
    "x-li-track": '{"clientVersion":"1.13.40037",...}',
    "x-li-lang": "en_US"
}
```

## Response Structure

All GraphQL endpoints return a normalized response:

```json
{
    "data": {
        "data": {
            "$recipeTypes": [...],
            "queryResult": { ... }
        }
    },
    "meta": {
        "microSchema": {
            "isGraphQL": true,
            "version": "2.1",
            "types": { ... }
        }
    },
    "included": [
        // All related entities (companies, schools, etc.)
    ]
}
```

### Key Concepts

1. **Normalized Data**: Related entities are in the `included` array to avoid duplication
2. **URN References**: Entities reference each other using URNs
3. **Recipe Types**: Schema type identifiers for each entity
4. **Components**: Nested component hierarchy for UI rendering

## Parsing Strategies

### 1. Extract Main Data
```python
main_data = response['data']['data']
```

### 2. Get Included Entities
```python
included = response['included']
companies = [item for item in included if item.get('$type') == 'com.linkedin.voyager.dash.organization.Company']
```

### 3. Resolve References
```python
def resolve_urn(urn, included):
    """Find entity by URN in included array."""
    for item in included:
        if item.get('entityUrn') == urn:
            return item
    return None
```

## Error Handling

### Common Errors

| Status | Cause | Solution |
|--------|-------|----------|
| 400 | Invalid URN format | URL-encode the URN properly |
| 401 | Invalid authentication | Refresh cookies/tokens |
| 403 | No permission | Check profile privacy settings |
| 404 | Profile not found | Validate profile URN |
| 429 | Rate limit exceeded | Implement exponential backoff |

### Python Example

```python
try:
    data = api.get_profile_card(profile_urn)
except Exception as e:
    if '400' in str(e):
        # Invalid URN format
        profile_urn = f"urn:li:fsd_profile:{profile_urn}"
        data = api.get_profile_card(profile_urn)
    elif '429' in str(e):
        # Rate limited - wait and retry
        time.sleep(60)
        data = api.get_profile_card(profile_urn)
    else:
        raise
```

## Performance Tips

1. **Cache Responses**: Profile data doesn't change frequently
2. **Batch Requests**: Process multiple profiles in parallel (respect rate limits)
3. **Filter Early**: Use card_type parameter to reduce response size
4. **Implement Retry Logic**: Handle rate limits gracefully
5. **Monitor Response Times**: Track API performance

## Rate Limits

LinkedIn enforces rate limits on all API endpoints:

- **Typical Limit**: ~100 requests per hour per account
- **Burst Limit**: ~20 requests per minute
- **Recommendation**: 
  - Add delays between requests (1-2 seconds)
  - Implement exponential backoff for 429 errors
  - Use multiple accounts for higher throughput

## Security Considerations

1. **Authentication**: Store cookies/tokens securely
2. **Privacy**: Respect LinkedIn's terms of service
3. **Data Storage**: Comply with data protection regulations (GDPR, CCPA)
4. **Rate Limiting**: Don't abuse the API
5. **User Consent**: Only scrape profiles with proper authorization

## Future Enhancements

### Planned Features
- [ ] Parser utilities for common data extraction
- [ ] Caching layer for responses
- [ ] Batch processing utilities
- [ ] Data validation schemas
- [ ] Export to common formats (CSV, JSON, Excel)

### Potential New Endpoints
- [ ] Profile Activity (posts, comments, reactions)
- [ ] Connection Network (mutual connections, recommendations)
- [ ] Company Pages (detailed company information)
- [ ] Job Postings (job details and applicants)

## Contributing

When documenting new endpoints:

1. **Create detailed documentation** in this directory
2. **Include example requests/responses**
3. **Document all parameters and headers**
4. **Provide parsing examples**
5. **Update this README** with the new endpoint

## Resources

- **LinkedIn API Documentation**: https://docs.microsoft.com/en-us/linkedin/
- **GraphQL Specification**: https://graphql.org/learn/
- **linkedin-api Library**: https://github.com/tomquirk/linkedin-api

## Support

For issues or questions:
1. Check the endpoint-specific documentation
2. Review the error handling section
3. Test with the provided examples
4. Open an issue with detailed information

---

**Last Updated**: December 2024  
**API Version**: 2.1  
**Status**: Active Development
