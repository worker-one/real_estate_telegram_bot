import csv
import logging
import os
from collections import defaultdict
from datetime import datetime

import pandas as pd
from sqlalchemy import Text, cast, func
from sqlalchemy.orm import Session

from real_estate_telegram_bot.db.database import get_session
from real_estate_telegram_bot.db.models import Project, ProjectFile, ProjectServiceCharge

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Projects

def read_project(project_id: int) -> Project:
    db: Session = get_session()
    result = db.query(Project).filter(Project.project_id == project_id).first()
    db.close()
    return result

def upsert_project(project: Project):
    db: Session = get_session()
    db.merge(project)
    db.commit()
    db.close()


def query_projects_by_name(project_name: str, mode: str = "ilike", similarity_threshold: float = 0.35) -> list[Project]:
    db: Session = get_session()
    if mode == "ilike":
        result = db.query(Project).filter(Project.project_name_id_buildings.ilike(f"%{project_name}%")).all()
    elif mode == "cosine":
        result = db.query(
            Project,
            func.similarity(cast(Project.project_name_id_buildings, Text), cast(project_name, Text)).label("similarity_score")
        ).filter(
            func.similarity(cast(Project.project_name_id_buildings, Text), cast(project_name, Text)) >= similarity_threshold
        ).order_by(
            func.similarity(cast(Project.project_name_id_buildings, Text), cast(project_name, Text)).desc()
        ).all()

        # Extract project
        result = [item[0] for item in result]
    else:
        raise ValueError(f"Query mode {mode} is not supported.")
    db.close()
    return result

def get_buildings_by_area(area_name: str) -> list[dict]:
    """
    Retrieves a list of buildings in the given area from the database and sorts them by age.

    :param area_name: Name of the area to filter projects.
    :return: A list of dictionaries containing building name, construction end date, and age.
    """
    db: Session = get_session()

    # Query the database for buildings in the given area (master_project_en)
    projects = db.query(Project).filter(Project.master_project_en.ilike(f"%{area_name}%")).all()

    if not projects:
        db.close()
        return []

    # # Sort by building age (newest to oldest)
    # projects.sort(key=lambda x: x.project_end_date, reverse=True)

    # Calculate building age
    current_year = datetime.now().year
    building_data = []

    for project in projects:
        if project.project_name_id_buildings:
            if project.project_end_date:
                building_age = current_year - project.project_end_date.year
                project_end_date = project.project_end_date
                if building_age <= 0:
                    building_age = project.project_status
            else:
                building_age = project.project_status
                project_end_date = None
            building_data.append({
                "Building name": project.project_name_id_buildings,
                "Construction end date": project_end_date,
                "Completion %": project.percent_completed,
                "How old is the building (years)": building_age
            })

    db.close()
    return building_data

def get_project_file_by_name(file_name: str) -> Project:
    db: Session = get_session()
    result = db.query(ProjectFile).filter(ProjectFile.file_name.ilike(f"%{file_name}%")).first()
    return result

def get_project_files_by_project_id(project_id: int) -> list[ProjectFile]:
    db: Session = get_session()
    result = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).all()
    return result


def add_project_file(file_name: str, file_type: str, file_telegram_id: str, project_id: int) -> ProjectFile:
    project_file = ProjectFile(
        file_name=file_name,
        file_type=file_type,
        project_id=project_id,
        file_telegram_id=file_telegram_id
    )
    db: Session = get_session()
    db.add(project_file)
    db.commit()
    db.close()
    return project_file

def update_project_file(file_name: str, file_type: str, file_telegram_id: str, project_id: int) -> ProjectFile:
    # Replace file_telegram_id in project file with file_telegram_id
    db: Session = get_session()
    project_file = db.query(ProjectFile).filter(ProjectFile.file_name == file_name).first()
    project_file.file_telegram_id = file_telegram_id
    db.commit()
    db.close()

# Get project file by `file_name`
def get_project_files_by_name(keyword: str, top_k: int = 10) -> ProjectFile:
    db: Session = get_session()
    result = db.query(ProjectFile).filter(ProjectFile.file_name.ilike(f"%{keyword}%")).limit(top_k).all()
    db.close()
    return result

def read_service_charge(charge_id: int) -> ProjectServiceCharge:
    db: Session = get_session()
    result = db.query(ProjectServiceCharge).filter(ProjectServiceCharge.charge_id == charge_id).first()
    db.close()
    return result

def get_project_service_charge_by_year(master_project_en: str) -> list[dict[str, any]]:
    db: Session = get_session()

    # Query to get the project service charge data
    query = db.query(
        ProjectServiceCharge.project_name,
        ProjectServiceCharge.property_group_name_en,
        ProjectServiceCharge.budget_year,
        ProjectServiceCharge.service_charge
    ).filter(
        ProjectServiceCharge.master_project_en.ilike(f"%{master_project_en}%")
    ).order_by(
        ProjectServiceCharge.project_name,
        ProjectServiceCharge.budget_year
    )

    # Fetching data from the query
    results = query.all()

    if not results:
        return pd.DataFrame()

    # Processing the results into a dictionary for pivoting
    data = defaultdict(lambda: {"project_name": "", "property_group_name_en": ""})

    for project_name, property_group_name_en, budget_year, service_charge in results:
        if not data[(project_name, property_group_name_en)]["project_name"]:
            data[(project_name, property_group_name_en)]["project_name"] = project_name
            data[(project_name, property_group_name_en)]["property_group_name_en"] = property_group_name_en
        data[(project_name, property_group_name_en)][budget_year] = service_charge

    # Converting the dictionary to a DataFrame
    df = pd.DataFrame.from_dict(data, orient="index").reset_index(drop=True)

    # Reordering columns to ensure years are in the correct order
    year_columns = sorted([col for col in df.columns if isinstance(col, int)])
    df = df[["project_name", "property_group_name_en"] + year_columns]

    # Fill missing values with empty strings or NaN if needed
    df = df.fillna("")
    return df


def get_area_service_charge_by_year(area_name: str) -> pd.DataFrame:
    db: Session = get_session()

    # Query to get the area service charge data
    query = db.query(
        ProjectServiceCharge.project_name,
        ProjectServiceCharge.property_group_name_en,
        ProjectServiceCharge.budget_year,
        ProjectServiceCharge.service_charge
    ).filter(
        ProjectServiceCharge.master_project_en.ilike(f"%{area_name}%")
    ).order_by(
        ProjectServiceCharge.project_name,
        ProjectServiceCharge.budget_year
    )

    # Fetching data from the query
    results = query.all()

    if not results:
        return pd.DataFrame()

    # Processing the results into a dictionary for pivoting
    data = defaultdict(lambda: {"project_name": "", "property_group_name_en": ""})

    for project_name, property_group_name_en, budget_year, service_charge in results:
        if not data[(project_name, property_group_name_en)]["project_name"]:
            data[(project_name, property_group_name_en)]["project_name"] = project_name
            data[(project_name, property_group_name_en)]["property_group_name_en"] = property_group_name_en
        data[(project_name, property_group_name_en)][budget_year] = service_charge

    # Converting the dictionary to a DataFrame
    df = pd.DataFrame.from_dict(data, orient="index").reset_index(drop=True)

    # Reordering columns to ensure years are in the correct order
    year_columns = sorted([col for col in df.columns if isinstance(col, int)])
    df = df[["project_name", "property_group_name_en"] + year_columns]

    # Fill missing values with empty strings or NaN if needed
    df = df.fillna("")
    return df

def upsert_project_service_charge(project_service_charge: ProjectServiceCharge):
    """ Upsert a project service charge record. """
    db: Session = get_session()
    db.merge(project_service_charge)
    db.commit()
    db.close()
