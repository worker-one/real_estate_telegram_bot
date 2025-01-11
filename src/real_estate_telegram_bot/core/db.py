import logging
import pandas as pd
import numpy as np

from real_estate_telegram_bot.db.crud import upsert_project_service_charge, read_service_charge
from real_estate_telegram_bot.db.crud import upsert_project, read_project
from real_estate_telegram_bot.db.models import ProjectServiceCharge, Project

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def compare_service_charges(charge1: ProjectServiceCharge, charge2: ProjectServiceCharge):
    """
    Compare two ServiceCharge objects and return a dictionary of differences.
    """
    differences = {}
    for key in charge1.__dict__:
        if key.startswith("_"):
            continue
        if str(charge1.__dict__[key]) != str(charge2.__dict__[key]):
            differences[key] = (charge1.__dict__[key], charge2.__dict__[key])
    return differences

def compare_projects(project1: Project, project2: Project):
    """
    Compare two Project objects and return a dictionary of differences.
    """
    differences = {}
    for key in project1.__dict__:
        if key.startswith("_"):
            continue
        if str(project1.__dict__[key]) != str(project2.__dict__[key]):
            differences[key] = (project1.__dict__[key], project2.__dict__[key])
    return differences

def import_service_charges_from_excel(excel_file_path: str):
    
    # Initialize results tracking
    results = []

    # Step 1: Read the Excel file
    df = pd.read_excel(excel_file_path, na_values=['#N/A','NA', 'N/A', 'nan', 'NaN', '', 'NaT'], keep_default_na=False)
    df = df.where(pd.notnull(df), None)
    df = df.replace({np.nan: None})

    # Step 2: Iterate over DataFrame rows and create ServiceCharge objects
    for index, row in df.iterrows():
        try:
            if index % 100 == 0:
                print(f"{index/len(df)*100:.2f}% done")
            service_charge = ProjectServiceCharge(
                charge_id=row['charge_id'],
                project_id=row['project_id'],
                charge_amount=row['charge_amount'],
                charge_date=row['charge_date'],
                charge_description=row['charge_description']
            )

            # Check if service charge exists
            existing = read_service_charge(service_charge.charge_id)

            if existing:
                diffs = compare_service_charges(service_charge, existing)
                if not diffs:
                    status = "unchanged"
                    message = " "
                else:
                    # show what columns have changed
                    status = "updated"
                    message = diffs
                    upsert_project_service_charge(service_charge)

            else:
                upsert_project_service_charge(service_charge)
                status = "created"
                message = " "

            results.append({
                "charge_id": service_charge.charge_id,
                "status": status,
                "message": message
            })
            
        except Exception as e:
            results.append({
                "charge_id": row.get('charge_id', 'unknown'),
                "status": "error", 
                "message": str(e)
            })
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    return results_df

def compare_projects(project1: Project, project2: Project):
    """
    Compare two Project objects and return a dictionary of differences.
    """
    differences = {}
    for key in project1.__dict__:
        if key.startswith("_"):
            continue
        if str(project1.__dict__[key]) != str(project2.__dict__[key]):
            differences[key] = (project1.__dict__[key], project2.__dict__[key])
    return differences

def import_projects_from_excel(excel_file_path: str):
    
    # Initialize results tracking
    results = []

    # Step 1: Read the Excel file
    df = pd.read_excel(excel_file_path, na_values=['#N/A','NA', 'N/A', 'nan', 'NaN', '', 'NaT'], keep_default_na=False)
    df = df.where(pd.notnull(df), None)
    df = df.replace({np.nan: None})

    # Step 2: Iterate over DataFrame rows and create Project objects
    for index, row in df.iterrows():
        try:
            if index % 100 == 0:
                print(f"{index/len(df)*100:.2f}% done")
            project = Project(
                project_id=row['project_id'],
                project_name=row['project_name'],
                project_name_id_buildings=row['project_name_id_buildings'],
                developer_id=row['developer_id'],
                developer_name=row['developer_name'],
                developer_name_en=row['developer_name_en'],
                registration_date=row['registration_date'],
                license_source_en=row['license_source_en'],
                license_number=row['license_number'],
                license_issue_date=row['license_issue_date'],
                license_expiry_date=row['license_expiry_date'],
                chamber_of_commerce_no=row['chamber_of_commerce_no'],
                webpage=row['webpage'],
                master_developer_name=row['master_developer_name'],
                master_developer_name_en=row['master_developer_name_en'],
                project_start_date=row['project_start_date'],
                project_end_date=row['project_end_date'],
                project_status=row['project_status'],
                percent_completed=row['percent_completed'],
                completion_date=row['completion_date'],
                cancellation_date=row['cancellation_date'],
                project_description_en=row['project_description_en'],
                area_name_en=row['area_name_en'],
                master_project_en=row['master_project_en'],
                zoning_authority_en=row['zoning_authority_en'],
                no_of_buildings=row['no_of_buildings'],
                no_of_villas=row['no_of_villas'],
                no_of_units=row['no_of_units'],
                is_free_hold=row['is_free_hold'],
                is_lease_hold=row['is_lease_hold'],
                is_registered=row['is_registered'],
                property_type_en=row['property_type_en'],
                property_sub_type_en=row['property_sub_type_en'],
                land_type_en=row['land_type_en'],
                floors=row['floors']
            )

            # Check if project exists
            existing = read_project(project.project_id)
            
            if existing:
                diffs = compare_projects(project, existing)
                if not diffs:
                    status = "unchanged"
                    message = " "
                else:
                    # show what columns have changed
                    status = "updated"
                    message = diffs
                    upsert_project(project)
                    
                    
            else:
                upsert_project(project)
                status = "created"
                message = " "
                
            results.append({
                "project_id": project.project_id,
                "status": status,
                "message": message
            })
            
        except Exception as e:
            results.append({
                "project_id": row.get('project_id', 'unknown'),
                "status": "error", 
                "message": str(e)
            })
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Log summary
    total = len(results_df)
    created = len(results_df[results_df['status'] == 'created'])
    updated = len(results_df[results_df['status'] == 'updated'])
    errors = len(results_df[results_df['status'] == 'error'])
    logger.info(f"Processed {total} records: {created} created {updated} updated, {errors} errors")
    
    return results_df