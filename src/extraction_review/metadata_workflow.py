from typing import Annotated, Any

from llama_cloud.types.configuration_response import ExtractV2Parameters
from workflows import Workflow, step
from workflows.events import StartEvent, StopEvent
from workflows.resource import Resource, ResourceConfig

from .clients import get_llama_cloud_client, project_id
from .config import EXTRACTED_DATA_COLLECTION, ExtractConfig, create_union_schema

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
    """Get presentation schema for investment analysis.

    Returns the investment analysis schema with proper structure for UI.
    """
    investment_schema = await _resolve_schema(extract_investment)

    # For investment analysis, we use a single comprehensive schema
    # but maintain the union structure for compatibility
    schemas = {
        "investment_analysis": investment_schema,
    }

    # Don't create a union for single schema - use it directly
    return {
        "json_schema": investment_schema,
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