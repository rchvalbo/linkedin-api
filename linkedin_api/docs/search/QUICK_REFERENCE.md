# Search Enhancement - Quick Reference Card

**Last Updated:** October 24, 2025

---

## 🚀 New Fields At A Glance

| Field | Type | Example | Coverage |
|-------|------|---------|----------|
| `public_identifier` | string | `"katie-oberle-37a64a278"` | 98% |
| `connection_degree` | string | `"2nd"` | 95% |
| `mutual_connections_count` | int | `55` | 100% |
| `mutual_connections_url` | string | `"https://..."` | 60% |
| `is_premium` | bool | `false` | 100% |
| `company` | string | `"Med4Hire"` | 70% |
| `member_id` | int | `1136267662` | 98% |
| `profile_ring_status` | string | `"HIRING"` | 5% |
| `is_hiring` | bool | `false` | 3% |
| `is_open_to_work` | bool | `false` | 2% |

---

## 💡 Common Use Cases

### Filter Warm Leads
```python
warm = [l for l in results if l['connection_degree'] == '2nd' and l['mutual_connections_count'] >= 10]
```

### Find Hiring Managers
```python
hiring = [l for l in results if l['is_hiring']]
```

### Premium Members Only
```python
premium = [l for l in results if l['is_premium']]
```

### Target Specific Companies
```python
target = [l for l in results if l['company'] in ['Google', 'Microsoft']]
```

---

## 🎯 Lead Scoring Formula

```python
score = 0
score += 40 if degree == '1st' else 25 if degree == '2nd' else 10
score += 30 if mutual >= 50 else 20 if mutual >= 20 else 10 if mutual >= 5 else 0
score += 15 if is_premium else 0
score += 15 if is_hiring else 0
```

---

## 📝 Personalization Template

```python
if mutual_connections_count >= 10:
    msg = f"Hi {name}, we have {mutual_connections_count} mutual connections!"
elif company:
    msg = f"Hi {name}, I saw you work at {company}."
else:
    msg = f"Hi {name}, I'd love to connect!"
```

---

## ⚠️ Null Handling

Always check for null:
```python
company = result.get('company') or 'Unknown'
degree = result.get('connection_degree') or '3rd+'
```

---

## 📊 Field Availability

- ✅ **Always Available:** urn_id, lead_name, distance, mutual_connections_count, is_premium
- ⚠️ **Usually Available (>90%):** job_title, location, connection_degree, public_identifier, member_id
- ⚠️ **Sometimes Available (60-80%):** company, mutual_connections_url
- ❌ **Rarely Available (<10%):** profile_ring_status, is_hiring, is_open_to_work

---

## 🔗 Documentation Links

- **Full API Docs:** `ENHANCED_SEARCH_RESPONSE.md`
- **Implementation Guide:** `SEARCH_DATA_ANALYSIS.md`
- **Field Comparison:** `SEARCH_FIELD_COMPARISON.md`
- **Code:** `/routes/search.py` (lines 17-304)

