import logging
from datetime import datetime
from typing import Optional

import pandas as pd
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from real_estate_telegram_bot.db.database import get_session
from real_estate_telegram_bot.db.models import User

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def read_user(user_id: str) -> User:
    db: Session = get_session()
    result = db.query(User).filter(User.id == user_id).first()
    db.close()
    return result


def read_user_by_username(username: str) -> User:
    """Read user by username"""
    db: Session = get_session()
    result = db.query(User).filter(User.username == username).first()
    db.close()
    return result


def read_users() -> list[User]:
    db: Session = get_session()
    result = db.query(User).all()
    db.close()
    return result


def create_user(
    id: int,
    username: Optional[str] = None,
    lang: Optional[str] = None,
    role: Optional[str] = "user"
) -> User:
    """
    Create a new user.

    Args:
        id: The user's ID.
        username: The user's name.
        lang: The user's language.
        role: The user's role.

    Returns:
        The created user object.
    """
    db: Session = get_session()
    db.expire_on_commit = False
    try:
        user = User(
            id=id,
            username=username,
            first_message_timestamp=datetime.now(),
            last_message_timestamp=datetime.now(),
            lang=lang,
            role=role
        )
        db.add(user)
        db.commit()
        logger.debug(f"User with name {user.username} added successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding user with name {username}: {e}")
        raise
    finally:
        db.close()
    return user


def update_user(
    id: int,
    username: Optional[str] = None,
    lang: Optional[str] = None,
    role: Optional[str] = None
) -> User:
    """
    Update an existing user.

    Args:
        id: The user's ID.
        username: The user's name.
        lang: The user's language.
        role: The user's role.

    Returns:
        The updated user object.
    """
    db: Session = get_session()
    db.expire_on_commit = False
    try:
        user = db.query(User).filter(User.id == id).first()
        if user:
            if username is not None:
                user.username = username 
            if lang is not None:
                user.lang = lang
            if role is not None:
                user.role = role
            user.last_message_timestamp = datetime.now()
            db.commit()
            logger.debug(f"User with ID {user.id} updated successfully.")
        else:
            logger.error(f"User with ID {id} not found.")
            raise ValueError(f"User with ID {id} not found.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user with ID {id}: {e}")
        raise
    finally:
        db.close()
    return user


def upsert_user(
    id: int,
    username: Optional[str] = None,
    lang: Optional[str] = None,
    role: Optional[str] = None
) -> User:
    """
    Insert or update a user.

    Args:
        id: The user's ID.
        username: The user's name.
        lang: The user's language.
        role: The user's role.
        active_session_id: The user's active session ID.

    Returns:
        The user object.
    """
    db: Session = get_session()
    db.expire_on_commit = False
    try:
        user = db.query(User).filter(User.id == id).first()
        if user:
            user = update_user(
                id=id,
                username=username,
                lang=lang,
                role=role
            )
        else:
            user = create_user(
                id=id,
                username=username,
                lang=lang,
                role=role
            )
    except Exception as e:
        db.rollback()
        logger.error(f"Error upserting user with ID {id}: {e}")
        raise
    finally:
        db.close()
    return user


def update_user_language(user_id: int, new_language: str):
    """ Update the language for a user. """
    db: Session = get_session()
    try:
        # Query the user by user_id
        user = db.query(User).filter(User.id == user_id).one()

        # Update the language field
        user.lang = new_language

        # Commit the transaction
        db.commit()

        logger.info(f"User {user_id} language updated to {new_language}")
    except NoResultFound:
        db.rollback()
        logger.info(f"No user found with user_id {user_id}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating language for user {user_id}: {e}")
    finally:
        db.close()
