import re
import calendar
from datetime import date
from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.models import Expense
from app.auth import jwt_required

summary_bp = Blueprint("summary", __name__, url_prefix="/summary")

MONTH_REGEX = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")

@summary_bp.get("")
@jwt_required
def get_summary():
    month_str = request.args.get("month")
    if not month_str:
        return jsonify({"error": "Query parameter 'month' is required in YYYY-MM format"}), 400

    match = MONTH_REGEX.match(month_str.strip())
    if not match:
        return jsonify({"error": "Invalid month format. Expected YYYY-MM (e.g. 2026-05)"}), 400

    year = int(match.group(1))
    month_num = int(match.group(2))
    _, last_day = calendar.monthrange(year, month_num)

    start_date = date(year, month_num, 1)
    end_date = date(year, month_num, last_day)

    stmt = db.select(Expense).filter(
        Expense.user_id == g.current_user_id,
        Expense.date >= start_date,
        Expense.date <= end_date,
    )
    expenses = db.session.execute(stmt).scalars().all()

    total = 0.0
    by_category: dict[str, float] = {}

    for exp in expenses:
        amt = float(exp.amount)
        total += amt
        by_category[exp.category] = round(by_category.get(exp.category, 0.0) + amt, 2)

    return jsonify({
        "month": month_str.strip(),
        "total": round(total, 2),
        "by_category": by_category,
    }), 200
