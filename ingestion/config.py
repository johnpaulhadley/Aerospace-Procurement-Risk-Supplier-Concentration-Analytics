"""Shared settings for ingestion: scope, kept columns and database connection."""
import os

from dotenv import load_dotenv

load_dotenv()

# Scope: a transaction is kept when its product/service code falls in one of
# these PSC groups OR its NAICS code is in aerospace product and parts
# manufacturing (3364xx). The NAICS rule brings in R&D and sustainment work.
PSC_GROUPS = ("14", "15", "16", "17", "18", "28")
NAICS_PREFIX = "3364"

AGENCIES = {
    "dod": {"name": "Department of Defense", "toptier_code": "097"},
    "nasa": {"name": "National Aeronautics and Space Administration", "toptier_code": "080"},
}

# Columns kept from the 297 in the source files.
COLUMNS = [
    "contract_transaction_unique_key", "contract_award_unique_key", "award_id_piid",
    "modification_number", "transaction_number", "parent_award_id_piid",
    "federal_action_obligation", "total_dollars_obligated",
    "base_and_exercised_options_value", "current_total_value_of_award",
    "base_and_all_options_value", "potential_total_value_of_award",
    "action_date", "action_date_fiscal_year", "period_of_performance_start_date",
    "period_of_performance_current_end_date", "period_of_performance_potential_end_date",
    "awarding_agency_code", "awarding_agency_name", "awarding_sub_agency_code",
    "awarding_sub_agency_name", "awarding_office_code", "awarding_office_name",
    "recipient_uei", "recipient_name", "recipient_name_raw", "cage_code",
    "recipient_parent_uei", "recipient_parent_name", "recipient_country_code",
    "recipient_state_code", "recipient_city_name",
    "primary_place_of_performance_country_code", "primary_place_of_performance_state_code",
    "primary_place_of_performance_city_name",
    "award_type_code", "award_type", "type_of_contract_pricing_code",
    "type_of_contract_pricing", "transaction_description",
    "prime_award_base_transaction_description", "action_type_code", "action_type",
    "product_or_service_code", "product_or_service_code_description",
    "naics_code", "naics_description",
    "dod_acquisition_program_code", "dod_acquisition_program_description",
    "extent_competed_code", "extent_competed", "solicitation_procedures",
    "other_than_full_and_open_competition", "number_of_offers_received",
    "undefinitized_action", "multi_year_contract",
    "contracting_officers_determination_of_business_size",
    "usaspending_permalink", "initial_report_date", "last_modified_date",
]


def database_url():
    return "postgresql+psycopg2://{u}:{p}@{h}:{port}/{db}".format(
        u=os.environ["POSTGRES_USER"], p=os.environ["POSTGRES_PASSWORD"],
        h=os.environ.get("POSTGRES_HOST", "localhost"),
        port=os.environ.get("POSTGRES_PORT", "5432"), db=os.environ["POSTGRES_DB"],
    )
