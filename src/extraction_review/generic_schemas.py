"""
Pydantic models for generic document schema.

This module defines the fallback schema for documents that don't fit into
specific categories or are of unknown type. Provides basic document metadata extraction.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal


class DealAdvisorItem(BaseModel):
    """Individual deal advisor."""
    advisor_name: Optional[str] = Field(default=None, description="Firm name (e.g. 'Goldman Sachs', 'Kirkland & Ellis', 'PwC')")
    advisor_role: Optional[Literal[
        "sellside_m_and_a",
        "buyside_m_and_a",
        "sellside_legal",
        "buyside_legal",
        "vdd_provider",
        "buyside_dd_provider",
        "qofe_provider",
        "tax_advisor",
        "process_manager",
        "debt_advisor",
        "not_known",
        "other"
    ]] = Field(default=None, description="Role of the advisor in the deal")
    advisor_role_other_description: Optional[str] = Field(
        default=None,
        description="If advisor_role is 'other', describe"
    )
    mandate_description: Optional[str] = Field(
        default=None,
        description="Brief description of the advisor's mandate if specified"
    )


class DocumentMetadata(BaseModel):
    """Metadata describing the source document itself."""
    company_name: str = Field(description="Name of the company being analysed in the document")
    document_type: Optional[Literal[
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
        "other"
    ]] = Field(default=None, description="Type of document")
    document_type_other_description: Optional[str] = Field(
        default=None,
        description="If document_type is 'other', describe specifically. Otherwise null."
    )
    dd_side: Optional[Literal[
        "vendor",
        "buyside",
        "joint_vendor_buyside",
        "not_applicable",
        "not_known"
    ]] = Field(
        default=None,
        description="For DD documents only: whether the report was commissioned by the seller (vendor) or the acquirer (buyside)"
    )
    document_producer: Optional[str] = Field(
        default=None,
        description="Name of the firm or team that produced the document (e.g. 'PwC', 'Goldman Sachs', 'in-house strategy team')"
    )
    producer_type: Optional[Literal[
        "investment_bank",
        "big4_accounting",
        "strategy_consultant",
        "specialist_advisor",
        "law_firm",
        "internal",
        "research_provider",
        "not_known",
        "other"
    ]] = Field(default=None, description="Category of document producer")
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
    deal_type: Optional[Literal[
        "series_a",
        "series_b",
        "series_c",
        "series_d_plus",
        "growth_equity",
        "majority_buyout",
        "minority_buyout",
        "carve_out",
        "public_to_private",
        "merger",
        "not_known",
        "other"
    ]] = Field(default=None, description="Type of transaction the document relates to")
    deal_type_other_description: Optional[str] = Field(
        default=None,
        description="If deal_type is 'other', describe specifically."
    )
    deal_advisors_mentioned: Optional[List[DealAdvisorItem]] = Field(
        default=None,
        description="Advisors named in the document (sellside/buyside M&A, legal, VDD provider, QofE provider, etc.)"
    )


class GenericDocumentSchema(BaseModel):
    """
    Generic fallback schema for documents that don't fit into specific categories.

    Provides basic document metadata extraction for unknown or uncategorized documents.

    Follows anti-hallucination extraction policy:
    - Extract only what the document STATES
    - Return null when not explicitly stated
    - Use literal values for enums
    """
    document_metadata: DocumentMetadata = Field(description="Document metadata including company name and document type")
