import sys
from app.app import create_app
from app.db import init_db, seed_db

def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else ".dogfood.toml"
    app = create_app(config_path)
    with app.app_context():
        init_db()
        seed_db()
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=False)

if __name__ == "__main__":
    main()
