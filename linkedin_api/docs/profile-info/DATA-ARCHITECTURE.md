# LinkedIn API Data Architecture

## Overview

LinkedIn profile data is split across multiple GraphQL endpoints. This document explains which endpoint provides which data and how to combine them for a complete profile.

---

## 🎯 Endpoint Summary

| Endpoint | Purpose | Key Data Returned |
|----------|---------|-------------------|
| `get_profile_graphql()` | Basic profile info | Name, headline, summary, location, pictures, industry |
| `get_profile_experience()` | Work history | Job titles, companies, dates, descriptions, skills per job |
| `get_profile_education()` | Education history | Schools, degrees, fields of study, dates |
| `get_profile_skills_graphql()` | Skills | Skills with endorsement counts |
| `get_profile_contact_info()` | Contact details | Email, phone, websites, Twitter, birthday |

---

## 📊 Complete Profile Data Flow

### 1. Basic Profile Information
**Endpoint:** `get_profile_graphql(public_id=None, urn_id=None)`

**GraphQL URL:** `/identity/dash/profiles/{profile_urn}?decorationId=com.linkedin.voyager.dash.deco.identity.profile.FullProfile-76`

**Returns:**
```json
{
    "first_name": "Glen",
    "last_name": "Turner",
    "headline": "Software Engineer • Building smart technology...",
    "summary": "Hey I'm Glen 👋🏻 I am on a mission...",
    "public_identifier": "glen-tech",
    "profile_urn": "urn:li:fsd_profile:ACoAAAS7RzQB5MFgx7URQOOa7dShFKQhfdIWxms",
    "member_urn": "urn:li:member:79382324",
    "tracking_id": "...",
    "premium": true,
    "show_premium_badge": true,
    "location": {
        "country_code": "us",
        "postal_code": "32801"
    },
    "geo_location": {
        "geo_urn": "urn:li:fsd_geo:105142029",
        "postal_code": "32801",
        "name": "Orlando, Florida, United States",
        "name_without_country": "Orlando, Florida"
    },
    "profile_picture": {
        "root_url": "https://media.licdn.com/...",
        "images": {
            "100x100": "https://...",
            "200x200": "https://...",
            "395x395": "https://..."
        }
    },
    "background_picture": {
        "root_url": "https://media.licdn.com/...",
        "images": {
            "800x800": "https://...",
            "1400x1400": "https://..."
        }
    },
    "industry_urn": "urn:li:fsd_industry:43",
    "industry_name": "Financial Services"
}
```

**⚠️ Important Notes:**
- This endpoint does NOT include complete work experience or education
- It only provides basic profile metadata
- Use dedicated endpoints for experience and education

---

### 2. Work Experience (Complete)
**Endpoint:** `get_profile_experience(profile_urn, locale="en_US")`

**GraphQL URL:** `/graphql?variables=(profileUrn:{urn},sectionType:experience,locale:{locale})&queryId=voyagerIdentityDashProfileComponents.c5d4db426a0f8247b8ab7bc1d660775a`

**Returns (Parsed):**
```json
{
    "work_experience": [
        {
            "title": "SOC Manager",
            "company": "GB&P",
            "company_id": "143650",
            "company_url": "https://www.linkedin.com/company/143650/",
            "company_logo": "https://media.licdn.com/.../200_200/...",
            "start_date": "2017-01-01",
            "end_date": "2018-12-31",
            "is_current": false,
            "location": null,
            "description": "Promoted from Senior Security Analyst...",
            "skills": ["Security Operations", "SIEM", "Technical Leadership"]
        }
    ]
}
```

**Key Features:**
- ✅ Complete job history with ALL positions
- ✅ Company names and logos
- ✅ Full job descriptions
- ✅ Skills per position
- ✅ Current position detection
- ✅ Structured date parsing

---

### 3. Education (Complete)
**Endpoint:** `get_profile_education(profile_urn, locale="en_US")`

**GraphQL URL:** `/graphql?variables=(profileUrn:{urn},sectionType:education,locale:{locale})&queryId=voyagerIdentityDashProfileComponents.c5d4db426a0f8247b8ab7bc1d660775a`

**Returns (Parsed):**
```json
{
    "education": [
        {
            "school": "University of Central Florida",
            "school_id": "18190",
            "school_url": "https://www.linkedin.com/school/18190/",
            "school_logo": "https://media.licdn.com/.../200_200/...",
            "degree": "Bachelor of Science - BS",
            "field_of_study": "Computer Science",
            "start_year": 2020,
            "end_year": 2023,
            "description": "Minor in Secure Networks, Graduated Summa Cum Laude"
        }
    ]
}
```

**Key Features:**
- ✅ Complete education history
- ✅ School names and logos
- ✅ Degrees and fields of study
- ✅ Year ranges
- ✅ Descriptions/activities

---

## 🔧 Why Multiple Endpoints?

### LinkedIn's Data Architecture

LinkedIn uses a **component-based architecture** where different sections of a profile are loaded separately:

1. **Profile Metadata Endpoint** (`FullProfile-76`)
   - Loads first for quick page render
   - Contains basic info, pictures, location
   - Does NOT contain full experience/education

2. **ProfileComponents Endpoint** (with `sectionType`)
   - Loads dynamically as user scrolls
   - Each section type is a separate request
   - Contains complete, detailed data for that section

### Why Experience/Education Are Separate

```
User visits profile page
    ↓
1. Load basic info (name, headline, picture) ← get_profile_graphql()
    ↓
2. User scrolls to experience section
    ↓
3. Load experience data ← get_profile_experience()
    ↓
4. User scrolls to education section
    ↓
5. Load education data ← get_profile_education()
```

This is called **"deferred loading"** - it improves page load performance by not loading everything at once.

---

## 🎨 Building a Complete Profile

### Recommended Approach

```python
from linkedin_api import Linkedin

api = Linkedin('username', 'password')

# Step 1: Get basic profile info
profile = api.get_profile_graphql(public_id="glen-tech")

# Step 2: Get complete work experience
experience_data = api.get_profile_experience(profile['profile_urn'])

# Step 3: Get complete education
education_data = api.get_profile_education(profile['profile_urn'])

# Step 4: Combine into complete profile
complete_profile = {
    **profile,
    "work_experience": experience_data.get("work_experience", []),
    "education": education_data.get("education", [])
}
```

### FastAPI Endpoint Example

```python
@router.get("/profile/{identifier}/complete")
def getCompleteProfile(identifier: str, authInfo = authDep):
    """Get complete profile with all data."""
    api = CreateLinkedinApi(authInfo).api
    
    # Get basic profile
    profile = api.get_profile_graphql(public_id=identifier)
    profile_urn = profile.get("profile_urn")
    
    # Get experience and education
    experience = api.get_profile_experience(profile_urn)
    education = api.get_profile_education(profile_urn)
    
    return {
        **profile,
        "work_experience": experience.get("work_experience", []),
        "education": education.get("education", [])
    }
```

---

## 📝 Data Completeness Matrix

| Data Field | get_profile_graphql | get_profile_experience | get_profile_education |
|------------|---------------------|------------------------|----------------------|
| First Name | ✅ | ❌ | ❌ |
| Last Name | ✅ | ❌ | ❌ |
| Headline | ✅ | ❌ | ❌ |
| Summary | ✅ | ❌ | ❌ |
| Location | ✅ | ❌ | ❌ |
| Profile Picture | ✅ | ❌ | ❌ |
| Background Picture | ✅ | ❌ | ❌ |
| Industry Name | ✅ | ❌ | ❌ |
| Job Titles | ❌ | ✅ | ❌ |
| Company Names | ❌ | ✅ | ❌ |
| Company Logos | ❌ | ✅ | ❌ |
| Job Descriptions | ❌ | ✅ | ❌ |
| Skills per Job | ❌ | ✅ | ❌ |
| Current Position | ❌ | ✅ | ❌ |
| School Names | ❌ | ❌ | ✅ |
| School Logos | ❌ | ❌ | ✅ |
| Degrees | ❌ | ❌ | ✅ |
| Fields of Study | ❌ | ❌ | ✅ |
| Education Years | ❌ | ❌ | ✅ |

---

## 🚀 Current Implementation Status

### ✅ Completed

- [x] Basic profile info endpoint (`get_profile_graphql`)
- [x] Work experience endpoint (`get_profile_experience`)
- [x] Education endpoint (`get_profile_education`)
- [x] Experience parser (extracts company names, dates, skills)
- [x] Education parser (extracts schools, degrees, years)
- [x] FastAPI endpoints with automatic parsing
- [x] Industry name extraction from included array
- [x] Company logo resolution
- [x] School logo resolution
- [x] Date parsing (handles multiple formats)
- [x] Current position detection

### 🔄 In Progress

- [ ] Complete profile endpoint (combines all data)
- [ ] Skills endpoint integration
- [ ] Contact info endpoint integration

### 📋 Planned

- [ ] Certifications endpoint
- [ ] Projects endpoint
- [ ] Volunteering endpoint
- [ ] Publications endpoint
- [ ] Recommendations endpoint

---

## 🔍 Raw Response Files

For reference, raw API responses are stored in:

- **Profile Info:** `/docs/profile-info/profile-info-raw-response.json`
- **Experience:** `/docs/professional-info/education-raw-reponse.json` (note: filename says education but contains experience data)
- **Education:** Same file contains education data

---

## 💡 Best Practices

### 1. Always Use Parsed Endpoints

```python
# ✅ Good - Returns clean, parsed data
experience = api.get_profile_experience(profile_urn)

# ❌ Avoid - Returns raw GraphQL (unless debugging)
raw_experience = api.get_profile_experience(profile_urn, raw=True)
```

### 2. Handle Missing Data Gracefully

```python
profile = api.get_profile_graphql(public_id="someone")

# Some fields may be None
company_name = profile.get("industry_name", "Unknown Industry")
location = profile.get("location", {}).get("country_code", "Unknown")
```

### 3. Cache Profile URNs

```python
# Get profile URN once
profile = api.get_profile_graphql(public_id="glen-tech")
profile_urn = profile["profile_urn"]

# Reuse for other endpoints
experience = api.get_profile_experience(profile_urn)
education = api.get_profile_education(profile_urn)
skills = api.get_profile_skills_graphql(profile_urn)
```

### 4. Use Type Hints

```python
from typing import Dict, List, Optional

def get_complete_profile(api: Linkedin, identifier: str) -> Dict:
    """Get complete profile with type safety."""
    profile: Dict = api.get_profile_graphql(public_id=identifier)
    experience: Dict = api.get_profile_experience(profile["profile_urn"])
    
    return {**profile, **experience}
```

---

## 🐛 Common Issues

### Issue 1: Missing Company Names

**Problem:** Company names are `None` in experience data

**Cause:** Company data is in the `included` array and must be resolved

**Solution:** Use the parsed endpoint - it automatically resolves company names from the included array

```python
# ✅ This works - parser resolves company names
experience = api.get_profile_experience(profile_urn)
```

### Issue 2: Incomplete Work History

**Problem:** Recent jobs are missing

**Cause:** Using `get_profile_graphql()` instead of `get_profile_experience()`

**Solution:** Always use `get_profile_experience()` for complete work history

```python
# ❌ Wrong - Only returns partial/no experience
profile = api.get_profile_graphql(public_id="someone")

# ✅ Correct - Returns ALL positions
experience = api.get_profile_experience(profile_urn)
```

### Issue 3: Date Parsing Errors

**Problem:** Dates are strings like "2017 - 2018 · 1 yr"

**Cause:** LinkedIn returns human-readable date strings

**Solution:** Use the parsed endpoint - it converts to ISO format

```python
# Parser converts:
# "Jun 2025 - Present" → start_date: "2025-06-01", end_date: None, is_current: True
# "2017 - 2018 · 1 yr" → start_date: "2017-01-01", end_date: "2018-01-01"
```

---

## 📚 Related Documentation

- [Profile Components Experience Endpoint](./professional-info/profile-components-experience-endpoint.md)
- [GraphQL Professional Info Endpoint](./professional-info/graphql-professional-info-endpoint.md)
- [Quick Reference Guide](./professional-info/QUICK-REFERENCE.md)
- [Deferred Loading Issue](./professional-info/DEFERRED-LOADING-ISSUE.md)

---

## 🎯 Summary

**Key Takeaways:**

1. ✅ **Use `get_profile_graphql()` for basic info** (name, headline, pictures, location, industry)
2. ✅ **Use `get_profile_experience()` for complete work history** (all jobs with company names, dates, descriptions)
3. ✅ **Use `get_profile_education()` for complete education** (all schools with degrees, dates)
4. ✅ **Parsed endpoints return clean data** - no need to manually parse GraphQL responses
5. ✅ **Combine endpoints for complete profile** - each endpoint serves a specific purpose

**Status:** ✅ **Core functionality complete and production-ready**

**Last Updated:** 2025-10-23
