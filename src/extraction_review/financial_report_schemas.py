"""
Pydantic models for financial report schema.

This module defines the schema for financial reports including SEC filings (10-K, 10-Q),
annual reports, quarterly reports, and earnings releases. Focuses on financial statements,
revenue breakdowns, and performance metrics.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


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
        description="Category of document producer (e.g., investment_bank, big4_accounting, company_internal)"
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
    deal_advisors_mentioned: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Advisors named in the document (sellside/buyside M&A, legal, VDD provider, etc.)"
    )


# Leadership item for company overview
class LeadershipItem(BaseModel):
    """Individual leadership team member."""
    role: Optional[str] = Field(default=None, description="Leadership role (e.g., CEO, CFO, Chairman)")
    name: Optional[str] = Field(default=None, description="Name of the person")
    tenure_in_role: Optional[str] = Field(default=None, description="How long in role (e.g., '5 years', 'since 2020')")
    background_notes: Optional[str] = Field(default=None, description="Notable background or qualifications")


# Company Overview section
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
    legal_entity_structure: Optional[Dict[str, Any]] = Field(
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
    ownership_structure: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Ownership structure including major shareholders and ownership percentages"
    )
    key_customers: Optional[List[str]] = Field(
        default=None,
        description="Key customers or client relationships"
    )


# Financial Profile section
class FinancialStatements(BaseModel):
    """Historical financial statements and key line items."""
    balance_sheet: Optional[Dict[str, Any]] = Field(default=None, description="Balance sheet data")
    income_statement: Optional[Dict[str, Any]] = Field(default=None, description="Income statement data")
    cash_flow_statement: Optional[Dict[str, Any]] = Field(default=None, description="Cash flow statement data")


class RevenueBreakdownItem(BaseModel):
    """Individual revenue breakdown item."""
    category: Optional[str] = Field(default=None, description="Revenue category (product, geography, customer segment)")
    amount: Optional[str] = Field(default=None, description="Revenue amount or percentage")
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
    gross_margin: Optional[Dict[str, Any]] = Field(default=None, description="Gross margin")
    operating_margin: Optional[Dict[str, Any]] = Field(default=None, description="Operating margin")
    ebitda_margin: Optional[Dict[str, Any]] = Field(default=None, description="EBITDA margin")
    net_margin: Optional[Dict[str, Any]] = Field(default=None, description="Net margin")


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


# Main Financial Report Schema
class FinancialReportSchema(BaseModel):
    """
    Schema for financial reports including SEC filings, annual reports, and quarterly reports.

    Focuses on financial statements, revenue breakdowns, and performance metrics.
    Optimized for extracting key financial information from 10-K, 10-Q, earnings releases,
    and other financial reporting documents.

    Follows anti-hallucination extraction policy:
    - Extract only what the document STATES
    - Use simple types for factual data
    - Return null when not explicitly stated
    - No computation of derived values
    """
    document_metadata: DocumentMetadata = Field(description="Document metadata including company name and document type")
    company_overview: Optional[CompanyOverview] = Field(default=None, description="Company information and business overview")
    financial_profile: Optional[FinancialProfile] = Field(default=None, description="Financial profile including statements and profitability")
    document_stated_risks: Optional[Risks] = Field(default=None, description="Document-stated risks across multiple categories")
