import numpy as np
import pandas as pd
from real_estate_telegram_bot.db.crud import upsert_project
from real_estate_telegram_bot.db.database import create_tables
from real_estate_telegram_bot.db.models import Project

if __name__ == '__main__':

    # Step 1: Read the Excel file
    excel_file_path = './data/Projects_2000-2025_14 oct_short.xlsx'
    df = pd.read_excel(excel_file_path, na_values=['#N/A','NA', 'N/A', 'nan', 'NaN', '', 'NaT'], keep_default_na=False)
    df = df.where(pd.notnull(df), None)
    df = df.replace({np.nan: None})
    create_tables()

    # Step 2: Iterate over DataFrame rows and create Project objects
    for index, row in df.iterrows():
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

        # Step 3: Upsert the project into the database
        try:
            upsert_project(project)
        except:
            print(f"Error upserting project: {project.project_id}")
            continue