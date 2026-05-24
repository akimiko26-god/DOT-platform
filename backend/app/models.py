import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class LeadStatus(str, enum.Enum):
    new = "new"
    in_progress = "in_progress"
    waiting = "waiting"
    done = "done"
    cancelled = "cancelled"


class LeadSource(str, enum.Enum):
    website = "website"
    landing = "landing"
    qr = "qr"
    form = "form"
    whatsapp = "whatsapp"
    telegram = "telegram"
    other = "other"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(64), default="")
    avatar_url = Column(String(512), default="")
    job_title = Column(String(128), default="")
    department = Column(String(128), default="")
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_seen_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    companies = relationship("Company", back_populates="owner")
    memberships = relationship("CompanyMember", back_populates="user", cascade="all, delete-orphan")
    reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(128), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reset_tokens")


class CompanyMember(Base):
    __tablename__ = "company_members"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_title = Column(String(128), default="")
    phone = Column(String(64), default="")
    department = Column(String(128), default="")
    role = Column(String(32), default="employee")
    perm_leads = Column(Boolean, default=False)
    perm_crm = Column(Boolean, default=False)
    perm_catalog = Column(Boolean, default=False)
    perm_qr = Column(Boolean, default=False)
    perm_settings = Column(Boolean, default=False)
    perm_employees = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="members")
    user = relationship("User", back_populates="memberships")


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    phone = Column(String(64), default="")
    email = Column(String(255), default="")
    address = Column(String(512), default="")
    website = Column(String(255), default="")
    whatsapp = Column(String(64), default="")
    telegram = Column(String(64), default="")
    instagram = Column(String(255), default="")
    work_schedule = Column(String(255), default="")
    activities = Column(Text, default="")
    director_name = Column(String(255), default="")
    bin_iin = Column(String(32), default="")
    legal_address = Column(String(512), default="")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    module_leads = Column(Boolean, default=True)
    module_crm = Column(Boolean, default=True)
    module_catalog = Column(Boolean, default=True)
    module_qr = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="companies")
    members = relationship("CompanyMember", back_populates="company", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="company", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="company", cascade="all, delete-orphan")
    catalog_categories = relationship("CatalogCategoryRef", back_populates="company", cascade="all, delete-orphan")
    catalog_tags = relationship("CatalogTagRef", back_populates="company", cascade="all, delete-orphan")
    catalog_folders = relationship("CatalogFolder", back_populates="company", cascade="all, delete-orphan")
    catalog_items = relationship("CatalogItem", back_populates="company", cascade="all, delete-orphan")
    page_views = relationship("PageView", back_populates="company", cascade="all, delete-orphan")
    qr_templates = relationship("QrSavedTemplate", back_populates="company", cascade="all, delete-orphan")
    qr_links = relationship("QrCustomLink", back_populates="company", cascade="all, delete-orphan")


class QrCustomLink(Base):
    __tablename__ = "qr_custom_links"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(128), nullable=False)
    url = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="qr_links")


class QrSavedTemplate(Base):
    __tablename__ = "qr_saved_templates"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(128), nullable=False)
    base_template = Column(String(32), default="custom")
    config_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="qr_templates")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(64), default="")
    email = Column(String(255), default="")
    notes = Column(Text, default="")
    is_vip = Column(Boolean, default=False)
    ai_insight = Column(Text, default="")
    visit_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="customers")
    leads = relationship("Lead", back_populates="customer")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    client_name = Column(String(255), nullable=False)
    client_phone = Column(String(64), default="")
    client_email = Column(String(255), default="")
    message = Column(Text, default="")
    source = Column(Enum(LeadSource), default=LeadSource.website)
    status = Column(Enum(LeadStatus), default=LeadStatus.new)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="leads")
    customer = relationship("Customer", back_populates="leads")
    comments = relationship("LeadComment", back_populates="lead", cascade="all, delete-orphan")


class LeadComment(Base):
    __tablename__ = "lead_comments"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    author_name = Column(String(255), default="Менеджер")
    author_job_title = Column(String(128), default="")
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="comments")
    user = relationship("User")


class CatalogCategoryRef(Base):
    __tablename__ = "catalog_category_refs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("catalog_category_refs.id"), nullable=True)
    name = Column(String(128), nullable=False)
    sort_order = Column(Integer, default=0)

    company = relationship("Company", back_populates="catalog_categories")
    parent = relationship("CatalogCategoryRef", remote_side=[id], backref="children")


class CatalogTagRef(Base):
    __tablename__ = "catalog_tag_refs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(64), nullable=False)
    sort_order = Column(Integer, default=0)

    company = relationship("Company", back_populates="catalog_tags")


class CatalogFolder(Base):
    __tablename__ = "catalog_folders"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    name = Column(String(128), nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="catalog_folders")
    items = relationship("CatalogItem", back_populates="folder")


class CatalogItem(Base):
    __tablename__ = "catalog_items"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    folder_id = Column(Integer, ForeignKey("catalog_folders.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    category = Column(String(128), default="")
    tags = Column(Text, default="[]")
    price = Column(Float, default=0)
    image_url = Column(String(512), default="")
    is_available = Column(Boolean, default=True)
    is_published = Column(Boolean, default=True)
    deleted_at = Column(DateTime, nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="catalog_items")
    folder = relationship("CatalogFolder", back_populates="items")


class PageView(Base):
    __tablename__ = "page_views"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    page = Column(String(64), default="profile")
    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company", back_populates="page_views")
