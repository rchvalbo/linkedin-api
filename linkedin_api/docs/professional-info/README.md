# Professional Information Endpoints - Documentation Index

## 📚 Overview

This directory contains documentation for LinkedIn GraphQL endpoints that retrieve professional information including work experience, education, certifications, and related data.

## 🎯 **NEW: Complete Data Architecture Guide**

**📖 [Read the Data Architecture Guide](../DATA-ARCHITECTURE.md)** - Comprehensive guide explaining:
- Which endpoint returns which data
- Why experience/education are separate from profile info
- How to build a complete profile
- Data completeness matrix
- Common issues and solutions

---

## 🎯 Quick Start - Which Endpoint Should I Use?

### For Work Experience ✅
**Use:** [`voyagerIdentityDashProfileComponents`](./profile-components-experience-endpoint.md) with `sectionType:experience`

**Why:** Returns complete job details including titles, descriptions, dates, skills, and company logos.

**Example:**
```python
api.get_profile_experience(profile_urn)
```

### For Education ✅
**Use:** [`voyagerIdentityDashProfileComponents`](./profile-components-experience-endpoint.md) with `sectionType:education`

**Why:** Returns complete education details including schools, degrees, fields of study, and dates.

**Example:**
```python
api.get_profile_education(profile_urn)
```

### For Skills ✅
**Use:** [`voyagerIdentityDashProfileSkills`](../graphql-skills-endpoint.md)

**Why:** Dedicated endpoint with endorsement counts and skill categories.

**Example:**
```python
api.get_profile_skills_graphql(urn_id)
```

### For Contact Info ✅
**Use:** [`voyagerIdentityDashProfileContactInfo`](../graphql-contact-info-endpoint.md)

**Why:** Returns email, phone, websites, and social links.

**Example:**
```python
api.get_profile_contact_info_graphql(public_id)
```

---

## 📖 Documentation Files

### ✅ Working Endpoints

| Document | Endpoint | Purpose | Status |
|----------|----------|---------|--------|
| [**Profile Components - Experience**](./profile-components-experience-endpoint.md) | `voyagerIdentityDashProfileComponents` | **Work experience & education** | ✅ **RECOMMENDED** |
| [Skills Endpoint](../graphql-skills-endpoint.md) | `voyagerIdentityDashProfileSkills` | Skills with endorsements | ✅ Working |
| [Contact Info Endpoint](../graphql-contact-info-endpoint.md) | `voyagerIdentityDashProfileContactInfo` | Contact details | ✅ Working |

### ⚠️ Reference Only

| Document | Endpoint | Purpose | Status |
|----------|----------|---------|--------|
| [Professional Info Variations](./graphql-professional-info-endpoint.md) | `voyagerIdentityDashProfiles` (3 variations) | Analysis of different queryIds | 📚 Reference |
| [Profile Cards Endpoint](./graphql-profile-cards-endpoint.md) | `voyagerIdentityDashProfileCards` | Metadata only (deferred cards) | ⚠️ Metadata Only |
| [Deferred Loading Issue](./DEFERRED-LOADING-ISSUE.md) | N/A | Explains empty `included` arrays | 📚 Reference |

---

## 🔄 Migration Guide: Legacy → New Endpoints

### Work Experience

**Before (DEPRECATED):**
```python
# Legacy endpoint - NO LONGER WORKS
profile = api.get_profile(public_id="johndoe")
experience = profile.get('experience', [])

# Returns:
{
  "title": "Software Engineer",
  "companyName": "Google",
  "locationName": "Seattle, WA",
  "timePeriod": {
    "startDate": {"year": 2020, "month": 1}
  }
}
```

**After (CURRENT):**
```python
# New endpoint - WORKING
experience_data = api.get_profile_experience(profile_urn)
parsed = parse_experience_response(experience_data)

# Returns:
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

### Education

**Before (DEPRECATED):**
```python
profile = api.get_profile(public_id="johndoe")
education = profile.get('education', [])

# Returns:
{
  "schoolName": "MIT",
  "degreeName": "Bachelor of Science",
  "fieldOfStudy": "Computer Science",
  "timePeriod": {
    "startDate": {"year": 2016},
    "endDate": {"year": 2020}
  }
}
```

**After (CURRENT):**
```python
education_data = api.get_profile_education(profile_urn)
parsed = parse_education_response(education_data)

# Returns:
{
  "school": "MIT",
  "degree": "Bachelor of Science",
  "field_of_study": "Computer Science",
  "start_year": 2016,
  "end_year": 2020,
  "description": "Graduated Summa Cum Laude..."
}
```

---

## 🎯 Target Data Format

### Work Experience Output

```json
{
  "work_experience": [
    {
      "title": "Senior Software Engineer",
      "company": "Google",
      "company_id": "1441",
      "company_url": "https://www.linkedin.com/company/1441/",
      "company_logo": "https://media.licdn.com/dms/image/.../200_200/...",
      "start_date": "2020-01-01",
      "end_date": null,
      "is_current": true,
      "location": null,
      "description": "Leading development of cloud infrastructure...",
      "skills": [
        "Python",
        "Kubernetes",
        "AWS",
        "Microservices"
      ]
    }
  ]
}
```

### Education Output

```json
{
  "education": [
    {
      "school": "Stanford University",
      "school_logo": "https://media.licdn.com/dms/image/.../200_200/...",
      "degree": "Master of Science - MS",
      "field_of_study": "Computer Science",
      "start_year": 2018,
      "end_year": 2020,
      "description": "Focus on Machine Learning and AI"
    }
  ]
}
```

---

## 🔍 Understanding the Endpoint Variations

### Variation 1: `voyagerIdentityDashProfiles` (vanityName)
- **QueryId:** `a1a483e719b20537a256b6853cdca711`
- **Purpose:** Full professional data (positions, companies, schools)
- **Status:** ⚠️ Returns some data but complex structure
- **Use Case:** May be useful for comprehensive profile fetch

### Variation 2: `voyagerIdentityDashProfiles` (profileUrn)
- **QueryId:** `81ad6d6680eb4b25257eab8e73b7189b`
- **Purpose:** Minimal profile lookup
- **Status:** ❌ Not useful (basic data only)
- **Use Case:** None - use other endpoints

### Variation 3: `voyagerIdentityDashProfiles` (metadata)
- **QueryId:** `2ca312bdbe80fac72fd663a3e06a83e7`
- **Purpose:** Profile structure/metadata (ProfileCard URNs)
- **Status:** ⚠️ Metadata only (empty `included` array)
- **Use Case:** Discover which sections a profile has

### ✅ Recommended: `voyagerIdentityDashProfileComponents`
- **QueryId:** `c5d4db426a0f8247b8ab7bc1d660775a`
- **Purpose:** Detailed section data (experience, education, etc.)
- **Status:** ✅ **WORKING - USE THIS**
- **Use Case:** Get full work experience and education data

---

## 🛠️ Implementation Checklist

### Phase 1: Core Experience Endpoint ✅
- [x] Document endpoint structure
- [x] Document response format
- [x] Document data extraction map
- [ ] Implement `get_profile_experience()` method
- [ ] Implement date parsing logic
- [ ] Implement experience parser
- [ ] Create FastAPI endpoint

### Phase 2: Education Endpoint
- [ ] Test education sectionType
- [ ] Document education response structure
- [ ] Implement `get_profile_education()` method
- [ ] Implement education parser
- [ ] Create FastAPI endpoint

### Phase 3: Additional Sections
- [ ] Test certifications sectionType
- [ ] Test projects sectionType
- [ ] Test volunteering sectionType
- [ ] Document findings
- [ ] Implement methods as needed

### Phase 4: Data Enhancement
- [ ] Implement company name extraction
- [ ] Implement location data (if available)
- [ ] Implement employment type detection
- [ ] Add caching layer
- [ ] Add error handling

---

## 📊 Data Comparison Matrix

| Field | Legacy Endpoint | New Endpoint | Notes |
|-------|----------------|--------------|-------|
| **Job Title** | ✅ `title` | ✅ `titleV2.text.text` | Same data |
| **Company Name** | ✅ `companyName` | ⚠️ Complex | Need to extract |
| **Start Date** | ✅ `timePeriod.startDate` (structured) | ⚠️ Text string | Need parsing |
| **End Date** | ✅ `timePeriod.endDate` (structured) | ⚠️ Text string | Need parsing |
| **Location** | ✅ `locationName` | ❌ Not visible | Missing |
| **Description** | ❌ Not available | ✅ Full text | **NEW!** |
| **Skills** | ❌ Not available | ✅ Per position | **NEW!** |
| **Company Logo** | ❌ Not available | ✅ Multiple sizes | **NEW!** |
| **Company URL** | ❌ Not available | ✅ Direct link | **NEW!** |

**Summary:**
- ✅ **Gained:** Descriptions, skills, company logos, company URLs
- ⚠️ **Changed:** Date format (structured → text)
- ❌ **Lost:** Location data, structured dates

---

## 🚨 Common Issues & Solutions

### Issue 1: Empty `included` Array

**Problem:** Response has empty `included` array

**Cause:** Using wrong queryId (Variation 3 - metadata endpoint)

**Solution:** Use `voyagerIdentityDashProfileComponents` with queryId `c5d4db426a0f8247b8ab7bc1d660775a`

### Issue 2: Can't Extract Company Name

**Problem:** Company name not in experience component

**Cause:** Company data is in separate entity or not included

**Solutions:**
1. Look for `subtitle` or `subtitleV2` in entityComponent
2. Extract company ID from URL and lookup in `included` array
3. Make separate company API call
4. Parse from company URL (not reliable)

### Issue 3: Date Parsing Fails

**Problem:** Can't parse date strings like "2017 - 2018 · 1 yr"

**Cause:** Multiple date formats in responses

**Solution:** Implement robust parser handling:
- "2017 - 2018 · 1 yr"
- "Jun 2025 - Present"
- "2021 - 2023 · 2 yrs 3 mos"
- "2020 - Present"

### Issue 4: Missing Location Data

**Problem:** No location field in response

**Cause:** Not included in this endpoint

**Solutions:**
1. Accept limitation (location not critical)
2. Try Variation 1 endpoint (may have location)
3. Make separate profile call for location

---

## 📝 Code Examples

### Fetch and Parse Experience

```python
from linkedin_api import Linkedin

api = Linkedin('username', 'password')

# Get raw data
profile_urn = "ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA"
raw_data = api.get_profile_experience(profile_urn)

# Parse into clean format
experiences = parse_experience_response(raw_data)

# Use the data
for exp in experiences:
    print(f"Title: {exp['title']}")
    print(f"Company: {exp['company']}")
    print(f"Dates: {exp['start_date']} to {exp['end_date']}")
    print(f"Skills: {', '.join(exp['skills'])}")
    print(f"Description: {exp['description'][:100]}...")
    print()
```

### FastAPI Endpoint

```python
@router.get("/profile/{profileUrn}/experience")
def getProfileExperience(profileUrn: str, authInfo = authDep):
    """Get work experience for a LinkedIn profile."""
    try:
        api = CreateLinkedinApi(authInfo).api
        raw_data = api.get_profile_experience(profileUrn)
        parsed_data = parse_experience_response(raw_data)
        return {"work_experience": parsed_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🎓 Key Learnings

### What We Discovered

1. **Multiple Endpoint Variations:** Same base URL, different queryIds, different purposes
2. **Deferred Loading Pattern:** Some endpoints return URN references, not data
3. **Component-Based Structure:** New endpoints use nested component architecture
4. **Section-Based Queries:** Can query specific sections (experience, education, etc.)
5. **Company Data Separation:** Company info in separate entities in `included` array

### Best Practices

1. **Use Section-Specific Endpoints:** `voyagerIdentityDashProfileComponents` with `sectionType`
2. **Parse Dates Carefully:** Handle multiple text formats
3. **Extract Company Data:** Look in `included` array for company entities
4. **Handle Missing Data:** Not all fields from legacy endpoint are available
5. **Cache Responses:** Reduce API calls by caching parsed data

### Patterns to Follow

1. **Two-Step Process:** Fetch raw data → Parse into clean format
2. **Recursive Parsing:** Navigate nested component structures
3. **URN Resolution:** Match URN references to entities in `included` array
4. **Fallback Logic:** Handle missing or optional fields gracefully
5. **Type Checking:** Verify `$type` fields to identify entity types

---

## 📚 Additional Resources

### Internal Documentation
- [Skills Endpoint](../graphql-skills-endpoint.md)
- [Contact Info Endpoint](../graphql-contact-info-endpoint.md)
- [Quick Reference](./QUICK-REFERENCE.md) (if exists)

### External Resources
- LinkedIn API (unofficial) - Community knowledge
- Browser DevTools - For discovering new endpoints
- GraphQL documentation - Understanding query structure

---

## 🔄 Update History

| Date | Change | Author |
|------|--------|--------|
| 2025-10-23 | Initial documentation of ProfileComponents endpoint | System |
| 2025-10-23 | Added migration guide and data comparison | System |
| 2025-10-23 | Created README index | System |

---

**Last Updated:** 2025-10-23  
**Status:** 📚 Active Documentation  
**Maintainer:** Development Team
