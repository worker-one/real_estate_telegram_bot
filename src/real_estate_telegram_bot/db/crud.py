import logging

from omegaconf import OmegaConf
from sqlalchemy.orm import Session

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

