from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, SessionLocal, engine
from app.migrate import run_migrations
from app.routers import admin, analytics, auth, catalog, companies, company_slides, customers, employees, leads, public, qr, uploads
from app.spa import mount_spa

app = FastAPI(
    title="./dot Platform API",
    description="MVP цифровой платформы для малого и среднего бизнеса (Казахстан)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(company_slides.router)
app.include_router(leads.router)
app.include_router(customers.router)
app.include_router(catalog.router)
app.include_router(analytics.router)
app.include_router(analytics.overview_router)
app.include_router(qr.router)
app.include_router(public.router)
app.include_router(employees.router)
app.include_router(admin.router)
app.include_router(catalog.admin_router)
app.include_router(uploads.router)


@app.on_event("startup")
def startup():
    from app.bootstrap import ensure_demo_data, ensure_superadmin

    Base.metadata.create_all(bind=engine)
    run_migrations()
    with SessionLocal() as db:
        ensure_superadmin(db)
        ensure_demo_data(db)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "dot-platform"}


mount_spa(app)
