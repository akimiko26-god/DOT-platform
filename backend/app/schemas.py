from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models import LeadSource, LeadStatus


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    is_admin: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CompanyCreate(BaseModel):
    name: str
    slug: str = Field(pattern=r"^[a-z0-9-]+$")
    description: str = ""
    director_name: str = ""
    bin_iin: str = ""
    legal_address: str = ""
    phone: str = ""
    email: str = ""
    address: str = ""
    website: str = ""
    whatsapp: str = ""
    telegram: str = ""
    instagram: str = ""
    work_schedule: str = ""
    activities: str = ""


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    director_name: Optional[str] = None
    bin_iin: Optional[str] = None
    legal_address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    whatsapp: Optional[str] = None
    telegram: Optional[str] = None
    instagram: Optional[str] = None
    work_schedule: Optional[str] = None
    activities: Optional[str] = None
    module_leads: Optional[bool] = None
    module_crm: Optional[bool] = None
    module_catalog: Optional[bool] = None
    module_qr: Optional[bool] = None


class CompanyOut(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    director_name: str = ""
    bin_iin: str = ""
    legal_address: str = ""
    phone: str
    email: str
    address: str
    website: str
    whatsapp: str
    telegram: str
    instagram: str
    work_schedule: str
    activities: str
    module_leads: bool
    module_crm: bool
    module_catalog: bool
    module_qr: bool
    is_active: bool

    class Config:
        from_attributes = True


class LeadCreate(BaseModel):
    client_name: str
    client_phone: str = ""
    client_email: str = ""
    message: str = ""
    source: LeadSource = LeadSource.form


class LeadUpdate(BaseModel):
    status: Optional[LeadStatus] = None
    client_name: Optional[str] = None
    client_phone: Optional[str] = None
    client_email: Optional[str] = None
    message: Optional[str] = None


class LeadCommentCreate(BaseModel):
    text: str
    author_name: str = "Менеджер"


class LeadCommentOut(BaseModel):
    id: int
    author_name: str
    author_job_title: str = ""
    text: str
    created_at: datetime

    class Config:
        from_attributes = True


class LeadOut(BaseModel):
    id: int
    client_name: str
    client_phone: str
    client_email: str
    message: str
    source: LeadSource
    status: LeadStatus
    created_at: datetime
    updated_at: datetime
    comments: list[LeadCommentOut] = []

    class Config:
        from_attributes = True


class CustomerCreate(BaseModel):
    name: str
    phone: str = ""
    email: str = ""
    notes: str = ""
    is_vip: bool = False


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None
    is_vip: Optional[bool] = None


class CustomerOut(BaseModel):
    id: int
    name: str
    phone: str
    email: str
    notes: str
    is_vip: bool = False
    visit_count: int
    ai_insight: str = ""
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerDetailOut(CustomerOut):
    leads: list[LeadOut] = []
    insight_meta: dict = {}


class QrTemplateSave(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    base_template: str = "custom"
    config: dict = {}


class QrTemplateOut(BaseModel):
    id: Optional[int] = None
    name: str
    base_template: str
    config: dict = {}
    is_system: bool = False

    class Config:
        from_attributes = True


class RefNameCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    parent_id: Optional[int] = None


class CatalogRefOut(BaseModel):
    id: int
    name: str
    parent_id: Optional[int] = None
    full_name: str = ""
    sort_order: int = 0

    class Config:
        from_attributes = True


class CatalogFolderCreate(BaseModel):
    name: str
    sort_order: int = 0


class CatalogFolderOut(BaseModel):
    id: int
    name: str
    sort_order: int

    class Config:
        from_attributes = True


class CatalogItemCreate(BaseModel):
    title: str
    description: str = ""
    category: str = ""
    tags: list[str] = []
    folder_id: Optional[int] = None
    price: float = 0
    image_url: str = ""
    is_available: bool = True
    sort_order: int = 0


class CatalogItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    folder_id: Optional[int] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    is_available: Optional[bool] = None
    is_published: Optional[bool] = None
    sort_order: Optional[int] = None


class CatalogItemOut(BaseModel):
    id: int
    folder_id: Optional[int] = None
    title: str
    description: str
    category: str
    tags: list[str] = []
    price: float
    image_url: str
    is_available: bool
    is_published: bool = True
    deleted_at: Optional[datetime] = None
    sort_order: int


class CatalogBulkIds(BaseModel):
    ids: list[int] = Field(min_length=1)


class CatalogBulkMove(BaseModel):
    ids: list[int] = Field(min_length=1)
    folder_id: Optional[int] = None


class CatalogBulkPublish(BaseModel):
    ids: list[int] = Field(min_length=1)
    is_published: bool


class AnalyticsOut(BaseModel):
    total_leads: int
    leads_by_status: dict[str, int]
    leads_by_source: dict[str, int]
    total_customers: int
    repeat_customers: int
    page_views: int
    conversion_rate: float
    popular_items: list[dict]
    leads_timeline: list[dict] = []
    status_chart: list[dict] = []
    source_chart: list[dict] = []


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    avatar_url: Optional[str] = None


class QrCustomLinkCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    url: str = Field(min_length=4, max_length=1024)


class QrCustomLinkOut(BaseModel):
    id: int
    name: str
    url: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessengerLinkOut(BaseModel):
    whatsapp_url: Optional[str] = None
    telegram_url: Optional[str] = None
    prefilled_message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6)


class CompanyAccessOut(BaseModel):
    company_id: int
    company_name: str
    slug: str
    permissions: dict


class UserMeOut(BaseModel):
    id: int
    email: str
    full_name: str
    phone: str = ""
    avatar_url: str = ""
    job_title: str = ""
    department: str = ""
    is_admin: bool
    is_active: bool
    companies_access: list[CompanyAccessOut] = []


class EmployeeCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: str
    phone: str = ""
    job_title: str = ""
    department: str = ""
    role: str = "employee"
    perm_leads: bool = False
    perm_crm: bool = False
    perm_catalog: bool = False
    perm_qr: bool = False
    perm_settings: bool = False
    perm_employees: bool = False


class EmployeeUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    perm_leads: Optional[bool] = None
    perm_crm: Optional[bool] = None
    perm_catalog: Optional[bool] = None
    perm_qr: Optional[bool] = None
    perm_settings: Optional[bool] = None
    perm_employees: Optional[bool] = None
    is_active: Optional[bool] = None


class EmployeeOut(BaseModel):
    id: int
    user_id: int
    email: str
    full_name: str
    phone: str
    job_title: str
    department: str
    role: str
    perm_leads: bool
    perm_crm: bool
    perm_catalog: bool
    perm_qr: bool
    perm_settings: bool
    perm_employees: bool
    is_active: bool
    is_online: bool = False
    last_seen_at: Optional[datetime] = None
    created_at: datetime


class EmployeeBulkIds(BaseModel):
    ids: list[int] = Field(min_length=1)

    class Config:
        from_attributes = True


class AdminStatsOut(BaseModel):
    users_total: int
    companies_total: int
    companies_active: int
    leads_total: int


class AdminUserOut(BaseModel):
    id: int
    email: str
    full_name: str
    is_admin: bool
    is_active: bool
    is_online: bool = False
    last_seen_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminUserUpdate(BaseModel):
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


class AdminCompanyOut(BaseModel):
    id: int
    slug: str
    name: str
    owner_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AdminCompanyUpdate(BaseModel):
    is_active: Optional[bool] = None
    name: Optional[str] = None
