# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Investment Due Diligence Data Extraction and Analysis application built with LlamaAgents that extracts structured investment due diligence information from documents using LlamaExtract. The application processes investment documents (VDD/buyside DD, IMs, pitch decks, market research, transcripts) while maintaining strict factual accuracy and source attribution through an anti-hallucination extraction policy.

## Development Commands

**Python:**
```bash
# Linting and formatting
uv run hatch run lint

# Type checking
uv run hatch run typecheck

# Run tests
uv run hatch run test

# Run all at once
uv run hatch run all-fix
```

**JavaScript (in ui directory):**
```bash
cd ui
pnpm run lint
pnpm run typecheck
pnpm run test
pnpm run all-fix
```

**Running the application locally:**
```bash
# Requires uv to be installed
uvx llamactl serve
```

## Architecture

### Core Components

**Configuration System (`src/extraction_review/config.py`):**
- Defines Pydantic schemas for investment document types and sections
- Configuration is loaded from `configs/config.json` via ResourceConfig
- Uses investment analysis schema from `investment_analysis_schema_v3.json`

**Workflows:**
- `process-file` (`src/extraction_review/process_file.py`): Main workflow for processing investment documents
  - Steps: download → extract → store
  - Uses typed context to pass state between steps
  - Streams progress updates to UI via `Status` events
  
- `metadata` (`src/extraction_review/metadata_workflow.py`): Exposes configuration metadata to UI
  - Returns JSON schema and collection name for dynamic UI generation

**Data Collection:**
- Uses `EXTRACTED_DATA_COLLECTION = "sec-filing-extraction"` for storing extracted data
- Stores data in LlamaCloud Agent Data with deduplication by file hash

### Processing Flow

1. **File Upload**: User uploads investment document through UI
2. **Download**: File downloaded from LlamaCloud storage
3. **Extraction**: LlamaExtract processes document using investment analysis schema
4. **Storage**: Extracted data stored in Agent Data with deduplication
5. **Review**: UI displays extracted data for review and editing

### Investment Analysis Schema Structure

The extraction schema (`investment_analysis_schema_v3.json`) follows a strict **Anti-Hallucination Extraction Policy**:

**Core Extraction Principles:**
1. **Neutrality**: Extract only what the document states; no assessment, judgment, or scoring
2. **Source-Grounding**: Most value-bearing fields wrapped in `{value, quotes, attribution}` objects
3. **Quotes Format**: Array of strings `'<verbatim quote, ≤50 words> @ <location>'` 
4. **Attribution Format**: `'<source_type>: <source_name>'` where source_type ∈ {company_management, company_financials_audited, company_financials_unaudited, third_party_research, industry_expert_interview, public_filings, news_article, regulatory_filing, document_author_analysis, not_specified, not_known}
5. **Null Over Guess**: Return `null` when not explicitly stated
6. **No Computation**: Extract only stated values, no calculated metrics
7. **Partial Info**: Capture available data even when incomplete
8. **Conditional Sections**: Merger considerations only for `deal_type='merger'`, carveout considerations only for `deal_type='carve_out'`

**Schema Sections:**
- **document_metadata**: Document producer, type, company name, version info
- **company_overview**: Business description, management team, ownership structure
- **market_analysis**: TAM/SAM/SOM, competitive positioning, market trends
- **company_analysis**: Business model, competitive moat, customer base, unit economics
- **financial_profile**: Financial statements, revenue mix, margins, working capital
- **document_stated_upsides_and_growth_signals**: Growth drivers and opportunities
- **document_stated_risks**: Business, financial, operational, regulatory risks
- **valuation_and_capital_structure_signals**: Valuation metrics, cap table, funding history
- **merger_considerations**: Integration risks, synergies (conditional on deal_type)
- **carveout_considerations**: Standalone operations, service agreements (conditional on deal_type)
- **technology_and_it**: Technology stack, IT infrastructure, cybersecurity posture
- **esg**: Environmental, social, governance factors

### Document Types Supported

The system processes various investment document types:
- **Due Diligence Reports**: commercial_dd, tech_it_dd, financial_dd, operations_dd, legal_dd, regulatory_dd, esg_dd, hr_people_dd, tax_dd, insurance_dd, environmental_dd
- **Investment Documents**: investment_memorandum, information_memorandum_teaser, management_presentation, pitch_deck
- **Financial Reports**: financial_statement, annual_report, quarterly_report
- **Internal Documents**: internal_document, board_pack
- **Research and Analysis**: analyst_report, market_research_report, broker_research
- **Transcripts**: expert_call_transcript, management_call_transcript, customer_call_transcript, earnings_call_transcript, other_transcript

## Key Files

- `investment_analysis_schema_v3.json` - Investment analysis extraction schema with anti-hallucination policy
- `LlamaExtractJsonSchema (1).md` - Schema design documentation and best practices
- `src/extraction_review/config.py` - Configuration and schema definitions
- `src/extraction_review/process_file.py` - Main processing workflow
- `src/extraction_review/clients.py` - LlamaCloud client interactions
- `src/extraction_review/json_util.py` - JSON utility functions
- `src/extraction_review/metadata_workflow.py` - Metadata exposure for UI
- `configs/config.json` - Runtime configuration

## Technology Stack

- **LlamaAgents**: Main application framework (llamactl)
- **LlamaCloud**: Cloud platform for file storage and processing
- **LlamaExtract**: Structured data extraction with anti-hallucination policies
- **Pydantic**: Data validation and schema definition
- **Python 3**: Backend language (via hatch environment)

## Development Notes

- The application uses typed contexts and discriminated unions for configuration
- All main configuration is centralized in `src/extraction_review/config.py`
- The project supports both local development and deployment to LlamaCloud
- Extraction policy emphasizes factual accuracy and source attribution over interpretation
- High-volume sections (financial_statements, revenue_mix, unit_economics, etc.) capture values directly without cell-level quotes for practical reasons
- Data deduplication is handled by file hash in Agent Data storage

## Schema Development Best Practices

Based on the schema documentation (`LlamaExtractJsonSchema (1).md`):

- **Field Naming**: Use `document_stated_` prefix for interpretive fields to signal values must come from the document
- **Evidence Structure**: Wrap value-bearing fields in objects with `value`, `quotes`, and `attribution` properties
- **Quote Formatting**: Keep quotes compact (`'<verbatim> @ <location>'`) to stay within schema size limits
- **Selective Application**: Apply source-grounding where it adds value, skip for high-volume tabular data
- **Testing**: Test on adversarial documents (vague, incomplete, contradictory) to surface hallucination patterns
- **Explicit Instructions**: Use enforceable rules like "Return null when not explicitly stated" rather than vague directives like "Be accurate"
- **Quality Measurement**: Audit extraction quality by checking that quotes match the document, not just value accuracy