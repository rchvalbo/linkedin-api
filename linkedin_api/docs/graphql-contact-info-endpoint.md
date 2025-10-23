# LinkedIn GraphQL Contact Info Endpoint Documentation

## Overview
This document details the implementation of the `get_profile_contact_info_graphql()` method, which retrieves contact information from LinkedIn profiles using their GraphQL API.

## Background
The legacy REST endpoint `/identity/profiles/{urn_id}/profileContactInfo` may be deprecated or rate-limited. The GraphQL endpoint provides an alternative method for retrieving profile contact information.

## Implementation Details

### Endpoint
```
GET https://www.linkedin.com/voyager/api/graphql
```

### Query Parameters
- **`includeWebMetadata`**: Boolean flag to include web metadata (typically `true`)
- **`variables`**: GraphQL query variables in the format:
  ```
  (memberIdentity:{public_id})
  ```
  **Important**: The colons must be URL-encoded as `%3A`

- **`queryId`**: The GraphQL query identifier
  ```
  voyagerIdentityDashProfiles.c7452e58fa37646d09dae4920fc5b4b9
  ```
  **Note**: This queryId may change over time as LinkedIn updates their API.

### Required Headers

| Header | Value | Purpose |
|--------|-------|---------|
| `accept` | `application/vnd.linkedin.normalized+json+2.1` | Specifies the response format |
| `x-restli-protocol-version` | `2.0.0` | LinkedIn's REST protocol version |
| `referer` | `https://www.linkedin.com/in/{public_id}/` | Origin page reference |
| `x-li-page-instance` | `urn:li:page:d_flagship3_profile_view_base_contact_details;{random_id}` | Page context tracking |
| `x-li-track` | JSON object with client metadata | Client tracking information |

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
https://www.linkedin.com/voyager/api/graphql?includeWebMetadata=true&variables=(memberIdentity:johndinsmore1)&queryId=voyagerIdentityDashProfiles.c7452e58fa37646d09dae4920fc5b4b9
```

## Key Implementation Details

### 1. URL Construction
Must be constructed manually as a string (same pattern as skills endpoint):

```python
variables = f"(memberIdentity:{public_id})"
encoded_variables = variables.replace(":", "%3A")
query_string = f"includeWebMetadata={include_metadata}&variables={encoded_variables}&queryId={query_id}"
full_url = f"/graphql?{query_string}"
```

### 2. Page Instance ID Generation
```python
random_bytes = bytes([random.randint(0, 255) for _ in range(16)])
page_instance_id = base64.b64encode(random_bytes).decode('utf-8').rstrip('=')
page_instance = f"urn:li:page:d_flagship3_profile_view_base_contact_details;{page_instance_id}"
```

### 3. Input Parameter
Unlike the skills endpoint which uses `urn_id`, this endpoint uses `public_id` (the vanity URL slug like `johndinsmore1`).

## Response Format

### Raw GraphQL Response
The raw response contains profile data in the `included` array with type `com.linkedin.voyager.dash.identity.profile.Profile`.

### Parsed Response
The `get_profile_contact_info_graphql()` method parses the GraphQL response and returns contact information:

```python
{
    "email_address": "johnwaynedinsmore@gmail.com",
    "websites": [
        {
            "url": "http://thejohndinsmore.com",
            "category": "PERSONAL",
            "label": null
        }
    ],
    "twitter": [],
    "birthdate": {
        "month": 10,
        "day": 6,
        "$recipeTypes": ["com.linkedin.bd0312d2f752c9990aa1bbe913dfa662"],
        "$type": "com.linkedin.common.Date"
    },
    "phone_numbers": [
        {
            "number": "2085700319",
            "type": "MOBILE"
        }
    ],
    "ims": [],
    "address": "250 E Myrtle St #311\nBoise Idaho 83702"
}
```

**Note:** Not all fields may be present depending on the profile's privacy settings and what information the user has shared. The `address` field is a bonus field not available in the legacy endpoint.

## Differences from Legacy Endpoint

| Aspect | Legacy Endpoint | GraphQL Endpoint |
|--------|----------------|------------------|
| **Parameter** | Uses `urn_id` or `public_id` | Uses `public_id` only |
| **URL Pattern** | `/identity/profiles/{id}/profileContactInfo` | `/graphql?variables=...&queryId=...` |
| **Response Structure** | Flat object | Nested in `data.identityDashProfilesByMemberIdentity` |
| **Headers** | Standard REST headers | Requires GraphQL-specific headers |

## Maintenance Notes

### QueryId Updates
The queryId (`voyagerIdentityDashProfiles.c7452e58fa37646d09dae4920fc5b4b9`) may change when LinkedIn updates their frontend. To find the current queryId:

1. Open LinkedIn in a browser with DevTools
2. Navigate to a profile's contact info section
3. Filter network requests for `graphql`
4. Look for requests with `memberIdentity` in the variables
5. Extract the `queryId` parameter from the URL
6. Update the hardcoded value in `get_profile_contact_info_graphql()`

### Privacy Considerations
Contact information availability depends on:
- The profile owner's privacy settings
- Your connection level with the profile owner
- LinkedIn Premium status
- Profile completeness

## Related Methods
- `get_profile_contact_info()`: Legacy REST endpoint
- `get_profile_skills_graphql()`: Similar GraphQL pattern for skills

## Implementation Date
October 22, 2025

## Testing
Use the FastAPI route:
```
GET /profile/get-contact-info-graphql/{publicId}
```

Example:
```
GET /profile/get-contact-info-graphql/johndinsmore1
```
