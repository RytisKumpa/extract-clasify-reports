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

- [Python](#tab-panel-184)
- [TypeScript](#tab-panel-185)

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
