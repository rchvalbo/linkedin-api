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

---

## 📊 Endpoint Comparison

### ✅ RECOMMENDED: Profile Components (Experience/Education)

**Endpoint:** `voyagerIdentityDashProfileComponents`  
**QueryId:** `c5d4db426a0f8247b8ab7bc1d660775a`

```python
# Work Experience
api.get_profile_experience(profile_urn)

# Education
api.get_profile_education(profile_urn)
```

**Returns:**
- ✅ Job titles, companies, dates
- ✅ Full job descriptions
- ✅ Skills per position
- ✅ Company logos (multiple sizes)
- ✅ Company URLs
- ✅ School information
- ✅ Degrees and fields of study

**URL Pattern:**
```
/graphql?variables=(profileUrn:urn%3Ali%3Afsd_profile%3A{ID},sectionType:experience,locale:en_US)&queryId=c5d4db426a0f8247b8ab7bc1d660775a
```

**Section Types:**
- `experience` - Work history
- `education` - Education history
- `certifications` - Licenses and certifications (likely)
- `projects` - Projects
- `volunteering` - Volunteer experience

---

### ✅ Profile Skills (GraphQL)

**Endpoint:** `voyagerIdentityDashProfileSkills`

```python
api.get_profile_skills_graphql(urn_id=profile_urn)
```

**Returns:**
- Skills with endorsement counts
- Skill categories
- Top skills

**URL Pattern:**
```
/graphql?variables=(profileUrn:{urn})&queryId=voyagerIdentityDashProfileSkills...
```

---

### ✅ Profile Contact Info (GraphQL)

**Endpoint:** `voyagerIdentityDashProfileContactInfo`

```python
api.get_profile_contact_info_graphql(public_id="johndoe")
```

**Returns:**
- Email addresses
- Phone numbers
- Websites
- Social media links
- Birthday

**URL Pattern:**
```
/graphql?variables=(vanityName:{public_id})&queryId=voyagerIdentityDashProfileContactInfo...
```

---

### ✅ Basic Profile (GraphQL)

**Endpoint:** `/identity/dash/profiles/{profile_urn}`

```python
api.get_profile_graphql(public_id="johndoe")
# or
api.get_profile_graphql(urn_id="ACoAAAS7RzQB...")
```

**Returns:**
- Name, headline, summary
- Profile picture
- Location
- Premium/verification status

**URL Pattern:**
```
/identity/dash/profiles/{profile_urn}?decorationId=com.linkedin.voyager.dash.deco.identity.profile.FullProfile-76
```

---

### ⚠️ Profile Cards (Metadata Only)

**Endpoint:** `voyagerIdentityDashProfileCards`

```python
api.get_profile_card(profile_urn)
```

**Returns:**
- ⚠️ **Metadata only** - List of available sections
- ⚠️ **Empty `included` array** - No actual data
- URN references to profile cards

**Use Case:** Discover which sections exist (not for data retrieval)

---

## 🔄 Migration from Legacy Endpoint

### Old Way (DEPRECATED ❌)

```python
# This NO LONGER WORKS
profile = api.get_profile(public_id="johndoe")
experience = profile.get('experience', [])
education = profile.get('education', [])

# Old format:
{
  "title": "Software Engineer",
  "companyName": "Google",
  "locationName": "Seattle, WA",
  "timePeriod": {
    "startDate": {"year": 2020, "month": 1}
  }
}
```

### New Way (CURRENT ✅)

```python
# Use ProfileComponents endpoint
experience_data = api.get_profile_experience(profile_urn)
parsed = parse_experience_response(experience_data)

# New format:
{
  "title": "Software Engineer",
  "company": "Google",
  "company_logo": "https://...",
  "start_date": "2020-01-01",
  "end_date": null,
  "is_current": true,
  "description": "Full job description...",
  "skills": ["Python", "Java", "AWS"]
}
```

---

## 📝 Common Patterns

### Get Complete Profile Data

```python
from linkedin_api import Linkedin

api = Linkedin('username', 'password')

# 1. Get basic profile
profile = api.get_profile_graphql(public_id="johndoe")
profile_urn = profile['profile_urn']

# 2. Get work experience
experience = api.get_profile_experience(profile_urn)
parsed_exp = parse_experience_response(experience)

# 3. Get education
education = api.get_profile_education(profile_urn)
parsed_edu = parse_education_response(education)

# 4. Get skills
skills = api.get_profile_skills_graphql(urn_id=profile_urn)

# 5. Get contact info
contact = api.get_profile_contact_info_graphql(public_id="johndoe")

# Combine all data
complete_profile = {
    **profile,
    "work_experience": parsed_exp,
    "education": parsed_edu,
    "skills": skills,
    "contact": contact
}
```

---

## 🎯 Target Data Formats

### Work Experience

```json
{
  "work_experience": [
    {
      "title": "Senior Software Engineer",
      "company": "Google",
      "company_id": "1441",
      "company_url": "https://www.linkedin.com/company/1441/",
      "company_logo": "https://media.licdn.com/dms/.../200_200/...",
      "start_date": "2020-01-01",
      "end_date": null,
      "is_current": true,
      "location": null,
      "description": "Leading development...",
      "skills": ["Python", "AWS", "Kubernetes"]
    }
  ]
}
```

### Education

```json
{
  "education": [
    {
      "school": "Stanford University",
      "school_logo": "https://...",
      "degree": "Master of Science - MS",
      "field_of_study": "Computer Science",
      "start_year": 2018,
      "end_year": 2020,
      "description": "Focus on Machine Learning"
    }
  ]
}
```

---

## 🔑 URN vs Public ID

### Public ID (vanityName)
- Custom URL identifier
- Example: `"johndoe"`
- User-friendly
- Used in profile URLs: `linkedin.com/in/johndoe`

### URN ID
- Internal LinkedIn identifier
- Example: `"ACoAAAS7RzQB5MFgx7URQOOa7dShFKQhfdIWxms"`
- System-generated
- Used in API calls

### Full URN
- Complete URN format
- Example: `"urn:li:fsd_profile:ACoAAAS7RzQB5MFgx7URQOOa7dShFKQhfdIWxms"`

### Conversion

```python
# Get URN from public_id
profile = api.get_profile_graphql(public_id="johndoe")
urn_id = profile['profile_urn']  
# Returns: "urn:li:fsd_profile:ACoAAAS7RzQB..."

# Extract ID from full URN
urn_id = "urn:li:fsd_profile:ACoAAAS7RzQB..."
profile_id = urn_id.split(':')[-1]  # "ACoAAAS7RzQB..."
```

---

## ⚠️ Common Issues

### Issue 1: Empty `included` Array

**Problem:** Response has `"included": []`

**Cause:** Using ProfileCards endpoint (metadata only)

**Solution:** Use ProfileComponents endpoint instead

```python
# ❌ Wrong - Returns metadata only
api.get_profile_card(profile_urn)

# ✅ Correct - Returns actual data
api.get_profile_experience(profile_urn)
```

### Issue 2: Date Parsing

**Problem:** Dates are text strings like "2017 - 2018 · 1 yr"

**Solution:** Implement date parser

```python
def parse_date_range(date_text):
    # Handle formats:
    # "2017 - 2018 · 1 yr"
    # "Jun 2025 - Present"
    # "2021 - 2023 · 2 yrs 3 mos"
    
    is_current = 'Present' in date_text
    # ... parsing logic
    return start_date, end_date, is_current
```

### Issue 3: Missing Company Names

**Problem:** Company name not in response

**Solutions:**
1. Look for `subtitle` in entityComponent
2. Extract company ID from URL
3. Lookup company entity in `included` array
4. Make separate company API call

---

## 🚀 FastAPI Examples

### Experience Endpoint

```python
@router.get("/profile/{profileUrn}/experience")
def getExperience(profileUrn: str, authInfo = authDep):
    """Get work experience for a profile."""
    api = CreateLinkedinApi(authInfo).api
    raw_data = api.get_profile_experience(profileUrn)
    parsed = parse_experience_response(raw_data)
    return {"work_experience": parsed}
```

### Education Endpoint

```python
@router.get("/profile/{profileUrn}/education")
def getEducation(profileUrn: str, authInfo = authDep):
    """Get education for a profile."""
    api = CreateLinkedinApi(authInfo).api
    raw_data = api.get_profile_education(profileUrn)
    parsed = parse_education_response(raw_data)
    return {"education": parsed}
```

### Complete Profile

```python
@router.get("/profile/{identifier}/complete")
def getCompleteProfile(identifier: str, authInfo = authDep):
    """Get complete profile data."""
    api = CreateLinkedinApi(authInfo).api
    
    # Determine if identifier is public_id or urn_id
    if len(identifier) > 20:
        profile = api.get_profile_graphql(urn_id=identifier)
        public_id = profile.get('public_identifier')
        profile_urn = identifier
    else:
        profile = api.get_profile_graphql(public_id=identifier)
        public_id = identifier
        profile_urn = profile.get('profile_urn')
    
    # Fetch all data
    experience = parse_experience_response(
        api.get_profile_experience(profile_urn)
    )
    education = parse_education_response(
        api.get_profile_education(profile_urn)
    )
    skills = api.get_profile_skills_graphql(urn_id=profile_urn)
    contact = api.get_profile_contact_info_graphql(public_id=public_id)
    
    return {
        **profile,
        "work_experience": experience,
        "education": education,
        "skills": skills,
        "contact": contact
    }
```

---

## 📚 Documentation Links

- [**Profile Components (Experience/Education)**](./profile-components-experience-endpoint.md) - **RECOMMENDED**
- [Profile Skills](../graphql-skills-endpoint.md)
- [Profile Contact Info](../graphql-contact-info-endpoint.md)
- [Professional Info Variations](./graphql-professional-info-endpoint.md) - Reference
- [Profile Cards](./graphql-profile-cards-endpoint.md) - Metadata only
- [Deferred Loading Issue](./DEFERRED-LOADING-ISSUE.md) - Explanation

---

**Last Updated:** 2025-10-23  
**Status:** ✅ Current

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
