import asyncio
import json
import logging
from typing import Annotated, Any, Literal

from llama_cloud import AsyncLlamaCloud
from llama_cloud.types.beta.extracted_data import ExtractedData, InvalidExtractionData
from llama_cloud.types.configuration_response import ExtractV2Parameters
from pydantic import BaseModel
from workflows import Context, Workflow, step
from workflows.events import Event, StartEvent, StopEvent
from workflows.resource import Resource, ResourceConfig

from .clients import agent_name, get_llama_cloud_client, project_id
from .config import (
    EXTRACTED_DATA_COLLECTION,
    ClassifyConfig,
    ExtractConfig,
    get_extraction_schema,
)

logger = logging.getLogger(__name__)

DISCRIMINATOR_FIELD = "document_type"

CLASSIFY_POLL_INTERVAL_S = 1.0
CLASSIFY_POLL_MAX_S = 300.0


class FileEvent(StartEvent):
    file_id: str
    file_hash: str | None = None


class DocumentClassifiedEvent(Event):
    document_type: str
    confidence: float | None = None
    reasoning: str | None = None


class Status(Event):
    level: Literal["info", "warning", "error"]
    message: str


class ExtractJobStartedEvent(Event):
    pass


class ExtractedEvent(Event):
    data: ExtractedData


class ExtractedInvalidEvent(Event):
    data: ExtractedData[dict[str, Any]]


class ExtractionState(BaseModel):
    file_id: str | None = None
    filename: str | None = None
    file_hash: str | None = None
    extract_job_id: str | None = None
    document_type: str | None = None
    classification_confidence: float | None = None
    classification_reasoning: str | None = None


async def _wait_for_classify(client: AsyncLlamaCloud, job_id: str) -> Any:
    """Poll `classify.get` until the job reaches a terminal state."""
    elapsed = 0.0
    while elapsed < CLASSIFY_POLL_MAX_S:
        job = await client.classify.get(job_id, project_id=project_id)
        if job.status in ("COMPLETED", "FAILED"):
            return job
        await asyncio.sleep(CLASSIFY_POLL_INTERVAL_S)
        elapsed += CLASSIFY_POLL_INTERVAL_S
    raise TimeoutError(
        f"Classify job {job_id} did not complete within {CLASSIFY_POLL_MAX_S}s"
    )


class ProcessFileWorkflow(Workflow):
    """Classify an investment document and extract structured investment due diligence information."""

    @step()
    async def start_extraction(
        self,
        event: FileEvent,
        ctx: Context[ExtractionState],
        llama_cloud_client: Annotated[
            AsyncLlamaCloud, Resource(get_llama_cloud_client)
        ],
        extract_config: Annotated[
            ExtractConfig,
            ResourceConfig(
                config_file="configs/config.json",
                path_selector="extract-investment",
                label="Investment Analysis Extraction",
                description="Comprehensive investment due diligence extraction with anti-hallucination policy",
            ),
        ],
    ) -> ExtractJobStartedEvent:
        """Start extraction job for the investment document."""
        file_id = event.file_id
        logger.info(f"Running file {file_id}")

        try:
            file_metadata = None
            async for f in llama_cloud_client.files.list(file_ids=[file_id]):
                file_metadata = f
                break
            if file_metadata is None:
                raise ValueError(f"File {file_id} not found")
            filename = file_metadata.name
        except Exception as e:
            logger.error(f"Error fetching file metadata {file_id}: {e}", exc_info=True)
            ctx.write_event_to_stream(
                Status(
                    level="error",
                    message=f"Error fetching file metadata {file_id}: {e}",
                )
            )
            raise e

        logger.info(f"Extracting investment due diligence data from file {filename}")
        ctx.write_event_to_stream(
            Status(level="info", message=f"Extracting investment data from file {filename}")
        )

        if extract_config.configuration_id:
            extract_job = await llama_cloud_client.extract.create(
                file_input=file_id,
                configuration_id=extract_config.configuration_id,
                project_id=project_id,
            )
        else:
            extract_job = await llama_cloud_client.extract.create(
                file_input=file_id,
                configuration=extract_config.model_dump(
                    exclude={"configuration_id", "product_type"},
                    exclude_none=True,
                ),
                project_id=project_id,
            )

        file_hash = event.file_hash or file_metadata.external_file_id

        async with ctx.store.edit_state() as state:
            state.file_id = file_id
            state.filename = filename
            state.file_hash = file_hash
            state.extract_job_id = extract_job.id

        return ExtractJobStartedEvent()

    @step()
    async def classify_document(
        self,
        event: ExtractJobStartedEvent,
        ctx: Context[ExtractionState],
        llama_cloud_client: Annotated[
            AsyncLlamaCloud, Resource(get_llama_cloud_client)
        ],
        classify_config: Annotated[
            ClassifyConfig,
            ResourceConfig(
                config_file="configs/config.json",
                path_selector="classify",
                label="Investment Document Classification",
                description="Rules for classifying investment document types (DD reports, IMs, pitch decks, etc.)",
            ),
        ],
    ) -> DocumentClassifiedEvent:
        """Classify the investment document type in parallel with extraction."""
        state = await ctx.store.get_state()
        if state.file_id is None or state.filename is None:
            raise ValueError("File ID or filename is not set")

        try:
            logger.info(f"Classifying investment document {state.filename}")
            ctx.write_event_to_stream(
                Status(level="info", message=f"Classifying document type for {state.filename}")
            )

            if classify_config.configuration_id:
                classify_job = await llama_cloud_client.classify.create(
                    file_input=state.file_id,
                    configuration_id=classify_config.configuration_id,
                    project_id=project_id,
                )
            else:
                classify_job = await llama_cloud_client.classify.create(
                    file_input=state.file_id,
                    configuration=classify_config.model_dump(
                        exclude={"configuration_id", "product_type"},
                        exclude_none=True,
                    ),
                    project_id=project_id,
                )

            completed = await _wait_for_classify(llama_cloud_client, classify_job.id)

            if completed.status == "FAILED" or completed.result is None:
                logger.warning(
                    f"Classification did not resolve for {state.filename}, defaulting to 'not_known'"
                )
                ctx.write_event_to_stream(
                    Status(
                        level="warning",
                        message="Document classification uncertain, using default schema",
                    )
                )
                async with ctx.store.edit_state() as state:
                    state.document_type = "not_known"
                return DocumentClassifiedEvent(document_type="not_known")

            result = completed.result
            document_type = result.type or "not_known"
            confidence = result.confidence
            reasoning = result.reasoning

            logger.info(
                f"Classified {state.filename} as {document_type} "
                f"(confidence: {confidence}, reasoning: {reasoning})"
            )
            ctx.write_event_to_stream(
                Status(
                    level="info",
                    message=f"Classified as {document_type}",
                )
            )

            async with ctx.store.edit_state() as state:
                state.document_type = document_type
                state.classification_confidence = confidence
                state.classification_reasoning = reasoning

            return DocumentClassifiedEvent(
                document_type=document_type,
                confidence=confidence,
                reasoning=reasoning,
            )

        except Exception as e:
            logger.error(f"Error classifying document {state.filename}: {e}", exc_info=True)
            ctx.write_event_to_stream(
                Status(
                    level="warning",
                    message=f"Document classification failed, using default schema: {e}",
                )
            )
            async with ctx.store.edit_state() as state:
                state.document_type = "not_known"
            return DocumentClassifiedEvent(document_type="not_known")

    @step()
    async def complete_extraction(
        self,
        event: DocumentClassifiedEvent,
        ctx: Context[ExtractionState],
        llama_cloud_client: Annotated[
            AsyncLlamaCloud, Resource(get_llama_cloud_client)
        ],
        extract_investment: Annotated[
            ExtractConfig,
            ResourceConfig(
                config_file="configs/config.json",
                path_selector="extract-investment",
                label="Investment Analysis Extraction",
            ),
        ],
    ) -> StopEvent:
        """Wait for extraction to complete, validate results, and save for review."""
        state = await ctx.store.get_state()
        if state.extract_job_id is None:
            raise ValueError("Job ID cannot be null when waiting for its completion")

        document_type = state.document_type or "not_known"
        extract_config = extract_investment

        await llama_cloud_client.extract.wait_for_completion(
            state.extract_job_id,
            project_id=project_id,
        )
        job = await llama_cloud_client.extract.get(
            state.extract_job_id,
            expand=["extract_metadata"],
            project_id=project_id,
        )

        extracted_event: ExtractedEvent | ExtractedInvalidEvent
        try:
            logger.info(
                f"Extracted data: {json.dumps(job.model_dump(mode='json'), indent=2, default=str)}"
            )
            if extract_config.configuration_id:
                config_resp = await llama_cloud_client.configurations.retrieve(
                    extract_config.configuration_id,
                    project_id=project_id,
                )
                params = config_resp.parameters
                if not isinstance(params, ExtractV2Parameters):
                    raise ValueError(
                        f"Configuration {extract_config.configuration_id} is not extract_v2"
                    )
                schema_class = get_extraction_schema(
                    dict(params.data_schema),
                    discriminator_field=DISCRIMINATOR_FIELD,
                    discriminator_value=document_type,
                )
            else:
                schema_class = get_extraction_schema(
                    dict(extract_config.data_schema),
                    discriminator_field=DISCRIMINATOR_FIELD,
                    discriminator_value=document_type,
                )

            data = ExtractedData.from_extract_job(
                job=job,
                schema=schema_class,
                file_name=state.filename,
                file_id=state.file_id,
                file_hash=state.file_hash,
            )
            if data.metadata is None:
                data.metadata = {}
            data.metadata["document_type"] = document_type
            data.metadata["classification_confidence"] = state.classification_confidence
            data.metadata["classification_reasoning"] = state.classification_reasoning
            extracted_event = ExtractedEvent(data=data)
        except InvalidExtractionData as e:
            logger.error(f"Error validating extracted data: {e}", exc_info=True)
            extracted_event = ExtractedInvalidEvent(data=e.invalid_item)
        except Exception as e:
            logger.error(
                f"Error extracting data from file {state.filename}: {e}", exc_info=True
            )
            ctx.write_event_to_stream(
                Status(
                    level="error",
                    message=f"Error extracting investment data from file {state.filename}: {e}",
                )
            )
            raise e

        ctx.write_event_to_stream(extracted_event)

        # Flatten the data structure for Agent Data storage
        # ExtractedData has nested structure: data.data contains actual content
        extracted_data = extracted_event.data
        data_dict = extracted_data.model_dump()

        # If data_dict has nested data.data structure, flatten it
        if isinstance(data_dict, dict) and "data" in data_dict:
            data_dict_content = data_dict["data"]
            if isinstance(data_dict_content, dict) and "data" in data_dict_content:
                # Flatten the structure: move content from data.data to top level
                content = data_dict_content["data"]
                metadata = data_dict_content.get("metadata", {})
                field_metadata = data_dict_content.get("field_metadata", {})

                # Create flattened structure
                flattened_dict = {
                    "data": content,
                    "metadata": {
                        **metadata,
                        "document_type": document_type,
                        "classification_confidence": state.classification_confidence,
                        "classification_reasoning": state.classification_reasoning,
                    },
                    "file_name": state.filename,
                    "file_id": state.file_id,
                    "file_hash": state.file_hash,
                    "field_metadata": field_metadata,
                    "overall_confidence": data_dict_content.get("overall_confidence"),
                }
                data_dict = flattened_dict

        if data_dict.get("file_hash") is not None:
            delete_result = await llama_cloud_client.beta.agent_data.delete_by_query(
                deployment_name=agent_name or "_public",
                collection=EXTRACTED_DATA_COLLECTION,
                filter={
                    "file_hash": {
                        "eq": data_dict["file_hash"],
                    },
                },
            )
            if delete_result.deleted_count > 0:
                logger.info(
                    f"Removed {delete_result.deleted_count} existing record(s) "
                    f"for file {data_dict.get('file_name', '')}"
                )
        item = await llama_cloud_client.beta.agent_data.create(
            data=data_dict,
            deployment_name=agent_name or "_public",
            collection=EXTRACTED_DATA_COLLECTION,
        )
        logger.info(
            f"Recorded investment due diligence data for file {data_dict.get('file_name', '')}"
        )
        ctx.write_event_to_stream(
            Status(
                level="info",
                message=f"Recorded investment data for file {data_dict.get('file_name', '')}",
            )
        )
        return StopEvent(result=item.id)


workflow = ProcessFileWorkflow(timeout=None)

if __name__ == "__main__":
    from pathlib import Path

    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    async def main():
        file = await get_llama_cloud_client().files.create(
            file=Path("test.pdf").open("rb"),
            purpose="extract",
        )
        await workflow.run(start_event=FileEvent(file_id=file.id))

    asyncio.run(main())