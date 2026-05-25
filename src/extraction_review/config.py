"""
Configuration for the investment due diligence extraction application.

Configuration is loaded from configs/config.json via ResourceConfig.
Each top-level key in config.json maps to an SDK product-configuration type:
the discriminated union members returned by `client.configurations.retrieve`.
Each template-side subclass adds an optional `configuration_id` so a key
can either carry an inline snapshot OR point at a saved platform config.
"""

import logging

from llama_cloud.types.beta.split_category import SplitCategory
from llama_cloud.types.classify_v2_parameters import ClassifyV2Parameters, Rule
from llama_cloud.types.extract_v2_parameters import ExtractV2Parameters
from llama_cloud.types.parse_v2_parameters import ParseV2Parameters
from llama_cloud.types.split_v1_parameters import SplitV1Parameters
from pydantic import BaseModel, Field

from .json_util import create_union_schema as create_union_schema
from .json_util import get_extraction_schema as get_extraction_schema

logger = logging.getLogger(__name__)


# The name of the collection to use for storing extracted data.
EXTRACTED_DATA_COLLECTION: str = "sec-filing-extraction"

# Investment Document Classification Types
INVESTMENT_DOCUMENT_TYPES = [
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
]


# Source-grounded value structure for anti-hallucination
class SourceGroundedValue(BaseModel):
    """Value with source grounding including quotes and attribution."""
    value: str = Field(description="The extracted value from the document")
    quotes: list[str] = Field(
        default=[],
        description="Array of supporting quotes from the document, max 5. Format: '<verbatim quote ≤50 words> @ <location>'"
    )
    attribution: str | None = Field(
        default=None,
        description="Source attribution. Format: '<source_type>: <source_name>'. "
        "source_type ∈ {company_management, company_financials_audited, company_financials_unaudited, "
        "third_party_research, industry_expert_interview, public_filings, news_article, "
        "regulatory_filing, document_author_analysis, not_specified, not_known}"
    )


# Document Metadata section
class DocumentMetadata(BaseModel):
    """Metadata describing the source document itself."""
    company_name: str = Field(description="Name of the company being analysed in the document")
    document_type: str = Field(
        description="Type of document (e.g., commercial_dd, investment_memorandum, pitch_deck, etc.)"
    )
    document_producer: str | None = Field(
        default=None,
        description="Name of the firm or team that produced the document (e.g. 'PwC', 'Goldman Sachs', 'in-house strategy team')"
    )
    producer_type: str | None = Field(
        default=None,
        description="Category of document producer (e.g., investment_bank, consulting_firm, company_internal, etc.)"
    )
    dd_side: str | None = Field(
        default=None,
        description="For DD documents only: whether vendor or buyside"
    )


# Competitive landscape item
class CompetitiveLandscapeItem(BaseModel):
    """Individual competitor or market position item."""
    competitor_name: str = Field(description="Name of competitor or market position")
    market_position: str | None = Field(default=None, description="Market position or description")
    market_share: str | None = Field(default=None, description="Market share percentage or description")


# Competitive advantage item
class CompetitiveAdvantageItem(BaseModel):
    """Individual competitive advantage item."""
    advantage_type: str = Field(description="Type of competitive advantage")
    description: str = Field(description="Description of the competitive advantage")
    sustainability: str | None = Field(default=None, description="Sustainability assessment")


# Go-to-market strategy item
class GoToMarketStrategyItem(BaseModel):
    """Individual go-to-market strategy item."""
    channel: str = Field(description="Sales or distribution channel")
    description: str = Field(description="Description of the channel strategy")
    effectiveness: str | None = Field(default=None, description="Channel effectiveness metrics")


# Moat component item
class MoatComponentItem(BaseModel):
    """Individual competitive moat component."""
    component_type: str = Field(description="Type of moat component")
    description: str = Field(description="Description of the moat component")
    strength: str | None = Field(default=None, description="Assessment of moat strength")


# Revenue breakdown item
class RevenueBreakdownItem(BaseModel):
    """Individual revenue breakdown item."""
    category: str = Field(description="Revenue category (product, geography, customer segment)")
    amount: str | None = Field(default=None, description="Revenue amount or percentage")
    growth_rate: str | None = Field(default=None, description="Growth rate for the category")
    description: str | None = Field(default=None, description="Additional details about the category")


# Debt structure item
class DebtStructureItem(BaseModel):
    """Individual debt structure item."""
    debt_type: str = Field(description="Type of debt (senior, mezzanine, convertible, etc.)")
    amount: str | None = Field(default=None, description="Debt amount")
    interest_rate: str | None = Field(default=None, description="Interest rate or range")
    maturity: str | None = Field(default=None, description="Maturity date or period")
    covenants: str | None = Field(default=None, description="Key debt covenants or restrictions")


# Equity structure item
class EquityStructureItem(BaseModel):
    """Individual equity structure item."""
    shareholder_type: str = Field(description="Type of shareholder (founder, VC, PE, etc.)")
    ownership_pct: str | None = Field(default=None, description="Ownership percentage")
    shares: str | None = Field(default=None, description="Number of shares or details")
    rights: str | None = Field(default=None, description="Special rights or preferences")


# Funding history item
class FundingHistoryItem(BaseModel):
    """Individual funding history item."""
    round_type: str = Field(description="Type of funding round (Series A, B, C, etc.)")
    amount: str | None = Field(default=None, description="Funding amount")
    date: str | None = Field(default=None, description="Funding date")
    investors: str | None = Field(default=None, description="Key investors in the round")
    valuation: str | None = Field(default=None, description="Post-money valuation")


# Security measure item
class SecurityMeasureItem(BaseModel):
    """Individual cybersecurity measure."""
    measure_type: str = Field(description="Type of security measure")
    description: str = Field(description="Description of the security measure")
    implementation_status: str | None = Field(default=None, description="Implementation status")


# Vulnerability item
class VulnerabilityItem(BaseModel):
    """Individual cybersecurity vulnerability."""
    vulnerability_type: str = Field(description="Type of vulnerability")
    severity: str | None = Field(default=None, description="Severity assessment")
    description: str = Field(description="Description of the vulnerability")
    mitigation_status: str | None = Field(default=None, description="Current mitigation status")


# Company Overview section
class CompanyOverview(BaseModel):
    """Company information including business description and management team."""
    business_description: SourceGroundedValue | None = Field(
        default=None,
        description="Description of the company's business model, products/services, and operations"
    )
    management_team: dict | None = Field(
        default=None,
        description="Management team information including key executives, board composition, and assessment"
    )


# Market Analysis section
class MarketAnalysis(BaseModel):
    """Market analysis including TAM/SAM/SOM and competitive positioning."""
    market_size: dict | None = Field(
        default=None,
        description="Total Addressable Market, Serviceable Addressable Market, Serviceable Obtainable Market"
    )
    competitive_positioning: dict | None = Field(
        default=None,
        description="Competitive position including landscape and advantages"
    )
    competitive_landscape: list[CompetitiveLandscapeItem] | None = Field(
        default=None,
        description="Array of competitors and market positions"
    )
    competitive_advantages: list[CompetitiveAdvantageItem] | None = Field(
        default=None,
        description="Array of competitive advantages"
    )


# Company Analysis section
class CompanyAnalysis(BaseModel):
    """Company analysis including business model and competitive moat."""
    business_model: dict | None = Field(
        default=None,
        description="Business model, revenue model, value proposition"
    )
    go_to_market_strategy: list[GoToMarketStrategyItem] | None = Field(
        default=None,
        description="Array of go-to-market strategies and channels"
    )
    competitive_moat: dict | None = Field(
        default=None,
        description="Competitive moat and sustainability assessment"
    )
    moat_components: list[MoatComponentItem] | None = Field(
        default=None,
        description="Array of competitive moat components"
    )


# Financial Profile section
class FinancialProfile(BaseModel):
    """Financial profile including statements, revenue mix, and profitability."""
    financial_statements: dict | None = Field(
        default=None,
        description="Historical financial statements including balance sheet, income statement, and cash flow"
    )
    revenue_mix: dict | None = Field(
        default=None,
        description="Revenue breakdown analysis"
    )
    by_product: list[RevenueBreakdownItem] | None = Field(
        default=None,
        description="Array of revenue breakdown by product"
    )
    by_geography: list[RevenueBreakdownItem] | None = Field(
        default=None,
        description="Array of revenue breakdown by geography"
    )
    by_customer_segment: list[RevenueBreakdownItem] | None = Field(
        default=None,
        description="Array of revenue breakdown by customer segment"
    )
    profitability_metrics: dict | None = Field(
        default=None,
        description="Key profitability metrics including gross margin, operating margin, EBITDA margin, net margin"
    )


# Upsides and Growth Signals section
class UpsidesAndGrowthSignals(BaseModel):
    """Document-stated upsides and growth signals."""
    growth_drivers: list[SourceGroundedValue] | None = Field(
        default=None,
        description="Key drivers of business growth and expansion opportunities"
    )
    market_opportunities: list[SourceGroundedValue] | None = Field(
        default=None,
        description="Market opportunities and expansion potential"
    )


# Risks section
class Risks(BaseModel):
    """Document-stated risks across business, financial, operational, and regulatory categories."""
    business_risks: list[SourceGroundedValue] | None = Field(
        default=None,
        description="Business-related risks and challenges"
    )
    financial_risks: list[SourceGroundedValue] | None = Field(
        default=None,
        description="Financial risks including liquidity, leverage, and market risks"
    )
    regulatory_risks: list[SourceGroundedValue] | None = Field(
        default=None,
        description="Regulatory and compliance risks"
    )


# Valuation and Capital Structure section
class ValuationAndCapitalStructure(BaseModel):
    """Valuation metrics and capital structure analysis."""
    valuation_metrics: dict | None = Field(
        default=None,
        description="Valuation metrics including enterprise value, equity value, and multiples"
    )
    capital_structure: dict | None = Field(
        default=None,
        description="Capital structure including debt, equity, and funding history"
    )
    debt_structure: list[DebtStructureItem] | None = Field(
        default=None,
        description="Array of debt structure items"
    )
    equity_structure: list[EquityStructureItem] | None = Field(
        default=None,
        description="Array of equity structure items"
    )
    funding_history: list[FundingHistoryItem] | None = Field(
        default=None,
        description="Array of funding history items"
    )


# Merger Considerations section (conditional)
class MergerConsiderations(BaseModel):
    """Merger-specific considerations (conditional on deal type)."""
    integration_risks: list[SourceGroundedValue] | None = Field(
        default=None,
        description="Integration risks and challenges for merger scenarios"
    )
    synergies: list[SourceGroundedValue] | None = Field(
        default=None,
        description="Expected synergies and value creation from merger"
    )


# Carveout Considerations section (conditional)
class CarveoutConsiderations(BaseModel):
    """Carveout-specific considerations (conditional on deal type)."""
    standalone_operations: list[SourceGroundedValue] | None = Field(
        default=None,
        description="Requirements and challenges for standalone operations"
    )
    service_agreements: list[SourceGroundedValue] | None = Field(
        default=None,
        description="Transition service agreements and shared services"
    )


# Technology and IT section
class TechnologyAndIT(BaseModel):
    """Technology and IT analysis including stack and cybersecurity."""
    technology_stack: list[SourceGroundedValue] | None = Field(
        default=None,
        description="Technology stack and technical infrastructure"
    )
    cybersecurity_posture: dict | None = Field(
        default=None,
        description="Cybersecurity posture including security measures, vulnerabilities, and compliance"
    )
    security_measures: list[SecurityMeasureItem] | None = Field(
        default=None,
        description="Array of cybersecurity measures"
    )
    vulnerabilities: list[VulnerabilityItem] | None = Field(
        default=None,
        description="Array of cybersecurity vulnerabilities"
    )


# ESG section
class ESG(BaseModel):
    """Environmental, Social, and Governance analysis."""
    environmental_factors: list[SourceGroundedValue] | None = Field(
        default=None,
        description="Environmental factors and sustainability practices"
    )
    social_factors: list[SourceGroundedValue] | None = Field(
        default=None,
        description="Social factors and impact analysis"
    )
    governance_factors: list[SourceGroundedValue] | None = Field(
        default=None,
        description="Governance structure and practices"
    )


# Main Investment Analysis Schema
class InvestmentAnalysisSchema(BaseModel):
    """
    Comprehensive investment due diligence extraction schema.

    Follows strict anti-hallucination policy with source grounding:
    1. Extract only what the document STATES - do not assess or score
    2. Source-ground most value-bearing fields with {value, quotes, attribution} structure
    3. Use quotes format: '<verbatim quote ≤50 words> @ <location>'
    4. Attribution format: '<source_type>: <source_name>'
    5. Return null when not explicitly stated - never invent values
    6. Do not compute ratios or derived values - capture only stated figures
    7. For partial information, capture what is available rather than null
    8. Conditional sections apply based on deal_type and document_type
    """

    document_metadata: DocumentMetadata = Field(description="Document metadata including company name and document type")
    company_overview: CompanyOverview | None = Field(default=None, description="Company information and business overview")
    market_analysis: MarketAnalysis | None = Field(default=None, description="Market analysis and competitive positioning")
    company_analysis: CompanyAnalysis | None = Field(default=None, description="Company analysis including business model and competitive moat")
    financial_profile: FinancialProfile | None = Field(default=None, description="Financial profile including statements and profitability")
    document_stated_upsides_and_growth_signals: UpsidesAndGrowthSignals | None = Field(default=None, description="Document-stated growth drivers and opportunities")
    document_stated_risks: Risks | None = Field(default=None, description="Document-stated risks across multiple categories")
    valuation_and_capital_structure_signals: ValuationAndCapitalStructure | None = Field(default=None, description="Valuation metrics and capital structure analysis")
    merger_considerations: MergerConsiderations | None = Field(default=None, description="Merger considerations (conditional on deal_type)")
    carveout_considerations: CarveoutConsiderations | None = Field(default=None, description="Carveout considerations (conditional on deal_type)")
    technology_and_it: TechnologyAndIT | None = Field(default=None, description="Technology and IT analysis")
    esg: ESG | None = Field(default=None, description="Environmental, Social, and Governance analysis")


# Default schema for backward compatibility - now uses investment analysis
class ExtractionSchema(InvestmentAnalysisSchema):
    """Default extraction schema - uses investment analysis structure for backward compatibility"""
    pass


# Mapping of document types to their schemas (unified approach for investment analysis)
DOCUMENT_SCHEMAS = {
    "investment_analysis": InvestmentAnalysisSchema,
}


class ExtractConfig(ExtractV2Parameters):
    """Extract product configuration.

    Inherits the SDK `ExtractV2Parameters` shape. Set `configuration_id`
    to a saved LlamaCloud configuration id (cfg-...) to pull parameters
    from the platform instead of using the local values.
    """

    configuration_id: str | None = None


class ClassifyConfig(ClassifyV2Parameters):
    """Classify product configuration.

    Inherits the SDK `ClassifyV2Parameters` shape. Overrides `rules` default
    to `[]` so an unused classify slot validates without a rule list.
    """

    rules: list[Rule] = []
    configuration_id: str | None = None


class ParseConfig(ParseV2Parameters):
    """Parse product configuration."""

    configuration_id: str | None = None


class SplitConfig(SplitV1Parameters):
    """Split product configuration."""

    categories: list[SplitCategory] = []
    configuration_id: str | None = None


class Config(BaseModel):
    """Root configuration model for configs/config.json."""

    classify: ClassifyConfig
    extract_investment: ExtractConfig = Field(alias="extract-investment")
    parse: ParseConfig
    split: SplitConfig