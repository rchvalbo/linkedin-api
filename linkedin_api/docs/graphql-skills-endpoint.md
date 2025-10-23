# LinkedIn GraphQL Skills Endpoint Documentation

## Overview
This document details the implementation and findings for the `get_profile_skills_graphql()` method, which retrieves skills data from LinkedIn profiles using their GraphQL API.

## Background
The legacy REST endpoint `/identity/profiles/{urn_id}/skills` was deprecated by LinkedIn and returns a `410 Gone` status. The GraphQL endpoint is the current method for retrieving profile skills data.

## Implementation Details

### Endpoint
```
GET https://www.linkedin.com/voyager/api/graphql
```

### Query Parameters
- **`variables`**: GraphQL query variables in the format:
  ```
  (profileUrn:urn%3Ali%3Afsd_profile%3A{URN_ID},sectionType:skills,locale:en_US)
  ```
  **Important**: The colons in the URN must be URL-encoded as `%3A`, but parentheses and commas should remain unencoded.

- **`queryId`**: The GraphQL query identifier
  ```
  voyagerIdentityDashProfileComponents.c5d4db426a0f8247b8ab7bc1d660775a
  ```
  **Note**: This queryId may change over time as LinkedIn updates their API. It can be found by inspecting network requests in a browser when viewing a profile's skills section.

### Required Headers

| Header | Value | Purpose |
|--------|-------|---------|
| `accept` | `application/vnd.linkedin.normalized+json+2.1` | Specifies the response format LinkedIn should return |
| `x-restli-protocol-version` | `2.0.0` | LinkedIn's REST protocol version |
| `referer` | `https://www.linkedin.com/in/{urn_id}/details/skills/` | Tells LinkedIn which page the request originated from |
| `x-li-page-instance` | `urn:li:page:d_flagship3_profile_view_base_skills_details;{random_id}` | Page context tracking identifier (random base64 string) |
| `x-li-pem-metadata` | `Voyager - Profile=view-skills-details` | Page event metadata |
| `x-li-track` | JSON object with client metadata | Client tracking information (see below) |

#### x-li-track Format
```json
{
  "clientVersion": "1.13.39992",
  "mpVersion": "1.13.39992",
  "osName": "web",
  "timezoneOffset": -4,
  "timezone": "America/New_York",
  "deviceFormFactor": "DESKTOP",
  "mpName": "voyager-web",
  "displayDensity": 2,
  "displayWidth": 6400,
  "displayHeight": 2666
}
```

### Example Request URL
```
https://www.linkedin.com/voyager/api/graphql?variables=(profileUrn:urn%3Ali%3Afsd_profile%3AACoAAAvWqK4BsmmRWSy7C7HfMacLyS59-cBZWBU,sectionType:skills,locale:en_US)&queryId=voyagerIdentityDashProfileComponents.c5d4db426a0f8247b8ab7bc1d660775a
```

## Key Implementation Findings

### 1. URL Construction Method
**Critical**: The URL must be constructed manually as a string, NOT using a `params` dictionary.

❌ **Wrong approach:**
```python
params = {"variables": variables, "queryId": query_id}
res = self._fetch("/graphql", params=params, headers=headers)
```

✅ **Correct approach:**
```python
query_string = f"variables={encoded_variables}&queryId={query_id}"
full_url = f"/graphql?{query_string}"
res = self._fetch(full_url, headers=headers)
```

This pattern matches the working `search_typeahead()` method in the codebase.

### 2. URL Encoding
The URN colons must be manually encoded as `%3A`:

```python
encoded_urn = profile_urn.replace(":", "%3A")
encoded_variables = f"(profileUrn:{encoded_urn},sectionType:skills,locale:{locale})"
```

### 3. Page Instance ID Generation
LinkedIn requires a unique page instance identifier for each request:

```python
import base64
import random

random_bytes = bytes([random.randint(0, 255) for _ in range(16)])
page_instance_id = base64.b64encode(random_bytes).decode('utf-8').rstrip('=')
page_instance = f"urn:li:page:d_flagship3_profile_view_base_skills_details;{page_instance_id}"
```

### 4. Profile Page Visit Not Required
Initial testing suggested visiting the profile page first might be necessary, but this proved unnecessary. The GraphQL endpoint works without a prior page visit.

## Troubleshooting History

### Error Progression
1. **500 Internal Server Error**: Incorrect queryId (`c6d4db...` instead of `c5d4db...`)
2. **400 Bad Request (37 bytes)**: Missing required headers (`x-li-page-instance`, etc.)
3. **400 Bad Request (14 bytes)**: Incorrect URL encoding (colons not encoded)
4. **200 Success**: All requirements met

### Common Pitfalls
- Using the wrong queryId (must match current LinkedIn implementation)
- Using `params` dict instead of manual URL construction
- Not URL-encoding the URN colons
- Missing any of the required headers
- Incorrect header values or formats

## Response Format

### Raw GraphQL Response
The raw response from LinkedIn is a complex nested structure with skills data in the `included` array under `PagedListComponent` items.

### Parsed Response
The `get_profile_skills_graphql()` method parses the raw response and returns a simplified list of skill objects:

```python
[
    {
        "name": "Salesforce.com",
        "numEndorsements": 1
    },
    {
        "name": "Software as a Service (SaaS)",
        "numEndorsements": 0
    },
    {
        "name": "Public Relations",
        "numEndorsements": 7
    }
]
```

**Note:** The GraphQL endpoint does not provide `standardizedSkillUrn` or `entityUrn` fields that were available in the legacy REST endpoint. If you need these URN identifiers for standardized skills, you may need to use an alternative approach or cross-reference with LinkedIn's skill taxonomy.

## Maintenance Notes

### QueryId Updates
The queryId (`voyagerIdentityDashProfileComponents.c5d4db426a0f8247b8ab7bc1d660775a`) may change when LinkedIn updates their frontend. To find the current queryId:

1. Open LinkedIn in a browser with DevTools
2. Navigate to a profile's skills section (`/in/{profile}/details/skills/`)
3. Filter network requests for `graphql`
4. Look for the `queryId` parameter in the request URL
5. Update the hardcoded value in `get_profile_skills_graphql()`

### Related Methods
- `search_typeahead()`: Uses similar GraphQL endpoint pattern
- `get_profile_skills()`: Legacy REST endpoint (deprecated, returns 410)

## Implementation Date
October 22, 2025

## References
- LinkedIn Voyager API (internal)
- Browser network inspection (Chrome DevTools)
- Existing `search_typeahead()` implementation pattern
