from ecom_agent_os.database.models import Base
from ecom_agent_os.database.session import engine


def main():

    print("Creating database tables...")

    Base.metadata.create_all(bind=engine)

    print("Database tables created.")


if __name__ == "__main__":
    main()
