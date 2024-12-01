import csv
import logging
import os
from collections import defaultdict
from datetime import datetime
from typing import Optional

import pandas as pd
from sqlalchemy import Text, cast, func, inspect, text
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from real_estate_telegram_bot.db.database import get_session
from real_estate_telegram_bot.db.models import Event, Project, ProjectFile, ProjectServiceCharge, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_user(user_id: str) -> User:
    db: Session = get_session()
    result = db.query(User).filter(User.id == user_id).first()
    db.close()
    return result


def read_users() -> list[User]:
    db: Session = get_session()
    result = db.query(User).all()
    db.close()
    return result


def upsert_user(
    id: int,
    username: Optional[str] = None,
    lang: Optional[str] = "en",
    role: Optional[str] = None,
):
    """
    Insert or update a user.

    Args:
        id (int): The user's ID.
        name (str): The user's name.
        lang (str): The user's language.
        role (str): The user's role.

    Returns:
        User: The user object.
    """
    db: Session = get_session()
    db.expire_on_commit = False
    try:
        user = db.query(User).filter(User.id == id).first()
        if user:
            if username:
                user.username = username
            if role and user.role != "admin":
                user.role = role
        else:
            user = User(
                id=id, username=username,
                lang=lang, role=role
            )
            db.add(user)
            logger.info(f"User with name {user.username} added successfully.")
        db.commit()
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding user with name {username}: {e}")
    finally:
        db.close()

def update_user_language(user_id: int, new_language: str):
    db: Session = get_session()
    try:
        # Query the user by user_id
        user = db.query(User).filter(User.user_id == user_id).one()

        # Update the language field
        user.language = new_language

        # Commit the transaction
        db.commit()

        logger.info(f"User {user_id} language updated to {new_language}")
    except NoResultFound:
        db.rollback()
        logger.info(f"No user found with user_id {user_id}")
    except Exception as e:
        db.rollback()
        logger.info(str(e))

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
        return None
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


def create_event(user_id: str, content: str, type: str) -> Event:
    """Create an event for a user."""
    event = Event(user_id=user_id, content=content, type=type, timestamp=datetime.now())
    db: Session = get_session()
    db.expire_on_commit = False
    db.add(event)
    db.commit()
    db.close()
    return event


def read_event(event_id: int) -> Optional[Event]:
    db: Session = get_session()
    try:
        return db.query(Event).filter(Event.id == event_id).first()
    finally:
        db.close()


def read_events_by_user(user_id: str) -> list[Event]:
    db: Session = get_session()
    try:
        return db.query(Event).filter(Event.user_id == user_id).all()
    finally:
        db.close()


def export_all_tables(export_dir: str):
    db = get_session()
    inspector = inspect(db.get_bind())

    for table_name in inspector.get_table_names():
        file_path = os.path.join(export_dir, f"{table_name}.csv")
        with open(file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            writer.writerow(columns)

            records = db.execute(text(f"SELECT * FROM {table_name}")).fetchall()
            for record in records:
                writer.writerow(record)

    db.close()
