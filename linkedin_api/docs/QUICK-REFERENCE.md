# LinkedIn GraphQL API - Quick Reference

## Profile Cards Endpoint

### Get All Cards
```python
api.get_profile_card("ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA")
```

```bash
GET /profile/get-profile-cards/ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA
```

### Get Specific Card
```python
api.get_profile_card("ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA", card_type="EXPERIENCE")
```

```bash
GET /profile/get-profile-card/ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA/EXPERIENCE
```

### Available Card Types
- `EXPERIENCE` - Work history
- `EDUCATION` - Education history
- `LICENSES_AND_CERTIFICATIONS` - Certifications
- `SKILLS` - Skills and endorsements
- `RECOMMENDATIONS` - Recommendations received
- `INTERESTS` - Companies/schools followed
- `SERVICES` - Professional services
- `CONTENT_COLLECTIONS` - Featured content
- `PROJECTS` - Projects
- `VOLUNTEERING_EXPERIENCE` - Volunteer work
- `PUBLICATIONS` - Publications
- `PATENTS` - Patents
- `COURSES` - Courses taken
- `HONORS_AND_AWARDS` - Honors and awards
- `LANGUAGES` - Languages spoken
- `ORGANIZATIONS` - Organizations

---

## Contact Info Endpoint

### Get Contact Information
```python
api.get_profile_contact_info_graphql(urn_id="ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA")
```

```bash
GET /profile/get-contact-info/ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA
```

### Returns
- Email addresses
- Phone numbers
- Websites
- Social media profiles
- Birthday
- Address

---

## Skills Endpoint

### Get Skills
```python
api.get_profile_skills_graphql(urn_id="ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA")
```

```bash
GET /profile/get-profile-skills/ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA
```

### Returns
- Skills with endorsement counts
- Skill categories
- Top skills
- Endorsers

---

## Common Patterns

### Extract Companies from Response
```python
response = api.get_profile_card(profile_urn, "EXPERIENCE")
included = response.get('included', [])
companies = [
    item for item in included 
    if item.get('$type') == 'com.linkedin.voyager.dash.organization.Company'
]
```

### Extract Schools from Response
```python
response = api.get_profile_card(profile_urn, "EDUCATION")
included = response.get('included', [])
schools = [
    item for item in included 
    if item.get('$type') == 'com.linkedin.voyager.dash.organization.School'
]
```

### Find Card in Response
```python
def find_card(response, card_type):
    included = response.get('included', [])
    for item in included:
        if item.get('$type') == 'com.linkedin.voyager.dash.identity.profile.tetris.Card':
            if f",{card_type}," in item.get('entityUrn', ''):
                return item
    return None
```

### Resolve URN Reference
```python
def resolve_urn(urn, included):
    for item in included:
        if item.get('entityUrn') == urn:
            return item
    return None
```

---

## Error Handling

### Basic Try-Catch
```python
try:
    data = api.get_profile_card(profile_urn)
except Exception as e:
    print(f"Error: {e}")
```

### Handle Rate Limiting
```python
import time

def fetch_with_retry(api, profile_urn, max_retries=3):
    for attempt in range(max_retries):
        try:
            return api.get_profile_card(profile_urn)
        except Exception as e:
            if '429' in str(e) and attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 60  # Exponential backoff
                print(f"Rate limited. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
```

---

## Response Structure Cheat Sheet

### Top Level
```json
{
    "data": { ... },      // Query result
    "meta": { ... },      // Schema metadata
    "included": [ ... ]   // Related entities
}
```

### Common Entity Types
```python
# Cards
"com.linkedin.voyager.dash.identity.profile.tetris.Card"

# Organizations
"com.linkedin.voyager.dash.organization.Company"
"com.linkedin.voyager.dash.organization.School"

# Social
"com.linkedin.voyager.dash.social.SocialDetail"
"com.linkedin.voyager.dash.relationships.MemberRelationship"
```

### URN Formats
```python
# Profile
"urn:li:fsd_profile:ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA"

# Profile Card
"urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,EXPERIENCE,en_US)"

# Company
"urn:li:fsd_company:1063"

# School
"urn:li:fsd_school:12345"
```

---

## Performance Tips

### 1. Cache Responses
```python
import functools
import time

@functools.lru_cache(maxsize=100)
def get_profile_cached(profile_urn):
    return api.get_profile_card(profile_urn)
```

### 2. Batch Processing
```python
import concurrent.futures

def fetch_profiles(profile_urns):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(api.get_profile_card, urn): urn for urn in profile_urns}
        results = {}
        for future in concurrent.futures.as_completed(futures):
            urn = futures[future]
            try:
                results[urn] = future.result()
            except Exception as e:
                print(f"Error fetching {urn}: {e}")
        return results
```

### 3. Add Delays
```python
import time

for profile_urn in profile_urns:
    data = api.get_profile_card(profile_urn)
    # Process data...
    time.sleep(2)  # 2 second delay between requests
```

---

## Testing

### Test Profile URN
```python
# Use your own profile for testing
test_urn = "ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA"
```

### Validate Response
```python
def validate_response(response):
    assert 'data' in response, "Missing 'data' key"
    assert 'included' in response, "Missing 'included' key"
    assert isinstance(response['included'], list), "'included' should be a list"
    return True
```

### Check for Specific Card
```python
def has_card(response, card_type):
    included = response.get('included', [])
    for item in included:
        if item.get('$type') == 'com.linkedin.voyager.dash.identity.profile.tetris.Card':
            if f",{card_type}," in item.get('entityUrn', ''):
                return True
    return False
```

---

## Debugging

### Print Response Structure
```python
import json

response = api.get_profile_card(profile_urn)
print(json.dumps(response, indent=2))
```

### Count Entities by Type
```python
from collections import Counter

def count_entity_types(response):
    included = response.get('included', [])
    types = [item.get('$type') for item in included]
    return Counter(types)

# Usage
counts = count_entity_types(response)
for entity_type, count in counts.items():
    print(f"{entity_type}: {count}")
```

### Extract All URNs
```python
def extract_urns(response):
    included = response.get('included', [])
    return [item.get('entityUrn') for item in included if 'entityUrn' in item]
```

---

## Common Issues

### Issue: 400 Bad Request
**Cause**: Invalid URN format  
**Fix**: Ensure URN is URL-encoded
```python
import urllib.parse
encoded_urn = urllib.parse.quote(profile_urn, safe='')
```

### Issue: Empty Response
**Cause**: Card type doesn't exist for profile  
**Fix**: Check available cards first
```python
all_cards = api.get_profile_card(profile_urn)
card_urns = all_cards['data']['data']['identityDashProfileCardsByDeferredCards']['*elements']
print("Available cards:", card_urns)
```

### Issue: Missing Data
**Cause**: Profile privacy settings  
**Fix**: Check if you have permission to view the profile

---

## Quick Examples

### Get Work Experience
```python
response = api.get_profile_card(profile_urn, "EXPERIENCE")
# Parse experience from response.included
```

### Get Education
```python
response = api.get_profile_card(profile_urn, "EDUCATION")
# Parse education from response.included
```

### Get Contact Info
```python
contact = api.get_profile_contact_info_graphql(urn_id=profile_urn)
emails = contact.get('emailAddress', [])
phones = contact.get('phoneNumbers', [])
```

### Get Skills
```python
skills = api.get_profile_skills_graphql(urn_id=profile_urn)
# Parse skills from response
```

---

## Documentation Links

- **Full Documentation**: `README-GRAPHQL-ENDPOINTS.md`
- **Profile Cards**: `graphql-profile-cards-endpoint.md`
- **Contact Info**: `graphql-contact-info-endpoint.md`
- **Professional Info**: `graphql-professional-info-endpoint.md`
