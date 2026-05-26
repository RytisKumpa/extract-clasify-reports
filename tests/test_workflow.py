from importlib.metadata import version

import pytest
from extraction_review.config import EXTRACTED_DATA_COLLECTION
from extraction_review.metadata_workflow import DISCRIMINATOR_FIELD, MetadataResponse
from extraction_review.metadata_workflow import workflow as metadata_workflow
from extraction_review.process_file import FileEvent, Status
from extraction_review.process_file import workflow as process_file_workflow
from llama_cloud_fake import FakeLlamaCloudServer
from workflows.events import StartEvent

INVESTMENT_DOCUMENT_TYPES = {
    "commercial_dd",
    "tech_it_dd",
    "financial_dd",
    "operations_dd",
    "legal_dd",
    "regulatory_dd",
    "esg_dd",
    "hr_people_dd",
    "tax_dd",
    "insurance_dd",
    "environmental_dd",
    "investment_memorandum",
    "information_memorandum_teaser",
    "management_presentation",
    "pitch_deck",
    "financial_statement",
    "annual_report",
    "quarterly_report",
    "internal_document",
    "board_pack",
    "analyst_report",
    "market_research_report",
    "broker_research",
    "expert_call_transcript",
    "management_call_transcript",
    "customer_call_transcript",
    "earnings_call_transcript",
    "other_transcript",
    "not_known",
    "other",
}

FAKE_HAS_CLASSIFY_V2 = version("llama-cloud-fake") >= "0.1.1"


@pytest.mark.asyncio
async def test_process_file_workflow(
    monkeypatch: pytest.MonkeyPatch,
    fake: FakeLlamaCloudServer,
) -> None:
    """Test that the investment due diligence workflow processes files correctly."""
    monkeypatch.setenv("LLAMA_CLOUD_API_KEY", "fake-api-key")
    file_id = fake.files.preload(path="tests/files/test.pdf")
    try:
        result = await process_file_workflow.run(start_event=FileEvent(file_id=file_id))
    except Exception:
        result = None
    assert result is not None
    assert isinstance(result, str)
    assert len(result) == 7


@pytest.mark.asyncio
@pytest.mark.skipif(
    not FAKE_HAS_CLASSIFY_V2,
    reason="llama-cloud-fake < 0.1.1 does not mock classify v2",
)
async def test_classify_v2_assigns_document_type(
    monkeypatch: pytest.MonkeyPatch,
    fake: FakeLlamaCloudServer,
) -> None:
    """Test that process_file workflow classifies investment documents correctly."""
    monkeypatch.setenv("LLAMA_CLOUD_API_KEY", "fake-api-key")
    file_id = fake.files.preload(path="tests/files/test.pdf")

    handler = process_file_workflow.run(start_event=FileEvent(file_id=file_id))
    classified_statuses: list[Status] = []
    async for event in handler.stream_events():
        if isinstance(event, Status):
            if event.level == "error":
                raise AssertionError(f"workflow errored: {event.message}")
            if event.message.startswith("Classified as "):
                classified_statuses.append(event)
    await handler

    # A real classify v2 result produces a "Classified as <type>" info status.
    # The fallback path (classification error -> "not_known") does *not* emit this.
    assert classified_statuses, (
        "expected a 'Classified as ...' status from a completed classify v2 job"
    )
    message = classified_statuses[-1].message

    # Check if the message contains any investment document type
    # Remove spaces and underscores for matching
    message_clean = message.replace(" ", "").replace("_", "")

    matched = None
    for doc_type in INVESTMENT_DOCUMENT_TYPES:
        doc_type_clean = doc_type.replace("_", "")
        if f"CLASSIFIEDAS{doc_type_clean}" in message_clean.upper():
            matched = doc_type
            break

    assert matched is not None, f"unexpected classification status: {message}"


@pytest.mark.asyncio
async def test_metadata_workflow() -> None:
    """Test that the metadata workflow returns investment analysis schema."""
    result = await metadata_workflow.run(start_event=StartEvent())
    assert isinstance(result, MetadataResponse)
    assert result.extracted_data_collection == EXTRACTED_DATA_COLLECTION
    assert result.discriminator_field == DISCRIMINATOR_FIELD

    # Should have investment_analysis schema only
    assert set(result.schemas.keys()) == {"investment_analysis"}

    # JSON schema should have the discriminator field
    assert DISCRIMINATOR_FIELD in result.json_schema.get("properties", {})


@pytest.mark.asyncio
async def test_json_util_data_extraction() -> None:
    """Test that json_util can handle investment data structures."""
    from extraction_review.json_util import get_data_from_agent_data

    # Test with nested data structure (what LlamaCloud Agent Data might return)
    nested_data = {
        "data": {
            "data": {
                "document_metadata": {"company_name": "Test Company", "document_type": "investment_memorandum"},
                "company_overview": {"business_description": {"value": "Test business"}}
            },
            "metadata": {"classification_confidence": 0.95},
            "file_name": "test.pdf",
            "field_metadata": {}
        }
    }

    extracted = get_data_from_agent_data(nested_data)
    assert extracted == nested_data["data"]
    assert "document_metadata" in extracted

    # Test with direct data structure
    direct_data = {
        "document_metadata": {"company_name": "Test Company", "document_type": "investment_memorandum"},
        "company_overview": {"business_description": {"value": "Test business"}}
    }

    extracted = get_data_from_agent_data(direct_data)
    assert extracted == direct_data


@pytest.mark.asyncio
async def test_investment_schema_structure() -> None:
    """Test that the investment analysis schema has the expected structure."""
    from extraction_review.config import InvestmentAnalysisSchema, DOCUMENT_SCHEMAS

    # Verify schema mapping
    assert "investment_analysis" in DOCUMENT_SCHEMAS
    assert DOCUMENT_SCHEMAS["investment_analysis"] == InvestmentAnalysisSchema

    # Verify required field
    schema = InvestmentAnalysisSchema.model_json_schema()
    assert "required" in schema
    assert "document_metadata" in schema["required"]

    # Verify main sections exist
    properties = schema["properties"]
    expected_sections = [
        "document_metadata",
        "company_overview",
        "market_analysis",
        "company_analysis",
        "financial_profile",
        "document_stated_upsides_and_growth_signals",
        "document_stated_risks",
        "valuation_and_capital_structure_signals",
        "merger_considerations",
        "carveout_considerations",
        "technology_and_it",
        "esg"
    ]

    for section in expected_sections:
        assert section in properties, f"Missing expected section: {section}"


@pytest.mark.asyncio
async def test_source_grounded_value_structure() -> None:
    """Test that source-grounded value structure is properly defined."""
    from extraction_review.config import SourceGroundedValue

    # Test creating a source-grounded value
    sg_value = SourceGroundedValue(
        value="Test value",
        quotes=["Quote 1 @ page 1", "Quote 2 @ page 2"],
        attribution="company_management: Executive Interview"
    )

    assert sg_value.value == "Test value"
    assert len(sg_value.quotes) == 2
    assert sg_value.attribution == "company_management: Executive Interview"

    # Test with optional fields
    sg_value_minimal = SourceGroundedValue(value="Minimal test")
    assert sg_value_minimal.quotes == []
    assert sg_value_minimal.attribution is None


@pytest.mark.asyncio
async def test_array_item_models() -> None:
    """Test that array item models are properly defined."""
    from extraction_review.config import (
        CompetitiveLandscapeItem,
        CompetitiveAdvantageItem,
        GoToMarketStrategyItem,
        MoatComponentItem,
        RevenueBreakdownItem,
        DebtStructureItem,
        EquityStructureItem,
        FundingHistoryItem,
        SecurityMeasureItem,
        VulnerabilityItem
    )

    # Test CompetitiveLandscapeItem
    competitor = CompetitiveLandscapeItem(
        competitor_name="Competitor A",
        market_position="#1 market leader",
        market_share="25"
    )
    assert competitor.competitor_name == "Competitor A"

    # Test GoToMarketStrategyItem
    strategy = GoToMarketStrategyItem(
        channel="Direct Sales",
        description="Direct sales to enterprise customers",
        effectiveness="High conversion rate"
    )
    assert strategy.channel == "Direct Sales"

    # Test RevenueBreakdownItem
    revenue = RevenueBreakdownItem(
        category="Americas",
        amount="44",
        growth_rate="15%",
        description="Revenue from Americas region"
    )
    assert revenue.category == "Americas"
    assert revenue.amount == "44"

    # Test with optional fields
    minimal_revenue = RevenueBreakdownItem(category="EMEA")
    assert minimal_revenue.amount is None
    assert minimal_revenue.growth_rate is None