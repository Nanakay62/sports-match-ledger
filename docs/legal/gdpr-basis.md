# GDPR Compliance & Data Protection Policy

**Sports News AI — Accountability Ledger**  
**Document Version:** 1.0.0  
**Effective Date:** September 2026  
**Contact:** `dpo@sportsnewsai.com`

---

## 1. Executive Summary & Regulatory Context

Sports News AI operates an evidence-grounded news aggregation and verification platform. The product differentiator is the **Accountability Ledger**: substantive claims from published sports reporting are extracted, attributed to their original outlet and byline, corroborated against independent sources, and resolved against official outcomes to generate public reliability ratings.

This document outlines the lawful basis for processing personal data, our data retention schedules, and data subject rectification protocols under the EU General Data Protection Regulation (Regulation (EU) 2016/679 - "GDPR") and national implementing legislation.

---

## 2. Lawful Basis for Processing (Art. 6 & Art. 85 GDPR)

Sports News AI processes personal data under two primary lawful bases:

### 2.1 Legitimate Interests (Art. 6(1)(f) GDPR)
Processing is necessary for the purposes of the legitimate interests pursued by the controller and the public, specifically:
- Providing transparent, public interest reporting on sports news accuracy.
- Maintaining receipts and provenance for news claims circulating in public discourse.
- Countering misinformation and uncorroborated rumours in sports media.

**Legitimate Interest Balancing Assessment:**
- **Necessity:** Public accountability cannot be delivered without recording the identity of the publishing outlet and the reporter's public byline.
- **Reasonable Expectations:** Professional sports journalists and news outlets publish articles intentionally for wide public distribution. It is within their reasonable expectations that published statements and bylines are read, analyzed, cited, and evaluated by media monitors and readers.
- **Fundamental Rights:** The processing is strictly limited to public professional output (bylines, public articles). No private, domestic, or non-professional personal data is collected or processed.

### 2.2 Freedom of Expression & Information (Art. 85 GDPR)
Member State law provides exemptions and derogations for processing carried out for journalistic purposes and the purposes of academic, artistic, or literary expression. Sports News AI exercises its journalistic and media accountability function by fact-checking, corroborating, and contextualizing public sports reports.

---

## 3. Data Categories Processed

1. **Journalist / Reporter Professional Information:**
   - Public byline name.
   - Public professional affiliations (outlet, publication, employer).
   - Public beat or focus area (e.g., Football / Transfers).
2. **Sports Figures (Players, Managers, Executives):**
   - Professional name and known aliases.
   - Sports club or national team affiliation.
   - Public career events (transfers, contracts, injuries, disciplinary actions).
3. **Public Audience / Users:**
   - Free tier users: Zero mandatory account creation or tracking cookies.
   - Pro tier subscribers: Email address and payment entitlement flags (handled via merchant-of-record).

---

## 4. Retention Schedule & Ledger Immutability

Sports News AI balances privacy minimization with historical audit integrity:

| Data Category | Retention Period | Justification |
| :--- | :--- | :--- |
| **Raw Scraped HTML / Document Bodies** | **90 Days** | Temporary buffer for extraction verification; purged after 90 days. |
| **Extracted Structured Claims** | **Indefinite (Append-Only)** | Essential for ledger integrity. Modifying or deleting claims would falsify historical reliability calculations. |
| **Outcome Resolutions & Scores** | **Indefinite** | Required for public accountability and verifiable mathematical scoring (Wilson lower bound). |
| **Quarantined / Malformed Documents** | **30 Days** | Debugging and SSRF security review; automatically purged thereafter. |
| **User Entitlements** | **Duration of Subscription + 12 Months** | Tax and merchant billing compliance. |

---

## 5. Data Subject Rights & Rectification Protocol

Under GDPR Articles 15–22, data subjects possess rights regarding access, rectification, erasure, and objection. Because Sports News AI operates an append-only accountability ledger, these rights are handled as follows:

### 5.1 Right to Rectification (Art. 16 GDPR)
- If a published claim, attribution, or fact is proven inaccurate or has been formally retracted by the original source:
  - We **do not silently edit or delete** ledger records (which would destroy audit transparency).
  - We issue a **formal supersession record** (`is_superseded = True`, `superseded_by = [NEW_CLAIM_ID]`).
  - The correction is prominently published on the public [`/corrections`](file:///apps/web/app/corrections) register and permanently linked to the event.

### 5.2 Right to Erasure ("Right to be Forgotten", Art. 17 GDPR)
- Under Art. 17(3)(a) and (d), erasure does not apply to processing necessary for:
  - Exercising the right of freedom of expression and information (journalistic exemption).
  - Archiving purposes in the public interest, scientific or historical research.
- Where requests concern private individuals (e.g., non-public figures or minors inadvertently cited in source feeds), full redaction and masking are immediately executed via manual editorial intervention.

### 5.3 Contact & DPO Inquiries
Requests for access, clarification, or editorial rectification should be directed to:
- **Email:** `dpo@sportsnewsai.com`
- **Editorial Review:** Accessible through the public corrections form on the website.
- **Response SLA:** Inquiries are acknowledged within 48 hours and resolved within 30 days.
