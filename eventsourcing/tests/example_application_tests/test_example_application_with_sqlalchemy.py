from eventsourcing.application.example.base import ExampleApplication
from eventsourcing.infrastructure.datastore.sqlalchemy import SQLAlchemyDatastoreStrategy, SQLAlchemySettings
from eventsourcing.infrastructure.stored_event_repos.with_sqlalchemy import SQLAlchemyStoredEventRepository, \
    SqlStoredEvent
from eventsourcing.tests.example_application_tests.base import ExampleApplicationTestCase
from eventsourcing.tests.stored_event_repository_tests.base_sqlalchemy import SQLAlchemyRepoTestCase


class TestExampleApplicationWithSQLAlchemy(SQLAlchemyRepoTestCase, ExampleApplicationTestCase):

    def setUp(self):
        self.datastore_strategy = create_sqlalchemy_datastore_strategy()
        self.datastore_strategy.setup_connection()
        self.datastore_strategy.setup_tables()
        super(TestExampleApplicationWithSQLAlchemy, self).setUp()

    def tearDown(self):
        super(TestExampleApplicationWithSQLAlchemy, self).tearDown()
        self.datastore_strategy.drop_tables()
        self.datastore_strategy.drop_connection()


def create_example_application_with_sqlalchemy(db_session, cipher=None):
    return ExampleApplication(
        stored_event_repository=SQLAlchemyStoredEventRepository(
            stored_event_table=SqlStoredEvent,
            db_session=db_session,
        ),
        cipher=cipher,
    )


def create_sqlalchemy_datastore_strategy(uri=None):
    return SQLAlchemyDatastoreStrategy(
        settings=SQLAlchemySettings(uri=uri),
        tables=(SqlStoredEvent,),
    )
