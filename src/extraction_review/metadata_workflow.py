from typing import Annotated, Any
import logging

from llama_cloud.types.configuration_response import ExtractV2Parameters
from workflows import Workflow, step
from workflows.events import StartEvent, StopEvent
from workflows.resource import Resource, ResourceConfig

from .clients import get_llama_cloud_client, project_id
from .config import EXTRACTED_DATA_COLLECTION, ExtractConfig, create_union_schema, INVESTMENT_DOCUMENT_TYPES

logger = logging.getLogger(__name__)

DISCRIMINATOR_FIELD = "document_type"


class MetadataResponse(StopEvent):
    json_schema: dict[str, Any]
    schemas: dict[str, dict[str, Any]]
    discriminator_field: str
    extracted_data_collection: str


async def _resolve_schema(extract_config: ExtractConfig) -> dict[str, Any]:
    """Return the data schema for an extract config, pulling from the platform if saved."""
    if extract_config.configuration_id:
        client = get_llama_cloud_client()
        config_resp = await client.configurations.retrieve(
            extract_config.configuration_id,
            project_id=project_id,
        )
        params = config_resp.parameters
        if not isinstance(params, ExtractV2Parameters):
            raise ValueError(
                f"Configuration {extract_config.configuration_id} is not extract_v2"
            )
        return dict(params.data_schema)
    return dict(extract_config.data_schema)


async def get_presentation_schema(
    extract_investment: Annotated[
        ExtractConfig,
        ResourceConfig(
            config_file="configs/config.json",
            path_selector="extract-investment",
            label="Investment Analysis Extraction",
        ),
    ],
) -> dict[str, Any]:
    """Get presentation schema for all document categories.

    Returns a mapping of document types to their appropriate schemas for the UI.
    """
    import json
    from pathlib import Path

    from extraction_review.config import (
        DOCUMENT_TYPE_TO_SCHEMA,
        INVESTMENT_DOCUMENT_TYPES,
        SCHEMA_FILE_PATHS,
    )

    # Load all category-specific schemas
    category_schemas = {}
    for category, schema_path in SCHEMA_FILE_PATHS.items():
        # Special handling for Pydantic models
        if category == "investment_doc":
            try:
                from extraction_review.investment_doc_schemas import InvestmentDocumentSchema
                category_schemas[category] = InvestmentDocumentSchema.model_json_schema()
                logger.info(f"Using Pydantic model for investment_doc schema")
                continue
            except ImportError:
                logger.warning("Could not import InvestmentDocumentSchema, falling back to JSON")

        if category == "due_diligence":
            try:
                from extraction_review.due_diligence_schemas import DueDiligenceSchema
                category_schemas[category] = DueDiligenceSchema.model_json_schema()
                logger.info(f"Using Pydantic model for due_diligence schema")
                continue
            except ImportError:
                logger.warning("Could not import DueDiligenceSchema, falling back to JSON")

        if category == "financial_report":
            try:
                from extraction_review.financial_report_schemas import FinancialReportSchema
                category_schemas[category] = FinancialReportSchema.model_json_schema()
                logger.info(f"Using Pydantic model for financial_report schema")
                continue
            except ImportError:
                logger.warning("Could not import FinancialReportSchema, falling back to JSON")

        if category == "generic":
            try:
                from extraction_review.generic_schemas import GenericDocumentSchema
                category_schemas[category] = GenericDocumentSchema.model_json_schema()
                logger.info(f"Using Pydantic model for generic schema")
                continue
            except ImportError:
                logger.warning("Could not import GenericDocumentSchema, falling back to JSON")

        schema_file = Path(schema_path)
        if schema_file.exists():
            with open(schema_file) as f:
                category_schemas[category] = json.load(f)
        else:
            # Fallback to empty schema if file doesn't exist
            category_schemas[category] = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {},
                "required": [],
            }

    # Map each document type to its category schema
    schemas = {}
    for doc_type in INVESTMENT_DOCUMENT_TYPES:
        # Get the schema category for this document type
        schema_category = DOCUMENT_TYPE_TO_SCHEMA.get(doc_type, "generic")
        schema = category_schemas.get(schema_category, category_schemas["generic"])

        schemas[doc_type] = schema
        # Also add uppercase version for UI compatibility
        schemas[doc_type.upper()] = schema

    # Use the generic schema as the default JSON schema
    default_schema = category_schemas.get("generic", {})

    return {
        "json_schema": default_schema,
        "schemas": schemas,
        "discriminator_field": DISCRIMINATOR_FIELD,
    }


class MetadataWorkflow(Workflow):
    """Provide extraction schema and configuration to the workflow editor."""

    @step
    async def get_metadata(
        self,
        _: StartEvent,
        presentation: Annotated[dict[str, Any], Resource(get_presentation_schema)],
    ) -> MetadataResponse:
        """Return the data schemas and storage settings for the review interface."""
        return MetadataResponse(
            json_schema=presentation["json_schema"],
            schemas=presentation["schemas"],
            discriminator_field=presentation["discriminator_field"],
            extracted_data_collection=EXTRACTED_DATA_COLLECTION,
        )


workflow = MetadataWorkflow(timeout=None)