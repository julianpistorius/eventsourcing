===========================
Alternative database schema
===========================

Let's say we want the database table to look like stored events, rather than sequenced items.

It's easy to do. Just define a new sequenced item class, e.g. ``StoredEvent`` below.

.. code:: python

    from collections import namedtuple

    StoredEvent = namedtuple('StoredEvent', ['aggregate_id', 'aggregate_version', 'event_type', 'state'])


Then define a suitable active record class.

.. code:: python

    from sqlalchemy.ext.declarative.api import declarative_base
    from sqlalchemy.sql.schema import Column, Sequence, UniqueConstraint
    from sqlalchemy.sql.sqltypes import BigInteger, Integer, String, Text
    from sqlalchemy_utils import UUIDType

    Base = declarative_base()

    class StoredEventTable(Base):
        # Explicit table name.
        __tablename__ = 'stored_events'

        # Unique constraint.
        __table_args__ = UniqueConstraint('aggregate_id', 'aggregate_version', name='stored_events_uc'),

        # Primary key.
        id = Column(Integer, Sequence('stored_event_id_seq'), primary_key=True)

        # Sequence ID (e.g. an entity or aggregate ID).
        aggregate_id = Column(UUIDType(), index=True)

        # Position (timestamp) of item in sequence.
        aggregate_version = Column(BigInteger(), index=True)

        # Type of the event (class name).
        event_type = Column(String(100))

        # State of the item (serialized dict, possibly encrypted).
        state = Column(Text())

Then redefine the application class to use the new sequenced item and active record classes.


.. code:: python

    from eventsourcing.application.policies import PersistencePolicy
    from eventsourcing.infrastructure.eventsourcedrepository import EventSourcedRepository
    from eventsourcing.infrastructure.eventstore import EventStore
    from eventsourcing.infrastructure.sqlalchemy.activerecords import SQLAlchemyActiveRecordStrategy
    from eventsourcing.infrastructure.sequenceditem import SequencedItem
    from eventsourcing.infrastructure.sequenceditemmapper import SequencedItemMapper
    from eventsourcing.example.domainmodel import Example, create_new_example
    from eventsourcing.domain.model.events import VersionedEntityEvent


    class Application(object):
        def __init__(self, datastore):
            self.event_store = EventStore(
                active_record_strategy=SQLAlchemyActiveRecordStrategy(
                    datastore=datastore,
                    active_record_class=StoredEventTable,
                    sequenced_item_class=StoredEvent,
                ),
                sequenced_item_mapper=SequencedItemMapper(
                    sequenced_item_class=StoredEvent,
                    sequence_id_attr_name='entity_id',
                    position_attr_name='entity_version',
                )
            )
            self.example_repository = EventSourcedRepository(
                event_store=self.event_store,
                mutator=Example.mutate,
            )
            self.persistence_policy = PersistencePolicy(self.event_store, event_type=VersionedEntityEvent)

        def create_example(self, foo):
            return create_new_example(foo=foo)

        def close(self):
            self.persistence_policy.close()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.close()


Set up the database.

.. code:: python

    from eventsourcing.infrastructure.sqlalchemy.datastore import SQLAlchemySettings, SQLAlchemyDatastore
    from eventsourcing.infrastructure.sqlalchemy.activerecords import SqlIntegerSequencedItem

    datastore = SQLAlchemyDatastore(
        base=Base,
        settings=SQLAlchemySettings(uri='sqlite:///:memory:'),
    )

    datastore.setup_connection()
    datastore.setup_tables()


Then you can use the application as before, and your events will be stored as "stored events".

.. code:: python

    with Application(datastore) as app:

        entity = app.create_example(foo='bar1')

        assert entity.id in app.example_repository

        assert app.example_repository[entity.id].foo == 'bar1'

        entity.foo = 'bar2'

        assert app.example_repository[entity.id].foo == 'bar2'

        # Discard the entity.
        entity.discard()
        assert entity.id not in app.example_repository

        try:
            app.example_repository[entity.id]
        except KeyError:
            pass
        else:
            raise Exception('KeyError was not raised')