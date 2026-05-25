---
title: Schema Design and Restrictions | Developer Documentation
description: Guide on designing schemas for LlamaExtract, including tips, best practices, examples, and JSON Schema restrictions.
---

At the core of LlamaExtract is the schema, which defines the structure of the data you want to extract from your documents.

## How to define your schema

A schema is made of **fields**. Each field has a **name**, a **type**, and optionally a **description**.

- **Field names** — Use clear, stable names that match how you’ll use the data (e.g. `invoice_number`, `vendor_name`). These become the keys in the extracted JSON.
- **Field descriptions** — Descriptions are **additional context for the underlying LLM**. They are not only for documentation: the extraction model uses them to decide what to extract. Use descriptions to guide the model on what the value for the field could be—for example, what the field means, where it usually appears in the document, acceptable formats, or examples. Better descriptions typically lead to more accurate and consistent extraction.

## Schema Restrictions

*LlamaExtract only supports a subset of the JSON Schema specification.* While limited, it should be sufficient for a wide variety of use-cases.

- If you are specifying the schema as a JSON, there are two ways you can mark optional fields:

    - not including them in the containing object’s `required` array
    - explicilty marking them as nullable fields using `anyOf` with a `null` type. See `"start_date"` field in the [example schema](../../getting_started/api).

- If you are using Pydantic for specifying the schema in the Python SDK, you can use the `Optional` annotation for marking optional fields.

- Root node must be of type `object`.

- Schema nesting must be limited to within 7 levels.

- The important fields are key names/titles, type and description. Fields for formatting, default values, etc. are **not supported**. If you need these, you can add the restrictions to your field description and/or use a post-processing step. e.g. default values can be supported by making a field optional and then setting `"null"` values from the extraction result to the default value.

- Additional schema restrictions:

    - **Maximum properties**: 5,000 total properties across the entire schema.
    - **Maximum total string content**: 120,000 characters for all strings (field names, descriptions, enum values, etc.) combined.
    - **Maximum raw JSON schema size**: 150,000 characters for the raw JSON schema string.

- If you hit these limits for complex extraction use cases, consider restructuring your extraction workflow to fit within these constraints, e.g. by extracting subsets of fields and later merging them together.

## Tips & Best Practices

- Try to limit schema nesting to 3-4 levels.
- Make fields optional when data might not always be present (specially `boolean` and `int` fields where defaults for missing values could cause confusion).
- When you want to extract a variable number of entities, use an `array` type. However, note that you cannot use an `array` type for the root node.
- Use descriptive field names and detailed descriptions. Use descriptions to pass formatting instructions or few-shot examples.
- Above all, start simple and iteratively build your schema to incorporate requirements.

## Writing a Factual Extraction Policy (Anti-Hallucination)

Field-level descriptions tell the model *what* to extract for a given field. A **top-level extraction policy** — placed in the root `description` of your schema — tells the model *how* to extract across **every** field. This is the single most effective lever for getting factual, neutral, source-grounded outputs from LlamaExtract.

A well-written extraction policy reduces three common failure modes:

- **Hallucination**: the model invents a value not stated in the document.
- **Interpretation drift**: the model paraphrases or summarises in a way that loses the document's original meaning.
- **Unsolicited judgement**: the model makes assessments (e.g. "high risk", "strong moat") that the document never made.

### What to include in a top-level extraction policy

A robust policy typically covers:

1. **Neutrality** — extract only what the document states; do not assess, judge, or score.
2. **Source-grounding** — require verbatim quotations alongside extracted values, with location references.
3. **Null over guess** — when in doubt, return `null` rather than infer.
4. **No computation** — never compute ratios, growth rates, margins, or other derived values; extract only stated figures.
5. **Partial-information handling** — when a field is only partially defined in the document, capture what is available rather than returning `null` for the whole field.
6. **Attribution** — preserve the original source of claims (e.g. third-party research, management interview).
7. **Conditional sections** — clarify which sections only populate under specific conditions.

### Worked example

Below is a worked example of a top-level policy used in an investment due diligence extraction schema. Adapt the same structure to your own domain.

```text
Schema for extracting investment due diligence information from documents
(VDD reports, buyside DD, IMs, pitch decks, management presentations,
market research, analyst reports, transcripts).

CORE EXTRACTION POLICY — apply to every field:

1. NEUTRALITY: Extract only what the document STATES. Do not assess, judge,
   or score. Where a field is named 'document_stated_X', the value reflects
   the DOCUMENT'S characterisation, not your own.

2. SOURCE-GROUNDING: Most value-bearing fields are wrapped in objects with
   'value', 'quotes', and 'attribution' properties. NOTE: High-volume sections
   (financial_statements, revenue_mix, unit_economics, working_capital_metrics,
   ebitda_bridge, sales_pipeline_and_bookings) do NOT carry cell-level quotes
   for practical reasons — capture stated values directly.

3. QUOTES FORMAT: Each entry in a 'quotes' array is a single string:
   '<verbatim quote, ≤50 words> @ <location>'. Location can be page number,
   section heading, slide number, etc. Up to 5 quotes per field. DO NOT
   paraphrase — copy text exactly.

4. ATTRIBUTION FORMAT: 'attribution' field is a single string:
   '<source_type>: <source_name>'. source_type values: company_management,
   company_financials_audited, company_financials_unaudited,
   third_party_research, industry_expert_interview, public_filings,
   news_article, regulatory_filing, document_author_analysis,
   not_specified, not_known. Example: 'third_party_research:
   Gartner Magic Quadrant 2024'.

5. NULL OVER GUESS: If a field is not explicitly stated, set value to null
   and leave quotes empty. Never invent.

6. NO COMPUTATION: Do not compute ratios, growth rates, margins, or
   conversions. Capture only stated values.

7. PARTIAL INFO: For partial information (e.g. TAM defined for some
   geographies but not others), capture what is available rather than null.

8. CONDITIONAL SECTIONS: 'merger_considerations' populates only when
   deal_type == 'merger'; 'carveout_considerations' only when deal_type ==
   'carve_out'. 'dd_side' applies only when document_type is a DD report.
```

### Design patterns that support a factual policy

The policy itself is only half the work. The schema structure should support it:

- **`document_stated_X` field naming** — for any interpretive field (severity, threat level, posture, intensity), prefix the field name with `document_stated_` to signal that the value must come from the document, not the model's judgement. For example, prefer `document_stated_competitive_threat_level` over `competitive_threat_level`.
- **Paired `value`+`quotes`+`attribution` wrappers** — wrap value-bearing fields in an object with the value and supporting evidence as sibling properties. This forces the model to produce evidence alongside the value, rather than treating evidence as optional.
- **Compact stringified formats** — to stay within LlamaExtract's schema size limits, represent quotes as flat strings (`'<verbatim> @ <location>'`) and attribution as a single string (`'<type>: <name>'`) rather than deeply nested objects. The trade-off is that downstream code must parse these strings.
- **Selective application** — apply source-grounding wrappers where they add value (narrative claims, judgements, market estimates) and skip them where the cost outweighs the benefit (high-volume tabular data like financial line items, where per-cell quotes become impractical). Document the exceptions in the root policy so the model knows where they apply.
- **Conditional sections** — for sections that should only populate under certain conditions (e.g. merger considerations when `deal_type == "merger"`), state the condition explicitly in the policy and in the section's own description.

### Tips when iterating on your policy

- **Test on adversarial documents.** Use documents that are vague, incomplete, or contradictory — these surface hallucination patterns that clean documents do not.
- **Be explicit, not aspirational.** "Be accurate" is too vague to act on. "Return null when not explicitly stated" is enforceable.
- **Use ALL CAPS sparingly but deliberately** for the highest-priority rules (e.g. "DO NOT paraphrase", "Capture only STATED values"). Models pay disproportionate attention to capitalised instructions.
- **Keep field descriptions short** when a global policy already covers the rule. Repeating the same guidance in every field description bloats the schema and dilutes attention.
- **Measure provenance, not just accuracy.** A value extracted without a supporting quote is suspicious — even if the value happens to be correct. Auditing extraction quality should include checking that quotes match the document.

## Automatic Schema Generation

Instead of manually defining schemas, you can use LlamaExtract’s automatic schema generation feature. The system can generate a schema based on:

- **A natural language prompt**: Describe what data you want to extract
- **A sample file**: Upload a document and let the system infer the schema from its structure
- **An existing schema to refine**: Provide a base schema and let the system improve or extend it

You can combine these inputs — for example, provide both a sample file and a prompt to guide the generation.

### Using the REST API

Terminal window

```
curl -X 'POST' \
  'https://api.cloud.llamaindex.ai/api/v2/extract/schema/generate?project_id={PROJECT_ID}' \
  -H 'accept: application/json' \
  -H "Authorization: Bearer $LLAMA_CLOUD_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "prompt": "Extract invoice details including invoice number, date, vendor name, line items with descriptions and amounts, and total amount",
    "file_id": "optional-file-id-for-sample-document"
  }'
```

Note

Automatic schema generation may include more fields than you need. Review the generated schema and remove unnecessary fields before using it in production — fewer, well-defined fields typically lead to better extraction quality.

For the full API documentation, see the [LlamaExtract API Reference](https://developers.llamaindex.ai/reference/resources/extract/).

## Defining Schemas with SDKs

- [Python](#tab-panel-174)
- [TypeScript](#tab-panel-175)

The Python SDK can be installed using

Terminal window

```
pip install llama-cloud>=2.1
```

Schemas can be defined using either Pydantic models or JSON Schema:

### Using Pydantic (Recommended)

```
from pydantic import BaseModel, Field
from typing import List, Optional


class Experience(BaseModel):
    company: str = Field(description="Company name")
    title: str = Field(description="Job title")
    start_date: Optional[str] = Field(description="Start date of employment")
    end_date: Optional[str] = Field(description="End date of employment")


class Resume(BaseModel):
    name: str = Field(description="Candidate name")
    experience: List[Experience] = Field(description="Work history")


schema = Resume.model_json_schema()
```

### Using JSON Schema

```
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Candidate name"},
        "experience": {
            "type": "array",
            "description": "Work history",
            "items": {
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string",
                        "description": "Company name",
                    },
                    "title": {"type": "string", "description": "Job title"},
                    "start_date": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "Start date of employment",
                    },
                    "end_date": {
                        "anyOf": [{"type": "string"}, {"type": "null"}],
                        "description": "End date of employment",
                    },
                },
            },
        },
    },
}
```

With your schema, you can directly run extractions using the SDK:

```
from llama_cloud import LlamaCloud


client = LlamaCloud(api_key="your_api_key")


file_obj = client.files.create(file="path/to/your/document.pdf", purpose="extract")


job = client.extract.create(
    file_input=file_obj.id,
    configuration={
            "data_schema": schema,
            "tier": "agentic",
        },
)


# Poll for completion
while job.status not in ("COMPLETED", "FAILED", "CANCELLED"):
    import time; time.sleep(2)
    job = client.extract.get(job.id)
```

The TypeScript SDK can be installed using

Terminal window

```
npm install @llamaindex/llama-cloud zod
```

Schemas can be defined using either Zod models or JSON Schema:

### Using Zod (Recommended)

```
import { z } from "zod";


const ExperienceSchema = z.object({
  company: z.string().describe("Company name"),
  title: z.string().describe("Job title"),
  start_date: z.string().nullable().describe("Start date of employment"),
  end_date: z.string().nullable().describe("End date of employment"),
});


const ResumeSchema = z.object({
  name: z.string().describe("Candidate name"),
  experience: z.array(ExperienceSchema).describe("Work history"),
});


const schema = z.toJSONSchema(ResumeSchema);
```

### Using JSON Schema

```
const schema = {
  type: "object",
  properties: {
    name: { type: "string", description: "Candidate name" },
    experience: {
      type: "array",
      description: "Work history",
      items: {
        type: "object",
        properties: {
          company: {
            type: "string",
            description: "Company name",
          },
          title: { type: "string", description: "Job title" },
          start_date: {
            anyOf: [{ type: "string" }, { type: "null" }],
            description: "Start date of employment",
          },
          end_date: {
            anyOf: [{ type: "string" }, { type: "null" }],
            description: "End date of employment",
          },
        },
      },
    },
  },
};
```

With your schema, you can directly run extractions using the SDK:

```
import fs from 'fs';
import LlamaCloud from '@llamaindex/llama-cloud';


const client = new LlamaCloud({
  apiKey: 'your_api_key',
});


const fileObj = await client.files.create({
  file: fs.createReadStream('path/to/your/document.pdf'),
  purpose: 'extract',
});


let job = await client.extract.create({
  file_input: fileObj.id,
  configuration: {
      data_schema: schema,
      tier: 'agentic',
    },
});


// Poll for completion
while (!['COMPLETED', 'FAILED', 'CANCELLED'].includes(job.status)) {
  await new Promise((r) => setTimeout(r, 2000));
  job = await client.extract.get(job.id);
}
```
