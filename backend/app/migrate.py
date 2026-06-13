from sqlalchemy import inspect, text

from app.database import engine


def run_migrations():
    """Простые миграции SQLite для локальной разработки."""
    insp = inspect(engine)
    with engine.begin() as conn:
        if "users" in insp.get_table_names():
            cols = {c["name"] for c in insp.get_columns("users")}
            if "phone" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(64) DEFAULT ''"))
            if "is_active" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            if "last_seen_at" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN last_seen_at DATETIME"))
            if "avatar_url" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(512) DEFAULT ''"))
            if "job_title" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN job_title VARCHAR(128) DEFAULT ''"))
            if "department" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN department VARCHAR(128) DEFAULT ''"))

        if "companies" in insp.get_table_names():
            cols = {c["name"] for c in insp.get_columns("companies")}
            if "director_name" not in cols:
                conn.execute(text("ALTER TABLE companies ADD COLUMN director_name VARCHAR(255) DEFAULT ''"))
            if "bin_iin" not in cols:
                conn.execute(text("ALTER TABLE companies ADD COLUMN bin_iin VARCHAR(32) DEFAULT ''"))
            if "legal_address" not in cols:
                conn.execute(text("ALTER TABLE companies ADD COLUMN legal_address VARCHAR(512) DEFAULT ''"))
            if "logo_url" not in cols:
                conn.execute(text("ALTER TABLE companies ADD COLUMN logo_url VARCHAR(512) DEFAULT ''"))

        if "lead_comments" in insp.get_table_names():
            cols = {c["name"] for c in insp.get_columns("lead_comments")}
            if "user_id" not in cols:
                conn.execute(text("ALTER TABLE lead_comments ADD COLUMN user_id INTEGER"))
            if "author_job_title" not in cols:
                conn.execute(text("ALTER TABLE lead_comments ADD COLUMN author_job_title VARCHAR(128) DEFAULT ''"))

        if "catalog_category_refs" in insp.get_table_names():
            cols = {c["name"] for c in insp.get_columns("catalog_category_refs")}
            if "parent_id" not in cols:
                conn.execute(text("ALTER TABLE catalog_category_refs ADD COLUMN parent_id INTEGER"))

        if "catalog_items" in insp.get_table_names():
            cols = {c["name"] for c in insp.get_columns("catalog_items")}
            if "tags" not in cols:
                conn.execute(text("ALTER TABLE catalog_items ADD COLUMN tags TEXT DEFAULT '[]'"))
            if "folder_id" not in cols:
                conn.execute(text("ALTER TABLE catalog_items ADD COLUMN folder_id INTEGER"))
            if "is_published" not in cols:
                conn.execute(text("ALTER TABLE catalog_items ADD COLUMN is_published BOOLEAN DEFAULT 1"))
            if "deleted_at" not in cols:
                conn.execute(text("ALTER TABLE catalog_items ADD COLUMN deleted_at DATETIME"))

        if "customers" in insp.get_table_names():
            cols = {c["name"] for c in insp.get_columns("customers")}
            if "ai_insight" not in cols:
                conn.execute(text("ALTER TABLE customers ADD COLUMN ai_insight TEXT DEFAULT ''"))
            if "is_vip" not in cols:
                conn.execute(text("ALTER TABLE customers ADD COLUMN is_vip BOOLEAN DEFAULT 0"))

        from app.database import Base
        from app import models  # noqa: F401

        for tbl in ("qr_saved_templates", "qr_custom_links", "company_slides", "user_sessions", "customer_insight_logs", "audit_logs"):
            if tbl not in insp.get_table_names():
                Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables[tbl]])

        for table in ("catalog_category_refs", "catalog_tag_refs"):
            if table not in insp.get_table_names():
                from app.database import Base
                from app import models  # noqa: F401

                Base.metadata.create_all(bind=engine, tables=[Base.metadata.tables[table]])

        if "password_reset_tokens" not in insp.get_table_names():
            from app.database import Base
            from app.models import PasswordResetToken

            PasswordResetToken.__table__.create(bind=engine, checkfirst=True)
