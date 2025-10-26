# LinkedIn API Parsers

This directory contains parser modules for LinkedIn API responses.

---

## 📁 Structure

```
parsers/
├── README.md                    # This file
├── search_parser.py             # Search response parser
├── test_search_parser.py        # Unit tests for search parser
├── experience_parser.py         # Experience response parser (existing)
├── education_parser.py          # Education response parser (existing)
└── ...                          # Other parsers
```

---

## 🔍 Search Parser

**File:** `search_parser.py`

### Purpose
Extracts and enriches data from LinkedIn search API responses. Provides helper functions to parse various fields from search results.

### Main Function

```python
from parsers.search_parser import parse_search_result

# Parse a complete search result
result = parse_search_result(raw_item)
```

**Returns:** Dict with 18 fields (7 original + 11 enhanced)

### Helper Functions

| Function | Purpose | Returns |
|----------|---------|---------|
| `extract_mutual_connections(item)` | Parse mutual connections count and URL | `Dict[str, Any]` |
| `extract_connection_degree(item)` | Extract "1st", "2nd", "3rd" | `Optional[str]` |
| `extract_premium_status(item)` | Check if premium member | `bool` |
| `extract_public_identifier(url)` | Parse vanity URL slug | `Optional[str]` |
| `extract_company_from_job_title(title)` | Parse company name from headline | `Optional[str]` |
| `extract_ring_status(item)` | Extract hiring/open-to-work status | `Dict[str, Any]` |
| `extract_member_id(item)` | Extract numeric member ID | `Optional[int]` |

---

## 🧪 Testing

### Run Tests

```bash
# Run all parser tests
pytest parsers/test_search_parser.py -v

# Run specific test class
pytest parsers/test_search_parser.py::TestExtractCompanyFromJobTitle -v

# Run with coverage
pytest parsers/test_search_parser.py --cov=search_parser --cov-report=html
```

### Test Coverage

- ✅ Mutual connections extraction (3 test cases)
- ✅ Connection degree extraction (4 test cases)
- ✅ Premium status detection (3 test cases)
- ✅ Public identifier parsing (4 test cases)
- ✅ Company name extraction (7 test cases)
- ✅ Ring status extraction (3 test cases)
- ✅ Member ID extraction (3 test cases)

**Total:** 27 test cases

---

## 📊 Usage Example

### In Routes

```python
from parsers.search_parser import parse_search_result

@router.get("/search/people")
def search_people(params: SearchParams):
    # Get raw data from LinkedIn API
    raw_data = api.search(params)
    
    # Parse each result
    results = []
    for item in raw_data:
        parsed = parse_search_result(item)
        results.append(parsed)
    
    return results
```

### Direct Helper Usage

```python
from parsers.search_parser import (
    extract_company_from_job_title,
    extract_mutual_connections
)

# Extract company from job title
company = extract_company_from_job_title("Engineer @ Google")
# Returns: "Google"

# Extract mutual connections
mutual = extract_mutual_connections(search_item)
# Returns: {'mutual_connections_count': 55, 'mutual_connections_url': '...'}
```

---

## 🎯 Benefits of Separation

### 1. **Maintainability**
- Parsing logic centralized in one place
- Easy to update when LinkedIn API changes
- Clear separation of concerns

### 2. **Testability**
- Each function can be unit tested independently
- Mock data easier to create
- Better test coverage

### 3. **Reusability**
- Parser can be used in multiple routes
- Helper functions can be imported individually
- Consistent parsing across the application

### 4. **Documentation**
- Type hints for all functions
- Docstrings with examples
- Clear function signatures

### 5. **Performance**
- No duplicate parsing logic
- Easier to optimize
- Can add caching if needed

---

## 🔧 Adding New Parsers

### Template

```python
def extract_new_field(item: Dict[str, Any]) -> Optional[str]:
    """
    Extract new field from search result.
    
    Args:
        item: Search result item from LinkedIn API
        
    Returns:
        Extracted value or None
        
    Example:
        >>> extract_new_field(item)
        'value'
    """
    # Extraction logic here
    value = item.get("path", {}).get("to", {}).get("field")
    return value if value else None
```

### Steps

1. Add extraction function to `search_parser.py`
2. Add type hints and docstring
3. Update `parse_search_result()` to include new field
4. Add unit tests to `test_search_parser.py`
5. Update documentation

---

## 📝 Best Practices

### Type Hints
Always use type hints for better IDE support:
```python
def extract_field(item: Dict[str, Any]) -> Optional[str]:
    ...
```

### Null Safety
Always handle missing/null values:
```python
value = item.get("field", {}).get("nested", None)
return value if value else None
```

### Regex Patterns
Use raw strings and case-insensitive matching:
```python
match = re.search(r'pattern', text, re.IGNORECASE)
```

### Documentation
Include examples in docstrings:
```python
"""
Example:
    >>> extract_company("Engineer @ Google")
    'Google'
"""
```

---

## 🐛 Common Issues

### Issue: Field Not Extracting
**Solution:** Check the sample response JSON to verify field path

### Issue: Regex Not Matching
**Solution:** Test regex pattern with various input formats

### Issue: Type Errors
**Solution:** Add proper null checks and type conversions

---

## 📚 Related Documentation

- **API Documentation:** `/docs/search/ENHANCED_SEARCH_RESPONSE.md`
- **Field Analysis:** `/docs/search/SEARCH_DATA_ANALYSIS.md`
- **Sample Response:** `/docs/search/search-response.json`
- **Usage in Routes:** `/routes/search.py`

---

## 🔄 Version History

**v1.0.0** (October 24, 2025)
- Initial release
- 7 extraction helper functions
- 1 main parsing function
- 27 unit tests
- Complete documentation

