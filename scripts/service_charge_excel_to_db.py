import numpy as np
import pandas as pd
from real_estate_telegram_bot.db.crud import upsert_project
from real_estate_telegram_bot.db.database import create_tables
from real_estate_telegram_bot.db.models import ProjectServiceCharge

if __name__ == '__main__':

    # Step 1: Read the Excel file
    excel_file_path = './data/Oa_Service_Charges_26_10_2024_s.xlsx'
    df = pd.read_excel(excel_file_path, na_values=['#N/A','NA', 'N/A', 'nan', 'NaN', '', 'NaT'], keep_default_na=False)
    df = df.where(pd.notnull(df), None)
    df = df.replace({np.nan: None})
    N = df.shape[0]
    create_tables()

    # Step 2: Iterate over DataFrame rows and create Project objects
    for index, row in df.iterrows():
        if index % 25 == 0:
            print(f"{index}/{N}")
        project = ProjectServiceCharge(
            project_id=row['project_id'],
            project_name = row["project_name"], 
            master_community_name_en_new = row["master_community_name_en_new"], 
            property_group_name_en = row["property_group_name_en"], 
            usage_name_en = row["usage_name_en"], 
            budget_year = row["budget_year"],
            master_project_en = row["master_project_en"],
            service_charge = row["Service Charge"],
            unit_ac = row["Unit AC"],
            meter_installation = row["Meter installation"]
        )

        # Step 3: Upsert the project into the database
        try:
            upsert_project(project)
        except:
            print(f"Error upserting project: {project.project_id}")
            continue