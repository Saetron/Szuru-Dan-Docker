import os
from pathlib import Path
from flask import Flask, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
from config import config
from routes.posts import posts_bp
from routes.tags import tags_bp
from routes.favorites import favorites_bp
from routes.users import users_bp
from routes.proxy import proxy_bp
from routes.admin import admin_bp

VERSION_FILE = Path(__file__).parent / "VERSION"
__version__ = VERSION_FILE.read_text().strip() if VERSION_FILE.exists() else "0.1.2"


def create_app():
    app = Flask(__name__)

    # Support reverse proxy headers for dynamic scheme/host detection
    app.wsgi_app = ProxyFix(
        app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
    )

    # Health check endpoint
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify(
            {
                "status": "healthy",
                "version": __version__,
                "backend_url": config.SZURUBOORU_URL,
                "reverse_proxy_mode": config.REVERSE_PROXY_MODE,
            }
        ), 200

    # Register blueprints
    app.register_blueprint(posts_bp)
    app.register_blueprint(tags_bp)
    app.register_blueprint(favorites_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(proxy_bp)
    app.register_blueprint(admin_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", config.SERVICE_PORT))
    app.run(debug=config.DEBUG, host="0.0.0.0", port=port)
