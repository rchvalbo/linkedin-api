# LinkedIn GraphQL Profile Cards Endpoint Documentation

## Overview
The Profile Cards endpoint returns **ALL** profile sections (cards) in a single GraphQL query. This is the most comprehensive way to fetch detailed profile information including experience, education, certifications, skills, recommendations, interests, and more.

## Endpoint Details

### GraphQL Query
```
GET /voyager/api/graphql?includeWebMetadata=true&variables=(profileUrn:urn%3Ali%3Afsd_profile%3A{PROFILE_URN_ID})&queryId=voyagerIdentityDashProfileCards.2bdab365ea61cd6af00b57e0183430c3
```

### Required Headers
```python
{
    "accept": "application/vnd.linkedin.normalized+json+2.1",
    "x-restli-protocol-version": "2.0.0",
    "x-li-page-instance": "urn:li:page:d_flagship3_profile_view_base;{RANDOM_BASE64_ID}",
    "x-li-pem-metadata": "Voyager - Profile=profile-tab-deferred-cards",
    "x-li-track": '{"clientVersion":"1.13.40037","mpVersion":"1.13.40037","osName":"web","timezoneOffset":-4,"timezone":"America/New_York","deviceFormFactor":"DESKTOP","mpName":"voyager-web","displayDensity":2,"displayWidth":6400,"displayHeight":2666}',
    "x-li-lang": "en_US"
}
```

### Query ID
- **Current**: `voyagerIdentityDashProfileCards.2bdab365ea61cd6af00b57e0183430c3`
- **Purpose**: Identifies the specific GraphQL query schema to execute
- **Note**: This may change over time as LinkedIn updates their API

## Response Structure

### Top-Level Structure
```json
{
    "data": {
        "data": {
            "$recipeTypes": [...],
            "identityDashProfileCardsByDeferredCards": {
                "*elements": [
                    "urn:li:fsd_profileCard:(PROFILE_URN,SERVICES,en_US)",
                    "urn:li:fsd_profileCard:(PROFILE_URN,CONTENT_COLLECTIONS,en_US)",
                    "urn:li:fsd_profileCard:(PROFILE_URN,SKILLS,en_US)",
                    "urn:li:fsd_profileCard:(PROFILE_URN,RECOMMENDATIONS,en_US)",
                    "urn:li:fsd_profileCard:(PROFILE_URN,INTERESTS,en_US)"
                ],
                "$type": "com.linkedin.restli.common.CollectionResponse"
            }
        }
    },
    "meta": {
        "microSchema": {
            "isGraphQL": true,
            "version": "2.1",
            "types": { ... }
        }
    },
    "included": [ ... ]  // All the actual card data
}
```

### Card Types Returned
The `*elements` array contains URNs for available profile cards:
- **SERVICES**: Professional services offered
- **CONTENT_COLLECTIONS**: Featured content/posts
- **SKILLS**: Skills and endorsements
- **RECOMMENDATIONS**: Recommendations received
- **INTERESTS**: Companies, schools, and topics followed

### Additional Card Types (may appear in included data)
- **EXPERIENCE**: Work history
- **EDUCATION**: Education history  
- **LICENSES_AND_CERTIFICATIONS**: Certifications
- **PROJECTS**: Projects
- **VOLUNTEERING_EXPERIENCE**: Volunteer work
- **PUBLICATIONS**: Publications
- **PATENTS**: Patents
- **COURSES**: Courses taken
- **HONORS_AND_AWARDS**: Honors and awards
- **TEST_SCORES**: Test scores
- **LANGUAGES**: Languages spoken
- **ORGANIZATIONS**: Organizations

## Included Data Structure

The `included` array contains the actual data for all cards and related entities. Each object has:
- **entityUrn**: Unique identifier
- **$type**: Type of entity (e.g., `com.linkedin.voyager.dash.identity.profile.tetris.Card`)
- **$recipeTypes**: Schema type identifiers
- **Data fields**: Specific to the entity type

### Common Entity Types in Response

#### 1. Profile Cards
```json
{
    "entityUrn": "urn:li:fsd_profileCard:(PROFILE_URN,CARD_TYPE,LOCALE)",
    "$type": "com.linkedin.voyager.dash.identity.profile.tetris.Card",
    "topComponents": [...],
    "subComponents": [...],
    "cardStyle": "DEFAULT"
}
```

#### 2. Companies
```json
{
    "entityUrn": "urn:li:fsd_company:1063",
    "$type": "com.linkedin.voyager.dash.organization.Company",
    "name": "Cisco",
    "logoResolutionResult": {
        "vectorImage": {
            "rootUrl": "https://media.licdn.com/dms/image/...",
            "artifacts": [...]
        }
    }
}
```

#### 3. Schools
```json
{
    "entityUrn": "urn:li:fsd_school:...",
    "$type": "com.linkedin.voyager.dash.organization.School",
    "name": "School Name",
    "logo": {...}
}
```

#### 4. Social Details (for posts/activities)
```json
{
    "entityUrn": "urn:li:fsd_socialDetail:(...)",
    "$type": "com.linkedin.voyager.dash.social.SocialDetail",
    "threadUrn": "urn:li:ugcPost:...",
    "allowedCommentersScope": "ALL"
}
```

#### 5. Member Relationships
```json
{
    "entityUrn": "urn:li:fsd_memberRelationship:...",
    "$type": "com.linkedin.voyager.dash.relationships.MemberRelationship",
    "memberRelationship": {
        "noConnection": {
            "memberDistance": "DISTANCE_2"
        }
    }
}
```

## Parsing Strategy

### Step 1: Extract Card URNs
```python
card_urns = response['data']['data']['identityDashProfileCardsByDeferredCards']['*elements']
```

### Step 2: Find Card Data in Included Array
```python
included = response['included']
cards = {}

for item in included:
    if item.get('$type') == 'com.linkedin.voyager.dash.identity.profile.tetris.Card':
        entity_urn = item.get('entityUrn')
        # Extract card type from URN: urn:li:fsd_profileCard:(URN,CARD_TYPE,LOCALE)
        card_type = entity_urn.split(',')[1]
        cards[card_type] = item
```

### Step 3: Extract Related Entities
```python
companies = [item for item in included if item.get('$type') == 'com.linkedin.voyager.dash.organization.Company']
schools = [item for item in included if item.get('$type') == 'com.linkedin.voyager.dash.organization.School']
```

### Step 4: Parse Components
Each card contains `topComponents` and `subComponents` arrays with nested component structures:
- **EntityComponent**: Individual items (jobs, education entries, etc.)
- **FixedListComponent**: Lists of items
- **TabComponent**: Tabbed sections
- **ActionComponent**: Interactive elements

## Example: Extracting Experience Data

```python
def extract_experience(card_data):
    """Extract work experience from EXPERIENCE card."""
    experiences = []
    
    # Navigate through component hierarchy
    for component in card_data.get('topComponents', []):
        if 'components' in component:
            for sub_component in component['components']:
                # Look for EntityComponent with position data
                entity = sub_component.get('components', {}).get('entityComponent')
                if entity:
                    experience = {
                        'title': entity.get('titleV2', {}).get('text'),
                        'subtitle': entity.get('subtitle', {}).get('text'),  # Company name
                        'caption': entity.get('caption', {}).get('text'),    # Date range
                        'metadata': entity.get('metadata', {}).get('text')   # Duration
                    }
                    experiences.append(experience)
    
    return experiences
```

## Example: Extracting Skills Data

```python
def extract_skills(card_data):
    """Extract skills from SKILLS card."""
    skills = []
    
    # Skills are typically in a pagedListComponent
    for component in card_data.get('topComponents', []):
        paged_list = component.get('components', {}).get('pagedListComponent')
        if paged_list:
            for item in paged_list.get('components', {}).get('elements', []):
                entity = item.get('components', {}).get('entityComponent')
                if entity:
                    skill = {
                        'name': entity.get('titleV2', {}).get('text'),
                        'endorsements': entity.get('caption', {}).get('text')
                    }
                    skills.append(skill)
    
    return skills
```

## Performance Considerations

### Response Size
- **Typical size**: 500KB - 2MB (depending on profile completeness)
- **Includes**: All cards, related entities, schema definitions
- **Recommendation**: Cache responses when possible

### Rate Limiting
- Same rate limits as other LinkedIn API endpoints
- Consider batching profile requests
- Implement exponential backoff for 429 errors

## Error Handling

### Common Errors

#### 400 Bad Request
- **Cause**: Invalid URN format or missing URL encoding
- **Solution**: Ensure URN is properly URL-encoded

#### 401 Unauthorized
- **Cause**: Invalid or expired authentication
- **Solution**: Refresh authentication cookies/tokens

#### 403 Forbidden
- **Cause**: No permission to view profile
- **Solution**: Check if profile is private or connection required

#### 404 Not Found
- **Cause**: Profile doesn't exist or has been deleted
- **Solution**: Validate profile URN before making request

## Python Implementation

```python
def get_profile_cards(self, profile_urn, locale="en_US"):
    """Fetch all profile cards using GraphQL API."""
    
    # Ensure full URN format
    if not profile_urn.startswith("urn:li:fsd_profile:"):
        profile_urn = f"urn:li:fsd_profile:{profile_urn}"
    
    # GraphQL query details
    query_id = "voyagerIdentityDashProfileCards.2bdab365ea61cd6af00b57e0183430c3"
    
    # URL encode the URN
    import urllib.parse
    encoded_urn = urllib.parse.quote(profile_urn, safe='')
    variables = f"(profileUrn:{encoded_urn})"
    full_url = f"/graphql?includeWebMetadata=true&variables={variables}&queryId={query_id}"
    
    # Generate random page instance ID
    import random, base64
    random_bytes = bytes([random.randint(0, 255) for _ in range(16)])
    page_instance_id = base64.b64encode(random_bytes).decode('utf-8').rstrip('=')
    page_instance = f"urn:li:page:d_flagship3_profile_view_base;{page_instance_id}"
    
    # Required headers
    headers = {
        "accept": "application/vnd.linkedin.normalized+json+2.1",
        "x-restli-protocol-version": "2.0.0",
        "x-li-page-instance": page_instance,
        "x-li-pem-metadata": "Voyager - Profile=profile-tab-deferred-cards",
        "x-li-track": '{"clientVersion":"1.13.40037","mpVersion":"1.13.40037","osName":"web","timezoneOffset":-4,"timezone":"America/New_York","deviceFormFactor":"DESKTOP","mpName":"voyager-web","displayDensity":2,"displayWidth":6400,"displayHeight":2666}',
        "x-li-lang": "en_US"
    }
    
    try:
        res = self._fetch(full_url, headers=headers)
        return res.json()
    except Exception as e:
        self.logger.error(f"Failed to fetch profile cards: {e}")
        return {}
```

## Use Cases

### 1. Complete Profile Scraping
Fetch all profile information in a single request instead of multiple endpoint calls.

### 2. Profile Comparison
Compare profiles by analyzing their cards and components.

### 3. Skill Analysis
Extract and analyze skills across multiple profiles.

### 4. Network Mapping
Build relationship graphs using member relationship data.

### 5. Content Discovery
Find featured posts and content collections from profiles.

## Next Steps

1. **Parse Specific Cards**: Implement parsers for EXPERIENCE, EDUCATION, CERTIFICATIONS
2. **Extract Structured Data**: Convert nested components into clean data structures
3. **Handle Edge Cases**: Account for missing fields and optional data
4. **Optimize Performance**: Cache responses and implement efficient parsing
5. **Document Card Schemas**: Create detailed documentation for each card type's structure

## Related Endpoints

- **Profile Skills (GraphQL)**: More detailed skills with categories
- **Profile Contact Info (GraphQL)**: Contact information and social links
- **Profile (Legacy REST)**: Basic profile information

## Notes

- This endpoint returns **deferred cards** - cards that load after initial profile view
- Some cards may not be present if the profile doesn't have that information
- The `included` array uses a normalized structure to avoid data duplication
- Entity relationships are represented by URN references that need to be resolved from the `included` array
