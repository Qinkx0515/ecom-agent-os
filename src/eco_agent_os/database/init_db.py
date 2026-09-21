from database.models import Base
from database.session import engine


def main():

    print("Creating database tables...")

    Base.metadata.create_all(
        bind=engine
    )

    print("Database tables created.")


if __name__ == "__main__":
    main()