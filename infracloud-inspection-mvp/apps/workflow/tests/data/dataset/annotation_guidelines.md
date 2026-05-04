# Annotation Guidelines — InfraCloud Inspection v1 Benchmark

These rules must be applied consistently when creating or reviewing gold labels for all 50 dataset cases. Read this document fully before annotating any case.

---

## 1. Gold vs Benchmark

**Gold** is ground truth about the inspection scenario — what the inspector said and what the correct field values are.
**Benchmark** is configuration about expected model behaviour — warnings, audio degradation, etc.

Never put model predictions or confidence estimates into the `gold` block.

---

## 2. `source_type` — How a Gold Value Was Determined

Every gold field must declare how its value was determined:

| source_type | Meaning | Example |
|-------------|---------|---------|
| `stated` | Inspector said the value explicitly and unambiguously | "Das ist Klasse zwei" → Class = "2" |
| `derived` | Value was calculated from something the inspector said using a defined rule | "Rissbreite eineinhalb Millimeter" → Class = "2" (via width table) |
| `inferred` | Value is a best guess — inspector was vague, hedged, or used a non-catalog synonym | "Ich glaube es ist ein Längsriss" → Damage Type inferred |

When in doubt between `stated` and `derived`, prefer `derived`. When in doubt between `derived` and `inferred`, prefer `inferred`.

---

## 3. Class Derivation from Crack Width

Use this mapping when an inspector gives a crack width measurement but does not state a class:

| Crack Width | Gold Class | source_type |
|-------------|-----------|-------------|
| < 1.0 mm | "1" | derived |
| 1.0 mm – 2.0 mm | "2" | derived |
| > 2.0 mm | "3" | derived |

**Borderline values:** Exactly 1.0 mm → Class "2" (inclusive lower bound). Exactly 2.0 mm → Class "2" (inclusive upper bound).

If the inspector states a class directly, use `stated` regardless of any width mentioned.
If both a class and a measurement are given and they contradict, use the stated class and note the contradiction in `description`.

---

## 4. Unit Normalization

All dimension fields (Length, Width, Depth) are stored in **centimetres** as a string.

| Inspector says | Gold value |
|----------------|-----------|
| "dreißig Zentimeter" | "30" |
| "dreißig Millimeter" | "3" |
| "eineinhalb Millimeter" | "0.15" |
| "zwei Meter" | "200" |
| "dreißig" (no unit) | "30" + source_type=`inferred` |

When no unit is given, assume cm and mark source_type as `inferred`.

---

## 5. Catalog Synonym Mapping

If the inspector uses a word that is not the exact catalog string, map to the nearest catalog value:

| Inspector says | Gold Damage Type | source_type |
|----------------|-----------------|-------------|
| "Längsriss" | "Risse \| Längsriss (trocken)" | inferred |
| "nasser Riss diagonal" | "Risse \| Diagonal (nass)" | inferred |
| "Rost" on steel | "Stahl \| Verrostet" | inferred |
| "Lochfraß" | "Bewehrung \| Lochkorrosion" | inferred |
| "abgesackt" | "Formänderung \| Abgesackt" | inferred |

If no reasonable catalog mapping exists, set value to `null` and set `catalog_valid = false`.

---

## 6. Self-Corrections

Gold value is always the **final stated value** after the correction.

> "Klasse drei, nein, Klasse zwei, also Klasse zwei."
> Gold Class = `"2"`, source_type = `stated`

Include the full corrected phrase as `evidence_span`.

---

## 7. Uncertain Speech

If the inspector uses hedging language ("ich glaube", "könnte sein", "vielleicht", "bin mir nicht sicher") **without further confirmation**, mark the field:

- `source_type = "inferred"`
- `is_critical = false`

If the same field is later confirmed in the same transcript, upgrade to `stated` or `derived`.

---

## 8. Intent Classification Rules

| Intent | Condition |
|--------|-----------|
| `VALIDATE_DAMAGE` | Inspector confirms the damage exists and provides/confirms field values. No conflict with existing record. |
| `REJECT_DAMAGE` | Inspector indicates the damage does not exist on site. Status gold = "Incorrectly detected". |
| `UPDATE_FIELD` | Inspector corrects one or more field values that differ from the existing record (conflicts present). |
| `CREATE_NEW` | Inspector describes a damage that has no corresponding suspicion. existing_record is a skeleton. |
| `UNSURE` | Intent cannot be determined from the transcript. Use for multiple damages in one utterance or genuinely ambiguous cases. |

**REJECT vs UPDATE boundary:** If the inspector says "there's no damage here" → REJECT. If the inspector corrects a value ("it's not concrete, it's steel") → UPDATE, even if they sound certain.

---

## 9. Status Transitions by Intent

| Intent | Gold Status |
|--------|-------------|
| VALIDATE_DAMAGE | "Damage" |
| REJECT_DAMAGE | "Incorrectly detected" |
| UPDATE_FIELD | Keep existing Status unless inspector explicitly changes it |
| CREATE_NEW | "Damage" (new damage being reported) |

---

## 10. Conflict vs Enrichment

- **Conflict:** extracted value ≠ existing_record value, and **both are non-null**
- **Enrichment:** existing_record value is null, extracted value is non-null → this is NOT a conflict, it is an enrichment

Only list conflicts in `gold.conflicts`. Enrichments are reflected only in `gold.fields`.

---

## 11. Material / Damage Type Cascade

When the material changes, the damage type gold value must also change to a valid catalog combination. If the inspector does not explicitly state the new damage type, derive it from the valid combos for the new material:

- Mark the inferred damage type as `source_type = "derived"`, not `stated`
- If multiple valid damage types exist for the new material, choose the most contextually appropriate one or use `inferred`

---

## 12. CREATE_NEW Existing Record Convention

For CREATE_NEW cases (TC039–TC043), the `existing_record` is a **minimal skeleton** — all damage fields are null, but asset/part/location context may be provided:

```json
{
  "Suspicion ID": "TC039",
  "Asset": "...",
  "Part": "...",
  "Object Part Category": "...",
  "Main Component Category": "...",
  "Status": "Suspicion",
  "Material": null,
  "Damage Type": null,
  "Class": null,
  "Length": null,
  "Width": null,
  "Depth": null,
  "Quantity": null,
  "Location Longitudinal": null,
  "Location Cross Section": null,
  "Location Height": null,
  "Damage description": null,
  "Remark": null,
  "Note": null
}
```

Conflict detection will produce no conflicts for CREATE_NEW cases (all existing fields are null). This is expected.

---

## 13. "Not Extractable" vs Null vs N/A

Three distinct gold values — do not confuse them:

| Value | Meaning | Scoring behaviour |
|-------|---------|-------------------|
| `null` | Inspector said nothing about this field. No information present. | Model returning `null` → PASS. Model returning a value → FAIL. |
| `"not_extractable"` | Inspector attempted to provide a value but it cannot be reliably determined — too noisy, garbled, self-contradictory, or mid-sentence cutoff. | Model returning `null` → PASS (correct abstention). Model returning any value → flagged as **hallucination risk** (separate counter in evaluation report, not a hard failure). |
| `"N/A"` | Field is structurally inapplicable for this case (e.g., Depth for a surface stain where depth has no meaning). | Model returning `null` or `"N/A"` → PASS. |

**When to use each:**

- Use `null` when the inspector simply did not mention the field.
- Use `"not_extractable"` when the inspector clearly attempted to convey a value, but the content is too ambiguous, garbled, or incomplete to annotate reliably. Examples:
  - Audio too noisy to hear a number: *"Die Länge ist... [wind noise]..."*
  - Inspector starts a classification then stops: *"Das ist eine Art... hmm."*
  - Measurement given but unit genuinely unknowable from context: *"Dreißig irgendwas."*
  - TC043-style unclear damage type: inspector describes seeing something structural but cannot name it
- Use `"N/A"` only when the field is structurally inapplicable. When in doubt between `null` and `"N/A"`, use `null`.

**source_type for `"not_extractable"` fields:**

Always use `source_type = "inferred"` and `is_critical = false`. The evidence_span should quote the fragment that triggered the annotation.

```json
"Damage Type": {
  "value": "not_extractable",
  "source_type": "inferred",
  "evidence_span": "es sieht aus wie irgendwas strukturelles, kann ich nicht genau sagen",
  "is_critical": false
}
```

**Hallucination risk counter in evaluation:**

The evaluator tracks a separate `hallucination_risk` column in the CSV. This is set to `true` when `gold_value == "not_extractable"` and the model returned a non-null value. It is reported separately from `field_correct` so it does not inflate the field failure rate but is still visible in the summary.

---

## 14. Multiple Damages in One Utterance

If the inspector clearly describes two distinct damage locations in a single recording:
- Set `intent = "UNSURE"`
- Label only the **first damage** in `gold.fields`
- Note the second damage in the case `description`
- Tag the case with `multiple_damages`

---

## 15. `is_critical` Assignment

A field is **critical** (`is_critical: true`) if a model error on this field would require human correction before the record could be submitted. Default rules:

| Field | is_critical |
|-------|-------------|
| Intent | true (always) |
| Status | true |
| Damage Type | true |
| Material | true |
| Class | false (unless derived from width in a VALIDATE case) |
| Length / Width / Depth | false |
| Quantity | false |
| Remark | false |
| Location fields | false |

Override: if a case specifically tests a field (e.g., TC025 tests Class upgrade), mark that field as `is_critical = true` for that case.

---

## 16. Inter-Annotator Agreement Check

Before building all 50 cases, independently annotate cases TC001, TC016, TC024, TC034, TC046, TC048 and compare:
- Intent agreement
- Critical field value agreement
- Conflict field list agreement

Resolve any disagreements by updating these guidelines before continuing.
