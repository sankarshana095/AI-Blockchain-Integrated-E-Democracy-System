from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.auth_service import login_user, logout_current_user
from services.booth_session_service import unregister_voting_terminal

bp = Blueprint("auth", __name__, url_prefix="/auth")


# -----------------------------
# Login
# -----------------------------
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            user = login_user(email, password)
            role = user.get("role")

            # -----------------------------
            # Role-based redirect
            # -----------------------------
            if role == "CITIZEN":
                return redirect(url_for("citizen.dashboard"))

            elif role == "PO":
                # Presiding Officer → Booth control
                return redirect(url_for("presiding_officer.dashboard"))

            elif role in {"ELECTED_REP", "OPPOSITION_REP"}:
                return redirect(url_for("representative.dashboard"))

            else:
                # CEC, CEO, DEO, RO, ERO, BLO
                return redirect(url_for("election_commission.dashboard"))

        except Exception as e:
            flash(str(e), "error")

    return render_template("auth/login.html")


# -----------------------------
# Logout
# -----------------------------
@bp.route("/logout")
def logout():
    # 🔑 IMPORTANT: Release voting terminal on logout
    booth_id = session.get("booth_id")
    if booth_id:
        unregister_voting_terminal(booth_id)

    logout_current_user()
    return redirect(url_for("auth.login"))
