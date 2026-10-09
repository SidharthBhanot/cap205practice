"""Run from the project root: python -m backend.init_db"""
from .database import init_db, make_engine


def main():
    engine = make_engine()
    init_db(engine)
    print(f"Database initialized: {engine.url}")


if __name__ == "__main__":
    main()
