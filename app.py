from flask import Flask, render_template
from config import Config


# Blueprints
from routes.auth_routes import bp as auth_bp
from routes.citizen_routes import bp as citizen_bp
from routes.representative_routes import bp as representative_bp
from routes.election_commission_routes import bp as commission_bp
from routes.ledger_routes import bp as ledger_bp
from routes.admin_routes import bp as admin_bp
from routes.public_routes import bp as public_bp
from routes.evote_routes import bp as evote_bp
from routes.presiding_officer_routes import bp as po_bp
from routes.verify_vote_routes import bp as verify_vote_bp


def create_app():
    import os
    from dotenv import load_dotenv
    load_dotenv()
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "templates"),
        static_folder=os.path.join(BASE_DIR, "static")
    )

    app.config["SECRET_KEY"] = Config.SECRET_KEY
    app.config["DEBUG"] = Config.DEBUG

    # -----------------------------
    # Register Blueprints
    # -----------------------------
    app.register_blueprint(auth_bp)
    app.register_blueprint(citizen_bp)
    app.register_blueprint(representative_bp)
    app.register_blueprint(commission_bp)
    app.register_blueprint(ledger_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(evote_bp)
    app.register_blueprint(po_bp)
    app.register_blueprint(verify_vote_bp)




    # -----------------------------
    # Error Handlers
    # -----------------------------
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("errors/500.html"), 500

    return app


# -----------------------------
# App Entry Point
# -----------------------------

app = create_app()

if __name__ == "__main__":
    app.run(debug=Config.DEBUG)
