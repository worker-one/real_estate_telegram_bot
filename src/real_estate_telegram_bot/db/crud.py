import logging

from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session
from datetime import datetime
from real_estate_telegram_bot.db.database import get_session
from real_estate_telegram_bot.db.models import Project, User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def read_user(user_id: int) -> User:
    db: Session = get_session()
    result = db.query(User).filter(User.user_id == user_id).first()
    db.close()
    return result

def read_users() -> list[User]:
    db: Session = get_session()
    result = db.query(User).all()
    db.close()
    return result

def upsert_user(
        user_id: str,
        username: str,
        phone_number: str = None,
        language: str = "en"
    ) -> User:
    user = User(
        user_id=user_id,
        username=username
    )
    if phone_number:
        user.phone_number = phone_number
    if language:
        user.language = language
    db: Session = get_session()
    db.merge(user)
    db.commit()
    db.close()
    return user

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

def query_projects_by_name(project_name: str) -> list[Project]:
    db: Session = get_session()
    result = db.query(Project).filter(Project.project_name_id_buildings.ilike(f"%{project_name}%")).all()
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

    # Calculate building age
    current_year = datetime.now().year
    building_data = []
    
    for project in projects:
        # Skip projects without an end date
        if project.project_end_date:
            building_age = current_year - project.project_end_date.year
            building_data.append({
                "Building name": project.project_name_id_buildings,
                "Construction end date": project.project_end_date.strftime('%Y-%m-%d'),
                "How old is the building": building_age
            })

    # Sort by building age (newest to oldest)
    building_data = sorted(building_data, key=lambda x: x["How old is the building"])

    db.close()
    return building_data