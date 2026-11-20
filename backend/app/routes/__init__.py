def register_routes(app):
    from .health import bp as health_bp
    from .puzzles import bp as puzzles_bp
    from .solve import bp as solve_bp

    for bp in (health_bp, puzzles_bp, solve_bp):
        app.register_blueprint(bp, url_prefix="/api")
