from app.routes.auth import auth_bp
from app.routes.expenses import expenses_bp
from app.routes.summary import summary_bp
from app.routes.health import health_bp

__all__ = ["auth_bp", "expenses_bp", "summary_bp", "health_bp"]
