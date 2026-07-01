"""
Pydantic models for investment document schema.

This module defines the schema for investment marketing documents including
investment memorandums, information memorandums, teasers, management presentations,
and pitch decks. Focuses on investment highlights, business overview, and
opportunity assessment.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# Source-grounded value structure for anti-hallucination
class SourceGroundedValue(BaseModel):
    """Value with source grounding including quotes and attribution."""
    value: Optional[str] = Field(default=None, description="The extracted value from the document")
    quotes: List[str] = Field(
        default=[],
        description="Array of supporting quotes from the document, max 5. Format: '<verbatim quote ≤50 words> @ <location>'"
    )
    attribution: Optional[str] = Field(
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
    document_type: Optional[str] = Field(default=None, description="Type of document")
    document_type_other_description: Optional[str] = Field(
        default=None,
        description="If document_type is 'other', describe specifically. Otherwise null."
    )
    dd_side: Optional[str] = Field(
        default=None,
        description="For DD documents only: whether vendor or buyside"
    )
    document_producer: Optional[str] = Field(
        default=None,
        description="Name of the firm or team that produced the document (e.g. 'PwC', 'Goldman Sachs', 'in-house strategy team')"
    )
    producer_type: Optional[str] = Field(
        default=None,
        description="Category of document producer (e.g., investment_bank, consulting_firm, company_internal)"
    )
    producer_type_other_description: Optional[str] = Field(
        default=None,
        description="If producer_type is 'other', describe specifically."
    )
    sellside_project_name: Optional[str] = Field(
        default=None,
        description="Project codename used in the sale process (e.g. 'Project Falcon')"
    )
    document_version: Optional[str] = Field(
        default=None,
        description="Version of the document if specified (e.g. 'v1', 'v2 — updated March 2025', 'Draft 3')"
    )
    document_date: Optional[str] = Field(
        default=None,
        description="Date the document was published or finalised (YYYY-MM-DD if available)"
    )
    deal_type: Optional[str] = Field(
        default=None,
        description="Type of transaction the document relates to"
    )
    deal_type_other_description: Optional[str] = Field(
        default=None,
        description="If deal_type is 'other', describe specifically."
    )
    deal_advisors_mentioned: Optional[List[str]] = Field(
        default=None,
        description="Advisors named in the document (sellside/buyside M&A, legal, VDD provider, etc.)"
    )


# Company Overview section
class LeadershipItem(BaseModel):
    """Individual leadership team member."""
    role: Optional[str] = Field(default=None, description="Leadership role (e.g., CEO, CFO, Chairman)")
    name: Optional[str] = Field(default=None, description="Name of the person")
    tenure_in_role: Optional[str] = Field(default=None, description="How long in role (e.g., '5 years', 'since 2020')")
    background_notes: Optional[str] = Field(default=None, description="Notable background or qualifications")


class CompanyOverview(BaseModel):
    """Company information including business description and management team."""
    company_industry: Optional[str] = Field(
        default=None,
        description="Top-level industry classification. Use GICS sector naming where possible (e.g. 'Financial Services', 'Healthcare')"
    )
    sub_industry: Optional[str] = Field(
        default=None,
        description="More specific sub-sector (e.g. 'Payments software', 'Medical devices — orthopaedics')"
    )
    year_founded: Optional[str] = Field(
        default=None,
        description="Year the company was founded (as stated, e.g. '1995', 'circa 1990s')"
    )
    headquarters: Optional[str] = Field(
        default=None,
        description="Primary headquarters location (City, Country)"
    )
    office_locations: Optional[List[str]] = Field(
        default=None,
        description="Office locations (city, country format)"
    )
    countries_of_operation: Optional[List[str]] = Field(
        default=None,
        description="Countries where the company has commercial operations"
    )
    legal_entity_structure: Optional[str] = Field(
        default=None,
        description="Legal entity structure of the company (incorporation details, legal form, holding company)"
    )
    key_leadership: Optional[List[LeadershipItem]] = Field(
        default=None,
        description="Key leadership team — CEO, CFO, Chairman, founders, board members, etc."
    )
    business_description: Optional[str] = Field(
        default=None,
        description="Description of the company's business model, products/services, and operations"
    )
    ownership_structure: Optional[str] = Field(
        default=None,
        description="Ownership structure including major shareholders and ownership percentages"
    )
    key_customers: Optional[List[str]] = Field(
        default=None,
        description="Key customers or client relationships with source grounding"
    )


# Market Analysis section
class MarketSize(BaseModel):
    """Market size breakdown by TAM/SAM/SOM."""
    tam: Optional[str] = Field(default=None, description="Total Addressable Market (TAM)")
    sam: Optional[str] = Field(default=None, description="Serviceable Addressable Market (SAM)")
    som: Optional[str] = Field(default=None, description="Serviceable Obtainable Market (SOM)")


class CompetitiveLandscapeItem(BaseModel):
    """Individual competitor or market position item."""
    competitor_name: Optional[str] = Field(default=None, description="Name of competitor or market position")
    market_position: Optional[str] = Field(default=None, description="Market position or description")
    market_share: Optional[str] = Field(default=None, description="Market share percentage or description")


class CompetitiveAdvantageItem(BaseModel):
    """Individual competitive advantage item."""
    advantage_type: Optional[str] = Field(default=None, description="Type of competitive advantage")
    description: Optional[str] = Field(default=None, description="Description of the competitive advantage")
    sustainability: Optional[str] = Field(default=None, description="Sustainability assessment")


class CompetitivePositioning(BaseModel):
    """Competitive position including market share, landscape, and advantages."""
    market_share: Optional[List[str]] = Field(default=None, description="Market share for each year in YYYY | Share % format ")
    competitive_landscape: Optional[List[CompetitiveLandscapeItem]] = Field(
        default=None,
        description="Array of competitors and market positions"
    )
    competitive_advantages: Optional[List[CompetitiveAdvantageItem]] = Field(
        default=None,
        description="Array of competitive advantages"
    )


class MarketAnalysis(BaseModel):
    """Market analysis including TAM/SAM/SOM and competitive positioning."""
    market_size: Optional[MarketSize] = Field(
        default=None,
        description="Total Addressable Market, Serviceable Addressable Market, Serviceable Obtainable Market"
    )
    competitive_positioning: Optional[CompetitivePositioning] = Field(
        default=None,
        description="Competitive position including landscape and advantages"
    )


# Company Analysis section
class GoToMarketStrategyItem(BaseModel):
    """Individual go-to-market strategy item."""
    channel: Optional[str] = Field(default=None, description="Sales or distribution channel")
    description: Optional[str] = Field(default=None, description="Description of the channel strategy")
    effectiveness: Optional[str] = Field(default=None, description="Channel effectiveness metrics")


class MoatComponentItem(BaseModel):
    """Individual competitive moat component."""
    component_type: Optional[str] = Field(default=None, description="Type of moat component")
    description: Optional[str] = Field(default=None, description="Description of the moat component")
    strength: Optional[str] = Field(default=None, description="Assessment of moat strength")


class BusinessModel(BaseModel):
    """Business model analysis and revenue generation approach."""
    revenue_model: Optional[str] = Field(default=None, description="Revenue model details")
    value_proposition: Optional[str] = Field(default=None, description="Value proposition")
    go_to_market_strategy: Optional[List[GoToMarketStrategyItem]] = Field(
        default=None,
        description="Array of go-to-market strategies and channels"
    )


class CompetitiveMoat(BaseModel):
    """Competitive moat analysis and sustainability."""
    moat_components: Optional[List[MoatComponentItem]] = Field(
        default=None,
        description="Array of competitive moat components"
    )
    sustainability_assessment: Optional[SourceGroundedValue] = Field(
        default=None,
        description="Sustainability assessment"
    )


class CompanyAnalysis(BaseModel):
    """Company analysis including business model and competitive moat."""
    business_model: Optional[BusinessModel] = Field(
        default=None,
        description="Business model analysis and revenue generation approach"
    )
    competitive_moat: Optional[CompetitiveMoat] = Field(
        default=None,
        description="Competitive moat analysis and sustainability"
    )


# Financial Profile section
class FinancialStatements(BaseModel):
    """Historical financial statements and key line items."""
    balance_sheet: Optional[List[str]] = Field(default=None, description="Balance sheet data")
    income_statement: Optional[List[str]] = Field(default=None, description="Income statement data")
    cash_flow_statement: Optional[List[str]] = Field(default=None, description="Cash flow statement data")


class RevenueBreakdownItem(BaseModel):
    """Individual revenue breakdown item."""
    category: Optional[str] = Field(default=None, description="Revenue category")
    amount: Optional[str] = Field(default=None, description="Revenue amount in cash terms either from the amount specified in the document or calculated from the percentage value specified.")
    value_type: Optional[str] = Field(default=None, description="Currency with monetary amount, Percentage, Basis Points, Shares")
    growth_rate: Optional[str] = Field(default=None, description="Growth rate for the category")
    description: Optional[str] = Field(default=None, description="Additional details about the category")


class RevenueMix(BaseModel):
    """Revenue breakdown by product, geography, and customer segment."""
    by_product: Optional[List[RevenueBreakdownItem]] = Field(
        default=None,
        description="Array of revenue breakdown by product"
    )
    by_geography: Optional[List[RevenueBreakdownItem]] = Field(
        default=None,
        description="Array of revenue breakdown by geography"
    )
    by_customer_segment: Optional[List[RevenueBreakdownItem]] = Field(
        default=None,
        description="Array of revenue breakdown by customer segment"
    )


class ProfitabilityMetrics(BaseModel):
    """Key profitability metrics and trends."""
    gross_margin: Optional[str] = Field(default=None, description="Gross margin")
    operating_margin: Optional[str] = Field(default=None, description="Operating margin")
    ebitda_margin: Optional[str] = Field(default=None, description="EBITDA margin")
    net_margin: Optional[str] = Field(default=None, description="Net margin")


class FinancialProfile(BaseModel):
    """Financial profile including statements, revenue mix, and profitability."""
    financial_statements: Optional[FinancialStatements] = Field(
        default=None,
        description="Historical financial statements and key line items"
    )
    revenue_mix: Optional[RevenueMix] = Field(
        default=None,
        description="Revenue breakdown by product, geography, and customer segment"
    )
    profitability_metrics: Optional[ProfitabilityMetrics] = Field(
        default=None,
        description="Key profitability metrics and trends"
    )


# Growth Signals section
class UpsidesAndGrowthSignals(BaseModel):
    """Document-stated upsides and growth signals."""
    growth_drivers: Optional[List[str]] = Field(
        default=None,
        description="Key drivers of business growth and expansion opportunities"
    )
    market_opportunities: Optional[List[str]] = Field(
        default=None,
        description="Market opportunities and expansion potential"
    )


# Risks section
class Risks(BaseModel):
    """Document-stated risks across business, financial, operational, and regulatory categories."""
    business_risks: Optional[List[str]] = Field(
        default=None,
        description="Business-related risks and challenges"
    )
    financial_risks: Optional[List[str]] = Field(
        default=None,
        description="Financial risks including liquidity, leverage, and market risks"
    )
    regulatory_risks: Optional[List[str]] = Field(
        default=None,
        description="Regulatory and compliance risks"
    )


# Valuation section
class DebtStructureItem(BaseModel):
    """Individual debt structure item."""
    debt_type: Optional[str] = Field(default=None, description="Type of debt (senior, mezzanine, convertible, etc.)")
    amount: Optional[str] = Field(default=None, description="Debt amount")
    interest_rate: Optional[str] = Field(default=None, description="Interest rate or range")
    maturity: Optional[str] = Field(default=None, description="Maturity date or period")
    covenants: Optional[str] = Field(default=None, description="Key debt covenants or restrictions")


class EquityStructureItem(BaseModel):
    """Individual equity structure item."""
    shareholder_type: Optional[str] = Field(default=None, description="Type of shareholder (founder, VC, PE, etc.)")
    ownership_pct: Optional[str] = Field(default=None, description="Ownership percentage")
    shares: Optional[str] = Field(default=None, description="Number of shares or details")
    rights: Optional[str] = Field(default=None, description="Special rights or preferences")


class FundingHistoryItem(BaseModel):
    """Individual funding history item."""
    round_type: Optional[str] = Field(default=None, description="Type of funding round (Series A, B, C, etc.)")
    amount: Optional[str] = Field(default=None, description="Funding amount")
    date: Optional[str] = Field(default=None, description="Funding date")
    investors: Optional[str] = Field(default=None, description="Key investors in the round")
    valuation: Optional[str] = Field(default=None, description="Post-money valuation")


class CapitalStructure(BaseModel):
    """Capital structure and funding information."""
    debt_structure: Optional[List[DebtStructureItem]] = Field(
        default=None,
        description="Array of debt structure items"
    )
    equity_structure: Optional[List[EquityStructureItem]] = Field(
        default=None,
        description="Array of equity structure items"
    )
    funding_history: Optional[List[FundingHistoryItem]] = Field(
        default=None,
        description="Array of funding history items"
    )


class ValuationMetrics(BaseModel):
    """Valuation metrics and comparable analysis."""
    enterprise_value: Optional[str] = Field(default=None, description="Enterprise value")
    equity_value: Optional[str] = Field(default=None, description="Equity value")
    multiples: Optional[str] = Field(default=None, description="Valuation multiples")


class ValuationAndCapitalStructure(BaseModel):
    """Valuation metrics and capital structure analysis."""
    valuation_metrics: Optional[ValuationMetrics] = Field(
        default=None,
        description="Valuation metrics and comparable analysis"
    )
    capital_structure: Optional[CapitalStructure] = Field(
        default=None,
        description="Capital structure and funding information"
    )


# Merger/Carveout Considerations sections
class MergerConsiderations(BaseModel):
    """Merger-specific considerations (conditional on deal type)."""
    integration_risks: Optional[List[str]] = Field(
        default=None,
        description="Integration risks and challenges for merger scenarios"
    )
    synergies: Optional[List[str]] = Field(
        default=None,
        description="Expected synergies and value creation from merger"
    )


class CarveoutConsiderations(BaseModel):
    """Carveout-specific considerations (conditional on deal type)."""
    standalone_operations: Optional[List[str]] = Field(
        default=None,
        description="Requirements and challenges for standalone operations"
    )
    service_agreements: Optional[List[str]] = Field(
        default=None,
        description="Transition service agreements and shared services"
    )


# Main Investment Document Schema
class InvestmentDocumentSchema(BaseModel):
    """
    Comprehensive investment document extraction schema for investment marketing documents.

    Focuses on investment highlights, business overview, and opportunity assessment
    for investment memorandums, information memorandums, teasers, management presentations,
    and pitch decks.

    Follows anti-hallucination extraction policy:
    - Extract only what the document STATES
    - Source-ground key fields with {value, quotes, attribution} structure
    - Return null when not explicitly stated
    - Do not compute ratios or derived values
    """
    document_metadata: DocumentMetadata = Field(description="Document metadata including company name and document type")
    company_overview: Optional[CompanyOverview] = Field(default=None, description="Company information and business overview")
    market_analysis: Optional[MarketAnalysis] = Field(default=None, description="Market analysis and competitive positioning")
    company_analysis: Optional[CompanyAnalysis] = Field(default=None, description="Company analysis including business model and competitive moat")
    financial_profile: Optional[FinancialProfile] = Field(default=None, description="Financial profile including statements and profitability")
    document_stated_upsides_and_growth_signals: Optional[UpsidesAndGrowthSignals] = Field(default=None, description="Document-stated growth drivers and opportunities")
    valuation_and_capital_structure_signals: Optional[ValuationAndCapitalStructure] = Field(default=None, description="Valuation metrics and capital structure analysis")
    merger_considerations: Optional[MergerConsiderations] = Field(default=None, description="Merger considerations (conditional on deal_type)")
    carveout_considerations: Optional[CarveoutConsiderations] = Field(default=None, description="Carveout considerations (conditional on deal_type)")
