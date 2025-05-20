import os
import logging
import csv
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import inspect, text

from real_estate_telegram_bot.db.database import get_session
from real_estate_telegram_bot.db.models import Event

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

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
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            writer.writerow(columns)

            records = db.execute(text(f"SELECT * FROM {table_name}")).fetchall()
            for record in records:
                writer.writerow(record)

    db.close()