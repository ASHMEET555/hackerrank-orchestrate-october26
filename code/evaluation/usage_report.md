# Model and API Usage Report

## Summary of Usage and Costs

The Ghost Data Still Exists deletion audit engine runs completely locally without external LLM API calls, cloud endpoints, or external model providers. All identity resolution, evidence indexing, linking, rule evaluation, and step planning operate deterministically via Python standard libraries and local readers.

---

## 1. Usage Summary

| Item | Value |
|---|---|
| **Model Provider** | None (Local deterministic rules engine) |
| **Model Name(s)** | None |
| **Total Model Calls** | 0 |
| **Input Tokens** | 0 |
| **Output Tokens** | 0 |
| **Total Tokens** | 0 |
| **Average Tokens per Request** | 0 |
| **Estimated Total Cost** | **$0.00** |
| **Estimated Cost per Request** | **$0.00** |

---

## 2. API Client Verification
Grep execution across `code/`, `code/tools/`, and `code/readers/` for external client libraries:

```bash
git grep -rn -E "anthropic|openai|google.generativeai|requests.post|httpx" code/ code/tools code/readers || echo "no API clients"
```

**Output**:
```text
no API clients
```

Zero external network requests or third-party inference APIs are invoked during the full execution of the 518 evaluation cases.
