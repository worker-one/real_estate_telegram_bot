import logging
import pandas as pd
import numpy as np

from real_estate_telegram_bot.db.crud import upsert_service_charge, read_service_charge
from real_estate_telegram_bot.db.models import ServiceCharge

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def compare_service_charges(charge1: ServiceCharge, charge2: ServiceCharge):
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
            service_charge = ServiceCharge(
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
                    upsert_service_charge(service_charge)
                    
            else:
                upsert_service_charge(service_charge)
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
    
    # Log summary
    total = len(results_df)
    created = len(results_df[results_df['status'] == 'created'])
    updated = len(results_df[results_df['status'] == 'updated'])
    errors = len(results_df[results_df['status'] == 'error'])
    logger.info(f"Processed {total} records: {created} created {updated} updated, {errors} errors")
    
    return results_df

if __name__ == "__main__":
    results_df = import_service_charges_from_excel(".tmp/test_data.xlsx")
    results_df.to_excel(".tmp/results.xlsx", index=False)