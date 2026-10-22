from datetime import datetime, date
from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.models import Expense
from app.auth import jwt_required

expenses_bp = Blueprint("expenses", __name__, url_prefix="/expenses")

def parse_date(date_str: str) -> date | None:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

def validate_amount(amount: any) -> tuple[float | None, str | None]:
    if amount is None or isinstance(amount, bool) or not isinstance(amount, (int, float)):
        return None, "Amount must be a positive number"
    if amount <= 0:
        return None, "Amount must be a positive number"
    return float(amount), None

@expenses_bp.post("")
@jwt_required
def create_expense():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be valid JSON"}), 400

    amount_raw = data.get("amount")
    category_raw = data.get("category")
    note_raw = data.get("note")
    date_raw = data.get("date")

    amount, amount_err = validate_amount(amount_raw)
    if amount_err:
        return jsonify({"error": amount_err}), 400

    if not category_raw or not isinstance(category_raw, str) or not category_raw.strip():
        return jsonify({"error": "Category is required and must be a non-empty string"}), 400

    if not date_raw or not isinstance(date_raw, str):
        return jsonify({"error": "Date is required and must be in YYYY-MM-DD format"}), 400

    parsed_date = parse_date(date_raw.strip())
    if parsed_date is None:
        return jsonify({"error": "Date is required and must be in YYYY-MM-DD format"}), 400

    note = None
    if note_raw is not None:
        if not isinstance(note_raw, str):
            return jsonify({"error": "Note must be a string if provided"}), 400
        note = note_raw.strip()

    expense = Expense(
        user_id=g.current_user_id,
        amount=amount,
        category=category_raw.strip(),
        note=note,
        date=parsed_date,
    )

    db.session.add(expense)
    db.session.commit()

    return jsonify(expense.to_dict()), 201

@expenses_bp.get("")
@jwt_required
def list_expenses():
    page_param = request.args.get("page", 1)
    per_page_param = request.args.get("per_page", 10)

    try:
        page = int(page_param)
        if page < 1:
            return jsonify({"error": "Page must be a positive integer"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Page must be a positive integer"}), 400

    try:
        per_page = int(per_page_param)
        if per_page < 1 or per_page > 100:
            return jsonify({"error": "Per_page must be an integer between 1 and 100"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Per_page must be an integer between 1 and 100"}), 400

    stmt = db.select(Expense).filter_by(user_id=g.current_user_id).order_by(
        Expense.date.desc(), Expense.id.desc()
    )

    pagination = db.paginate(stmt, page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": [item.to_dict() for item in pagination.items],
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    }), 200

@expenses_bp.get("/<int:expense_id>")
@jwt_required
def get_expense(expense_id: int):
    expense = db.session.execute(
        db.select(Expense).filter_by(id=expense_id, user_id=g.current_user_id)
    ).scalar_one_or_none()
    if expense is None:
        return jsonify({"error": "Expense not found"}), 404

    return jsonify(expense.to_dict()), 200

@expenses_bp.route("/<int:expense_id>", methods=["PUT", "PATCH"])
@jwt_required
def update_expense(expense_id: int):
    expense = db.session.execute(
        db.select(Expense).filter_by(id=expense_id, user_id=g.current_user_id)
    ).scalar_one_or_none()
    if expense is None:
        return jsonify({"error": "Expense not found"}), 404

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be valid JSON"}), 400

    if not data:
        return jsonify({"error": "No update fields provided"}), 400

    if "amount" in data:
        amount, amount_err = validate_amount(data["amount"])
        if amount_err:
            return jsonify({"error": amount_err}), 400
        expense.amount = amount

    if "category" in data:
        cat = data["category"]
        if not cat or not isinstance(cat, str) or not cat.strip():
            return jsonify({"error": "Category must be a non-empty string"}), 400
        expense.category = cat.strip()

    if "date" in data:
        date_raw = data["date"]
        if not date_raw or not isinstance(date_raw, str):
            return jsonify({"error": "Date must be in YYYY-MM-DD format"}), 400
        parsed = parse_date(date_raw.strip())
        if parsed is None:
            return jsonify({"error": "Date must be in YYYY-MM-DD format"}), 400
        expense.date = parsed

    if "note" in data:
        note_raw = data["note"]
        if note_raw is not None and not isinstance(note_raw, str):
            return jsonify({"error": "Note must be a string or null"}), 400
        expense.note = note_raw.strip() if isinstance(note_raw, str) else None

    db.session.commit()
    return jsonify(expense.to_dict()), 200

@expenses_bp.delete("/<int:expense_id>")
@jwt_required
def delete_expense(expense_id: int):
    expense = db.session.execute(
        db.select(Expense).filter_by(id=expense_id, user_id=g.current_user_id)
    ).scalar_one_or_none()
    if expense is None:
        return jsonify({"error": "Expense not found"}), 404

    db.session.delete(expense)
    db.session.commit()

    return "", 204
