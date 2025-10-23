# LinkedIn GraphQL Professional Info Endpoint

## Overview
This endpoint retrieves a LinkedIn profile's professional information including work history, education, and certifications using the GraphQL API.

**Status:** 🚧 Under Investigation

**Purpose:** Fetch comprehensive professional data (positions, education, certifications, etc.) for a given LinkedIn profile.

---

## Endpoint Variations

### Variation 1: Using vanityName (Public Identifier)

**Request Method:** `GET`

**Base URL:**
```
https://www.linkedin.com/voyager/api/graphql
```

**Query Parameters:**
- `includeWebMetadata`: `true`
- `variables`: `(vanityName:amberdevilbiss)`
- `queryId`: `voyagerIdentityDashProfiles.a1a483e719b20537a256b6853cdca711`

**Full URL Example:**
```
https://www.linkedin.com/voyager/api/graphql?includeWebMetadata=true&variables=(vanityName:amberdevilbiss)&queryId=voyagerIdentityDashProfiles.a1a483e719b20537a256b6853cdca711
```

**Request Headers (from screenshot):**
```
accept: application/vnd.linkedin.normalized+json+2.1
accept-encoding: gzip, deflate, br, zstd
accept-language: en-US,en;q=0.9
cache-control: no-cache, no-store
content-encoding: gzip
content-length: 18969
content-security-policy: default-src 'none' frame-ancestors 'none' form-action 'none'
content-type: application/vnd.linkedin.normalized+json+2.1; charset=UTF-8
csrf-token: ajax:6926685819872007-ATL
x-li-page-instance: urn:li:page:d_flagship3_profile_view_base;...
x-li-track: {"clientVersion":"1.13.40037",...}
x-restli-protocol-version: 2.0.0
```

**Key Observations:**
- Uses `vanityName` parameter (same as `public_id` or `publicIdentifier`)
- Example: `amberdevilbiss` is the vanity name from the profile URL
- QueryId: `voyagerIdentityDashProfiles.a1a483e719b20537a256b6853cdca711`

---

## Data Retrieved

### Expected Professional Information:
- ✅ **Work History** (positions, companies, dates, descriptions)
- ✅ **Education** (schools, degrees, fields of study, dates)
- ✅ **Certifications** (certification name, issuing organization, dates)
- ❓ **Volunteer Experience**
- ❓ **Publications**
- ❓ **Patents**
- ❓ **Courses**
- ❓ **Projects**
- ❓ **Honors & Awards**
- ❓ **Test Scores**
- ❓ **Languages**

---

## Additional Variations

### Variation 2: Using profileUrn (URN-based)

**Request Method:** `GET`

**Base URL:**
```
https://www.linkedin.com/voyager/api/graphql
```

**Query Parameters:**
- `includeWebMetadata`: `true`
- `variables`: `(profileUrn:urn:li:fsd_profile:ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA)`
- `queryId`: `voyagerIdentityDashProfiles.81ad6d6680eb4b25257eab8e73b7189b`

**Full URL Example:**
```
https://www.linkedin.com/voyager/api/graphql?includeWebMetadata=true&variables=(profileUrn:urn:li:fsd_profile:ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA)&queryId=voyagerIdentityDashProfiles.81ad6d6680eb4b25257eab8e73b7189b
```

**Key Observations:**
- Uses `profileUrn` parameter instead of `vanityName`
- **Different queryId**: `voyagerIdentityDashProfiles.81ad6d6680eb4b25257eab8e73b7189b` (vs Variation 1's `a1a483e719b20537a256b6853cdca711`)
- URN format: `urn:li:fsd_profile:{profileId}`
- Same headers as Variation 1

**Response Structure:**
- Main data path: `data.data.identityDashProfilesById` (different from Variation 1!)
- Returns single profile URN reference
- Minimal `included` array - only contains basic profile entity
- **Much less data than Variation 1** - appears to be a lighter endpoint

**Comparison with Variation 1:**
| Aspect | Variation 1 (vanityName) | Variation 2 (profileUrn) |
|--------|-------------------------|-------------------------|
| **Parameter** | `vanityName:amberdevilbiss` | `profileUrn:urn:li:fsd_profile:...` |
| **QueryId** | `a1a483e719b20537a256b6853cdca711` | `81ad6d6680eb4b25257eab8e73b7189b` |
| **Data Path** | `identityDashProfilesByMemberIdentity` | `identityDashProfilesById` |
| **Response Size** | Large (positions, education, companies, etc.) | Minimal (basic profile only) |
| **Use Case** | Full professional data retrieval | Basic profile lookup by URN |

### Variation 3: Profile Structure/Metadata Endpoint ⭐ **CRITICAL**

**Request Method:** `GET`

**Base URL:**
```
https://www.linkedin.com/voyager/api/graphql
```

**Query Parameters:**
- `includeWebMetadata`: `true`
- `variables`: `(vanityName:amberdevilbiss)`
- `queryId`: `voyagerIdentityDashProfiles.2ca312bdbe80fac72fd663a3e06a83e7`

**Full URL Example:**
```
https://www.linkedin.com/voyager/api/graphql?includeWebMetadata=true&variables=(vanityName:amberdevilbiss)&queryId=voyagerIdentityDashProfiles.2ca312bdbe80fac72fd663a3e06a83e7
```

**Key Observations:**
- Uses `vanityName` parameter (like Variation 1)
- **Different queryId**: `2ca312bdbe80fac72fd663a3e06a83e7`
- **THIS IS THE PROFILE STRUCTURE/METADATA ENDPOINT!**

**What This Endpoint Returns:**

This endpoint provides the **ROADMAP** to all profile data by returning **ProfileCard URNs** for every section:

```json
"*cards": [
  "urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,EXPERIENCE,en_US)",
  "urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,EDUCATION,en_US)",
  "urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,LICENSES_AND_CERTIFICATIONS,en_US)",
  "urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,SKILLS,en_US)",
  "urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,PROJECTS,en_US)",
  "urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,VOLUNTEERING_EXPERIENCE,en_US)",
  "urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,PUBLICATIONS,en_US)",
  "urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,PATENTS,en_US)",
  "urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,COURSES,en_US)",
  "urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,HONORS_AND_AWARDS,en_US)",
  "urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,TEST_SCORES,en_US)",
  "urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,LANGUAGES,en_US)",
  "urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,ORGANIZATIONS,en_US)",
  // ... and more
]
```

**Complete List of Profile Cards (23 sections):**
1. **EXPERIENCE** ⭐ - Work history
2. **EDUCATION** ⭐ - Schools and degrees
3. **LICENSES_AND_CERTIFICATIONS** ⭐ - Certifications
4. **SKILLS** - Skills (we already have this via separate endpoint)
5. **PROJECTS** - Personal/professional projects
6. **VOLUNTEERING_EXPERIENCE** - Volunteer work
7. **PUBLICATIONS** - Published works
8. **PATENTS** - Patent filings
9. **COURSES** - Completed courses
10. **HONORS_AND_AWARDS** - Awards and honors
11. **TEST_SCORES** - Test scores
12. **LANGUAGES** - Language proficiencies
13. **ORGANIZATIONS** - Professional organizations
14. **RECOMMENDATIONS** - Given/received recommendations
15. **ABOUT** - About section
16. **HIGHLIGHTS** - Profile highlights
17. **FEATURED** - Featured content
18. **SERVICES** - Services offered
19. **CONTENT_COLLECTIONS** - Content collections
20. **INTERESTS** - Interests
21. **VOLUNTEER_CAUSES** - Causes supported
22. **PROMO** - Promotional content
23. **SALES_LEAD_INSIGHTS** - Sales insights

**How to Use These URNs:**

Each ProfileCard URN can be used to fetch the **detailed data** for that section. For example:
- `EXPERIENCE` card → Fetch to get full position details (titles, descriptions, dates)
- `EDUCATION` card → Fetch to get full education details (degrees, fields of study, dates)
- `LICENSES_AND_CERTIFICATIONS` card → Fetch to get certification details

**Architecture Pattern:**
```
Step 1: Call Variation 3 (Metadata Endpoint)
   ↓
Get list of ProfileCard URNs for all sections
   ↓
Step 2: Call individual ProfileCard endpoints
   ↓
Get detailed data for EXPERIENCE, EDUCATION, CERTIFICATIONS, etc.
```

---

## Testing Individual ProfileCard Fetch

### How to Fetch a ProfileCard

Based on the URN format from Variation 3, we need to test fetching individual cards.

**ProfileCard URN Format:**
```
urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,EXPERIENCE,en_US)
                        └─────────────── Profile ID ──────────────┘  └─ Card Type ─┘ └Locale┘
```

**Potential Endpoint Patterns to Test:**

**Option 1: Direct ProfileCard Endpoint**
```
GET /voyager/api/identity/dash/profileCards/{cardUrn}
GET /voyager/api/identity/dash/profileCards/urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,EXPERIENCE,en_US)
```

**Option 2: GraphQL with ProfileCard URN**
```
GET /voyager/api/graphql?variables=(profileCardUrn:urn:li:fsd_profileCard:(...))&queryId={someQueryId}
```

**Option 3: Dash Profiles with Card Type**
```
GET /voyager/api/identity/dash/profiles/{profileUrn}/cards/{cardType}
GET /voyager/api/identity/dash/profiles/ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA/cards/EXPERIENCE
```

**Option 4: Decorated Profile Endpoint**
```
GET /voyager/api/identity/dash/profiles/{profileUrn}?decorationId=com.linkedin.voyager.dash.deco.identity.profile.{CardType}
```

### Test Cases

**Test 1: Fetch EXPERIENCE Card**
- **URN**: `urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,EXPERIENCE,en_US)`
- **Expected Data**: Full position details (titles, descriptions, dates, companies)

**Test 2: Fetch EDUCATION Card**
- **URN**: `urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,EDUCATION,en_US)`
- **Expected Data**: Full education details (degrees, fields of study, dates, schools)

**Test 3: Fetch LICENSES_AND_CERTIFICATIONS Card**
- **URN**: `urn:li:fsd_profileCard:(ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA,LICENSES_AND_CERTIFICATIONS,en_US)`
- **Expected Data**: Certification details (names, issuers, dates)

### What to Look For in Response

1. **Position/Experience Data:**
   - Job title
   - Company name
   - Employment type (full-time, part-time, contract)
   - Start date (month, year)
   - End date (month, year) or null for current
   - Location
   - Description/responsibilities

2. **Education Data:**
   - School name
   - Degree type (Bachelor's, Master's, etc.)
   - Field of study
   - Start date
   - End date
   - Grade/GPA
   - Activities and societies
   - Description

3. **Certification Data:**
   - Certification name
   - Issuing organization
   - Issue date
   - Expiration date (if applicable)
   - Credential ID
   - Credential URL

### Next: Test in Browser DevTools

**Steps to Test:**
1. Open LinkedIn profile in browser
2. Open DevTools → Network tab
3. Navigate to "Experience" section or scroll to load it
4. Look for API calls to `/voyager/api/` endpoints
5. Identify the endpoint pattern used for ProfileCard data
6. Document the request URL, headers, and response structure

---

## Implementation Considerations

### Parameter Options:
1. **vanityName** - Public identifier (e.g., "amberdevilbiss")
2. **memberIdentity** - URN-based identifier (to be confirmed)
3. **profileUrn** - Full profile URN (to be confirmed)

### Questions to Answer:
- [x] What is the complete response structure?
- [x] Which fields are included in the response?
- [ ] Can we use URN instead of vanityName?
- [ ] What are the other variations of this endpoint?
- [ ] What privacy restrictions apply?
- [ ] How does this differ from the legacy endpoint?

---

## Response Structure

### Raw Response Overview

The response follows LinkedIn's GraphQL normalized format with:

1. **Main Data Path**: `data.data.identityDashProfilesByMemberIdentity`
2. **Elements Array**: Contains URN references to profile entities
3. **Included Array**: Contains the actual entity data (profiles, companies, schools, connections, etc.)

**Key Response Fields:**
```json
{
  "data": {
    "data": {
      "identityDashProfilesByMemberIdentity": {
        "*elements": [
          "urn:li:fsd_profile:ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA"
        ],
        "$type": "com.linkedin.restli.common.CollectionResponse"
      }
    }
  },
  "included": [
    // Array of entities referenced by URNs
  ]
}
```

### Response Contains

Based on the actual response, this endpoint returns:

#### ✅ **Profile Data** (`com.linkedin.voyager.dash.identity.profile.Profile`)
- Basic info: firstName, lastName, headline, publicIdentifier
- Profile picture with multiple resolutions
- Location (countryCode, postalCode)
- Premium features and badges
- Verification status
- Creator status
- Member relationship data

#### ✅ **Education** (Referenced via `profileTopEducation`)
- URN references to education entries: `urn:li:fsd_profileEducation:(...)`
- Paging information (count, start, total)
- Example shows 2 education entries

#### ✅ **Work Experience** (`com.linkedin.voyager.dash.identity.profile.Position`)
- **Full position data IS included in the response!**
- Entity URN: `urn:li:fsd_profilePosition:(profileUrn,positionId)`
- Company name (single and multi-locale)
- Company URN reference: `"*company": "urn:li:fsd_company:78449382"`
- **Date range with start/end dates**:
  - Start: `{ month: 6, year: 2025, day: null }`
  - End: `null` (indicates current position)
- Position type: `com.linkedin.voyager.dash.identity.profile.Position`

#### ✅ **Company Data** (`com.linkedin.voyager.dash.organization.Company`)
- Company name, logo (vectorImage with multiple resolutions)
- Universal name (URL slug)
- Entity URN
- Example: "Skyhigh Security", "Colorado State University Global"

#### ✅ **School Data** (`com.linkedin.voyager.dash.organization.School`)
- School name, logo
- Entity URN
- URL

#### ✅ **Connection Data** (`com.linkedin.voyager.dash.relationships.Connection`)
- Created date
- Connected member URN
- Connection entity URN

#### ✅ **Mutual Connections/Insights** (`com.linkedin.voyager.dash.relationships.Insight`)
- Shared connections with profile pictures
- Text description (e.g., "David Barthelemy and Wayne Smith are mutual connections")
- Navigation URL to view all mutual connections

#### ✅ **Member Relationship** (`com.linkedin.voyager.dash.relationships.MemberRelationship`)
- Connection status (self, connection, noConnection)
- Invitation status

### Important Notes on Response Structure

**✅ Data Resolution Pattern - How the Endpoint Works:**

This endpoint uses LinkedIn's **normalized GraphQL response format** with URN-based references:

1. **Main Response** (`data.data.identityDashProfilesByMemberIdentity`):
   - Contains URN references in `*elements` arrays
   - Example: `"*elements": ["urn:li:fsd_profilePosition:(...,2666845637)"]`

2. **Included Array** (`included`):
   - Contains the **actual entity data** for all referenced URNs
   - You must match URNs from main response to entities in `included` array
   - All related entities (positions, education, companies, schools) are included here

**Example Resolution Flow:**
```
Profile → "*profileTopPosition" → ["urn:li:fsd_profilePosition:(...)"]
                                          ↓
Included Array → Find entity with matching URN → Full Position Data
                                          ↓
Position → "*company" → "urn:li:fsd_company:78449382"
                                          ↓
Included Array → Find company entity → Company Name, Logo, etc.
```

**What IS included (confirmed):**
- ✅ Full position/work history with dates, company names
- ✅ Company entities with logos and details
- ✅ School entities with logos and details
- ✅ Connection and relationship data
- ✅ Profile pictures and verification status

**What's NOT visible yet (need to confirm):**
- ❓ Full education details (degrees, fields of study, dates) - URNs present, need to check `included` array
- ❓ Job titles for positions - need to check if included in Position entity
- ❓ Position descriptions
- ❓ Certifications
- ❓ Volunteer experience
- ❓ Publications, patents, courses, projects
- ❓ Honors & awards

**Next: Please share more entities from the `included` array to see:**
1. Full Position entity (with job title, description if available)
2. Full Education entity (with degree, field of study, dates)
3. Any Certification entities (if present)

### Parsed Response Design

**Proposed structure for `get_profile_professional_info_graphql()`:**

```python
{
    "profile": {
        "entity_urn": "urn:li:fsd_profile:ACoAAAvf7-UBk_8MvFoDYosW9PdYq24NTpjzHQA",
        "first_name": "Amber",
        "last_name": "DeVilbiss",
        "public_identifier": "amberdevilbiss",
        "headline": "...",
        "location": {
            "country_code": "us",
            "postal_code": null
        },
        "profile_picture": {
            "root_url": "https://media.licdn.com/dms/image/v2/...",
            "images": {
                "100x100": "...",
                "200x200": "...",
                "400x400": "...",
                "800x800": "..."
            }
        },
        "verified": true,
        "premium": false,
        "creator": false
    },
    "education": [
        {
            "urn": "urn:li:fsd_profileEducation:(...)",
            "school": {
                "name": "Colorado State University Global",
                "logo_url": "...",
                "urn": "urn:li:fsd_school:42146"
            }
            # Note: Full details require resolving the URN
        }
    ],
    "positions": [
        # URN references only - need to resolve for full data
    ],
    "companies": [
        {
            "name": "Skyhigh Security",
            "universal_name": "skyhighsecurity",
            "logo": {...},
            "url": "https://www.linkedin.com/company/skyhighsecurity/"
        }
    ],
    "mutual_connections": {
        "count": 2,
        "insight_text": "David Barthelemy and Wayne Smith are mutual connections",
        "profiles": [
            {
                "first_name": "David",
                "last_name": "Barthelemy",
                "public_identifier": "david-barthelemy-611996bb",
                "profile_picture": {...}
            }
        ]
    },
    "member_relationship": {
        "is_connection": true,
        "connected_at": 1670475031000
    }
}
```

---

## Comparison with Other Endpoints

| Endpoint | Purpose | Parameter Type |
|----------|---------|----------------|
| `get_profile_graphql()` | Basic profile info | URN or public_id |
| `get_profile_contact_info_graphql()` | Contact details | public_id |
| `get_profile_skills_graphql()` | Skills & endorsements | URN |
| **`get_profile_professional_info_graphql()`** | **Work/Education/Certs** | **vanityName (public_id)** |

---

## Implementation Strategy

### Recommended Approach: Two-Phase Data Retrieval

**Phase 1: Get Profile Structure (Variation 3)**
```python
# Call metadata endpoint to get ProfileCard URNs
metadata = get_profile_structure(vanity_name="amberdevilbiss")
cards = metadata["cards"]  # List of all ProfileCard URNs

# Extract specific card URNs
experience_card = find_card(cards, "EXPERIENCE")
education_card = find_card(cards, "EDUCATION")
certifications_card = find_card(cards, "LICENSES_AND_CERTIFICATIONS")
```

**Phase 2: Fetch Detailed Data for Each Card**
```python
# Use ProfileCard URNs to fetch detailed data
experience_data = fetch_profile_card(experience_card)
education_data = fetch_profile_card(education_card)
certifications_data = fetch_profile_card(certifications_card)
```

### Why This Approach?

1. **Variation 1** gives us SOME data (positions with dates, companies) but may not include full details
2. **Variation 3** gives us the STRUCTURE (all available sections as URNs)
3. **Individual ProfileCard fetches** give us COMPLETE data for each section

### Alternative: Use Variation 1 + Fallback

If Variation 1 provides sufficient data (positions with dates, companies), we can:
1. Use Variation 1 as primary source
2. Fall back to ProfileCard fetches only when detailed data is missing

## Next Steps

1. ✅ Document Variation 1 (vanityName - partial data)
2. ✅ Document Variation 2 (profileUrn - minimal data)
3. ✅ Document Variation 3 (vanityName - metadata/structure)
4. ⏳ **CRITICAL**: Test fetching individual ProfileCard data (EXPERIENCE, EDUCATION, LICENSES_AND_CERTIFICATIONS)
5. ⏳ Determine if Variation 1 data is sufficient or if we need ProfileCard fetches
6. ⏳ Design final method signature based on findings
7. ⏳ Implement parsing logic
8. ⏳ Create route endpoint

---

## Notes

- **QueryId may change**: Like other GraphQL endpoints, the queryId (`voyagerIdentityDashProfiles.a1a483e719b20537a256b6853cdca711`) may need to be updated when LinkedIn updates their frontend
- **includeWebMetadata**: Set to `true` - purpose unclear, may provide additional metadata
- **Variables format**: Uses LinkedIn's custom format `(vanityName:value)` instead of JSON

---

## Implementation Date
*To be determined*

## Related Documentation
- [GraphQL Contact Info Endpoint](./graphql-contact-info-endpoint.md)
- [GraphQL Skills Endpoint](./graphql-skills-endpoint.md)
