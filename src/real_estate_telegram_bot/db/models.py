from sqlalchemy import Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base model"""

    pass

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    user_id = Column(Integer, ForeignKey('users.user_id'))
    message_text = Column(String)

    user = relationship("User", back_populates="message")


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    first_message_timestamp = Column(DateTime)
    username = Column(String)
    phone_number = Column(String)
    language = Column(String, default='en')

    message = relationship("Message", back_populates="user", cascade="all, delete-orphan")


class Project(Base):

    __tablename__ = 'projects'

    project_id = Column(Integer, primary_key=True)
    project_name = Column(String)
    project_name_id_buildings = Column(String)
    developer_id = Column(Integer)
    developer_name = Column(String)
    developer_name_en = Column(String)
    registration_date = Column(DateTime, nullable=True)
    license_source_en = Column(String)
    license_number = Column(String)
    license_issue_date = Column(DateTime, nullable=True)
    license_expiry_date = Column(DateTime, nullable=True)
    chamber_of_commerce_no = Column(String)
    webpage = Column(String)
    master_developer_name = Column(String)
    master_developer_name_en = Column(String)
    project_start_date = Column(DateTime, nullable=True)
    project_end_date = Column(DateTime, nullable=True)
    project_status = Column(String)
    percent_completed = Column(Integer)
    completion_date = Column(DateTime, nullable=True)
    cancellation_date = Column(DateTime, nullable=True)
    project_description_en = Column(String)
    area_name_en = Column(String)
    master_project_en = Column(String)
    zoning_authority_en = Column(String)
    no_of_buildings = Column(Integer)
    no_of_villas = Column(Integer)
    no_of_units = Column(Integer)
    is_free_hold = Column(String)
    is_lease_hold = Column(String)
    is_registered = Column(String)
    property_type_en = Column(String)
    property_sub_type_en = Column(String)
    land_type_en = Column(String)
    floors = Column(Integer)

    project_files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    project_service_charge = relationship("ProjectServiceCharge", back_populates="project", cascade="all, delete-orphan")

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class ProjectServiceCharge(Base):
    __tablename__ = 'projects_service_charge'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'))
    project_name = Column(String)
    master_community_name_en_new = Column(String)
    property_group_name_en = Column(String)
    usage_name_en = Column(String)
    budget_year = Column(Integer)
    master_project_en = Column(String)
    service_charge = Column(Integer)
    unit_ac = Column(Integer)
    meter_installation = Column(Integer)

    project = relationship("Project", back_populates="project_service_charge")

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class ProjectFile(Base):

    __tablename__ = 'project_files'

    file_id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.project_id'))
    file_name = Column(String)
    file_type = Column(String)
    file_telegram_id = Column(String)

    project = relationship("Project", back_populates="project_files")
