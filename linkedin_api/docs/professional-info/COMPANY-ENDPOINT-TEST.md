# Company Endpoint Testing Guide

## Purpose

Testing the `get_company` endpoint to determine if we can extract missing company names from work experience data.

---

## Background

### Current Situation

The `get_profile_experience()` endpoint returns work experience data with:
- ✅ Job titles
- ✅ Company IDs (extracted from URLs)
- ✅ Company URLs
- ⚠️ Company names (resolved from `included` array when available)
- ✅ Company logos (when available in `included` array)

**Issue:** Some work experience entries may have company IDs but missing company names if the company data isn't in the `included` array.

### Hypothesis

The `get_company(public_id)` endpoint might allow us to:
1. Fetch company details using the company ID or public identifier
2. Extract the company name directly
3. Fill in missing company names in work experience data

---

## Testing Steps

### Step 1: Get Work Experience Data

```bash
GET /profile/get-experience/{profileUrn}
```

**Look for entries with:**
- `company_id` present
- `company` is `null` or missing

**Example Response:**
```json
{
    "work_experience": [
        {
            "title": "Software Engineer",
            "company": null,  // ⚠️ Missing
            "company_id": "143650",  // ✅ Have this
            "company_url": "https://www.linkedin.com/company/143650/",
            "company_logo": null,
            "start_date": "2020-01-01",
            "end_date": null,
            "is_current": true
        }
    ]
}
```

### Step 2: Test Company Endpoint with ID

Try fetching company data using the company ID:

```bash
GET /profile/get-company/143650
```

**Expected:** Company data with name, description, etc.

### Step 3: Test Company Endpoint with Public ID

If the numeric ID doesn't work, try with a public identifier (if available):

```bash
GET /profile/get-company/google
GET /profile/get-company/microsoft
```

### Step 4: Analyze Response Structure

Look at the response to identify:
1. Where the company name is located
2. What other useful data is available
3. If the endpoint works with numeric IDs or only public identifiers

---

## Expected Company Response Structure

Based on the `get_company()` method, the response should follow the `WebFullCompanyMain-12` decoration:

```json
{
    "name": "Company Name",
    "description": "Company description...",
    "industry": "Software Development",
    "companyPageUrl": "https://www.linkedin.com/company/...",
    "employeeCount": 10000,
    "specialties": ["Cloud", "AI", "ML"],
    "logo": {
        "image": {
            "attributes": [
                {
                    "detailData": {
                        "profilePictureDisplayImage": {
                            "artifacts": [...]
                        }
                    }
                }
            ]
        }
    }
}
```

---

## Key Questions to Answer

### 1. Does the endpoint work with numeric company IDs?

**Test:**
```bash
GET /profile/get-company/143650
```

**Result:** ✅ Works / ❌ Doesn't work / ⚠️ Requires public identifier

---

### 2. Can we extract company names reliably?

**Look for:**
- `name` field in response
- Alternative name fields
- Consistency across different companies

---

### 3. Is there a way to convert company ID to public identifier?

**Check if response includes:**
- `universalName` (public identifier)
- `vanityName`
- Any field that maps numeric ID to public string

---

### 4. What additional data can we extract?

**Useful fields to look for:**
- Company size/employee count
- Industry
- Founded year
- Headquarters location
- Company type (public, private, nonprofit, etc.)

---

## Implementation Options

### Option A: Direct Company Lookup (If numeric IDs work)

```python
# In experience_parser.py
def _find_company_data_with_fallback(company_id, included, api):
    """
    Find company data in included array, with fallback to API call.
    """
    # Try included array first
    company_name, company_logo = _find_company_data(company_id, included)
    
    if not company_name and company_id:
        # Fallback: fetch from company endpoint
        try:
            company_data = api.get_company(public_id=company_id)
            company_name = company_data.get('name')
            # Extract logo if available
        except:
            pass
    
    return company_name, company_logo
```

**Pros:**
- Simple implementation
- Fills in missing data automatically

**Cons:**
- Requires passing `api` instance to parser
- Additional API calls (rate limiting concern)
- Slower parsing

---

### Option B: Two-Step Process (Recommended)

```python
# Step 1: Parse experience with what's available
experience_data = api.get_profile_experience(profile_urn)
parsed = parse_experience_response(experience_data)

# Step 2: Fill in missing company names
for exp in parsed['work_experience']:
    if not exp['company'] and exp['company_id']:
        try:
            company = api.get_company(public_id=exp['company_id'])
            exp['company'] = company.get('name')
            # Optionally add more company data
            exp['company_industry'] = company.get('industry')
            exp['company_size'] = company.get('employeeCount')
        except:
            pass
```

**Pros:**
- Parser stays pure (no API calls)
- User controls when to make additional API calls
- Can batch/cache company lookups

**Cons:**
- Requires additional code in application layer
- More complex for end users

---

### Option C: Separate Endpoint for Enhanced Experience

```python
@router.get("/get-experience-enhanced/{profileUrn}")
def getExperienceEnhanced(profileUrn: str, authInfo = authDep):
    """
    Get work experience with enhanced company data.
    
    This endpoint automatically fills in missing company names
    by making additional API calls to the company endpoint.
    """
    api = CreateLinkedinApi(authInfo).api
    
    # Get experience data
    raw_data = api.get_profile_experience(profileUrn)
    parsed_data = parse_experience_response(raw_data)
    
    # Enhance with company data
    for exp in parsed_data:
        if not exp['company'] and exp['company_id']:
            try:
                company = api.get_company(public_id=exp['company_id'])
                exp['company'] = company.get('name')
                exp['company_description'] = company.get('description')
                exp['company_industry'] = company.get('industry')
                exp['company_size'] = company.get('employeeCount')
            except Exception as e:
                print(f"Failed to fetch company {exp['company_id']}: {e}")
    
    return {"work_experience": parsed_data}
```

**Pros:**
- Clean separation of concerns
- Users can choose basic or enhanced endpoint
- Easy to add caching later

**Cons:**
- Duplicate endpoint
- Potentially many API calls

---

## Testing Checklist

- [ ] Test with numeric company ID (e.g., `143650`)
- [ ] Test with public identifier (e.g., `google`)
- [ ] Verify company name is in response
- [ ] Check if response includes logo data
- [ ] Test with multiple companies to ensure consistency
- [ ] Document response structure
- [ ] Measure response time (for rate limiting considerations)
- [ ] Test error handling (invalid company ID)
- [ ] Check if authentication is required
- [ ] Verify the endpoint works with the current API session

---

## Next Steps

1. **Test the endpoint** with various company IDs
2. **Document findings** in this file
3. **Decide on implementation approach** (A, B, or C)
4. **Update parsers/endpoints** based on findings
5. **Update documentation** with new capabilities

---

## Test Results

### Test 1: Numeric Company ID

**Request:**
```bash
GET /profile/get-company/143650
```

**Response:**
```json
// Paste response here
```

**Result:** ✅ / ❌ / ⚠️

**Notes:**

---

### Test 2: Public Identifier

**Request:**
```bash
GET /profile/get-company/google
```

**Response:**
```json
// Paste response here
```

**Result:** ✅ / ❌ / ⚠️

**Notes:**

---

### Test 3: Company from Experience Data

**Company ID from experience:** 

**Request:**
```bash
GET /profile/get-company/{company_id}
```

**Response:**
```json
// Paste response here
```

**Result:** ✅ / ❌ / ⚠️

**Notes:**

---

## Findings Summary

**Date:** 2025-10-23

**Tested By:**

**Key Findings:**
1. 
2. 
3. 

**Recommended Approach:**

**Implementation Notes:**

---

## Related Files

- **Endpoint:** `/routes/profile.py` - `getCompany()` function
- **LinkedIn API:** `/linkedin_api/linkedin.py` - `get_company()` method
- **Parser:** `/parsers/experience_parser.py` - Company data extraction
- **Documentation:** `/docs/DATA-ARCHITECTURE.md` - Overall architecture

---

**Status:** 🧪 Testing Phase  
**Last Updated:** 2025-10-23
