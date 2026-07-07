"""Core public interface for the GraphQL execution engine."""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from typing import Any

from graphql import GraphQLField, GraphQLObjectType, GraphQLSchema, GraphQLString
from graphql import parse as parse_graphql
from graphql import validate as validate_graphql

from ._ast.document import get_operation
from .error_handler import BaseErrorHandler, FastFailErrorHandler
from ._evaluation import evaluate_operation
from .types import JSONDict
from ._structures.schema import DeferredFieldData
from .exceptions import SchemaFrozenError
from .types import DeferredField

LOGGER = logging.getLogger(__name__)

# TODO needs tests for almost everything


# TODO dataclass it
class Schema:
    """A GraphQL schema representing query + mutation root fields with rich nested response types.

    The schema is modifiable whilst root fields are being registered. Once it is first
    used (for execution or otherwise) then the schema is frozen and cannot be modified.
    """

    #: The `graphql-core` AST for the schema, created lazily on demand.
    #: This is valid once the schema is frozen.
    _ast: GraphQLSchema | None

    #: Whether this schema has been frozen, and hence may not be modified.
    _frozen: bool

    #: Metadata for all root level mutations, keyed by the field's schema name.
    #: This is valid once the schema is frozen.
    _mutations: dict[str, DeferredFieldData] | None

    #: Metadata for all root level queries, keyed by the field's schema name.
    #: This is valid once the schema is frozen.
    _queries: dict[str, DeferredFieldData] | None

    #: Mapping of {schema_name: handler_function} for all mutation fields at the root level.
    #: Note that mutations must always be at the root level, and must always be a deferred field
    #: (not a simple field).
    # todo call these raw
    _root_mutations: dict[str, DeferredField]

    #: Mapping of {schema_name: handler_function} for all query fields at the root level.
    #: Note that root level fields must always be a deferred field (not a simple field).
    # todo call these raw
    _root_queries: dict[str, DeferredField]

    def __init__(self) -> None:
        self._ast = None
        self._frozen = False
        self._mutations = None
        self._queries = None
        self._root_queries = {}
        self._root_mutations = {}

    def freeze(self):
        """Explicitly freeze the schema, which will prevent any more fields from being registered.

        Internal data structures are then constructed.

        NB: This function needs to be non-async so it can be easily called by
        module-level code as users build up a schema.
        """
        if self._frozen:
            LOGGER.warning("Freezing an already-frozen schema.")

        # TODO it'd be good to have a proper lock around this. we want to avoid data
        #   structures being updated concurrently whilst we're creating them
        #   -> coudl jsut say it's not threadsafe? But need to deal with it being called by parallel calls to execute
        self._frozen = True

        # TODO Create internal schema representation using our own (actually useful) data structures
        # TODO this should actually fully process the linked field to pull out types and other
        #   internal structure, then store that rather than the raw functon. Then (maybe) update
        #   include_schema as well to use the internal structure.
        # TODO build the type registry here so the whole type graph can be validated
        self._build_metadata()

        # Create internal AST representation
        self._build_ast()

        # TODO need to validate the AST - see `graphql.validate_schema`

    @property
    def is_frozen(self) -> bool:
        """Whether this schema is frozen, meaning no more fields may be registered."""
        return self._frozen

    def register_query(
        self, func: DeferredField | None = None
    ) -> DeferredField | Callable[[DeferredField], DeferredField]:
        """Register the handler for a top-level "root" query field.

        May be called directly or used as a decorator. Returns the original function.
        """
        if func is None:
            # Decorator was called first before decorating the target
            return lambda f: self._register_root_field(self._root_queries, f)
        return self._register_root_field(self._root_queries, func)

    def register_mutation(
        self, func: DeferredField | None = None
    ) -> DeferredField | Callable[[DeferredField], DeferredField]:
        """Register the handler for a top-level "root" mutation field.

        May be called directly or used as a decorator. Returns the original function.

        By convention, fields that modify data are registered as mutations rather than queries
        (similar to the distinction between GET vs POST/PATCH in RESTful API's). Stated
        more precisely, a single GraphQL request that requests multiple top-level mutation fields
        will process each field sequentially, whereas query fields are processed in parallel.
        """
        if func is None:
            # Decorator was called first before decorating the target
            return lambda f: self._register_root_field(self._root_mutations, f)
        return self._register_root_field(self._root_mutations, func)

    def include_schema(self, other: Schema) -> Schema:
        """Merge all the schema data from the other schema into this schema.

        This copies across root queries and mutations, and other internal data.

        Additionally, the other schema is frozen (if it isn't already) so that the user can't inadvertently register
        more fields in the other schema and believe they are also in this schema.
        """
        # TODO include isnt quite the right word - implies a dynamic linking, rather than an import or merge
        if self.is_frozen:
            raise SchemaFrozenError("Cannot modify a frozen schema.")
        other.freeze()

        for target, source in (
            (self._root_queries, other._root_queries),
            (self._root_mutations, other._root_mutations),
        ):
            if shared_keys := target.keys() & source.keys():
                raise ValueError(f"Merge will create duplicate fields {shared_keys}.")
            target.update(source)
        return self

    async def execute(
        self,
        document: str,
        *,
        # TODO we will eventually need more parameters here
        error_handler: BaseErrorHandler | None = None,
        operation_name: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> JSONDict:
        """Execute a GraphQL operation against this schema, returning just the result data.

        Any errors during field evaluation will be reported to `error_handler`.
        The caller should extract them from there for returning to the GraphQL client,
        if necessary.

        This will implicitly freeze the schema if it's not frozen yet.

        Raises:
            Any unhandled errors during field evaluation.
        """
        # Executing a request will automatically freeze the schema and build internal structures
        if not self.is_frozen:
            LOGGER.debug("Implicitly freezing schema at execution time")
            # TODO avoid blocking the async loop - wrap in an async call
            self.freeze()

        # Ensure an error handler is configured
        if error_handler is None:
            # Production-ready GraphQL requests all go through a well-defined binding
            # which explicitly passes a proper error tracker. OTOH code that directly
            # calls `execute()` without setting an error handler is internal or unit
            # test code, so it's reasonable to default to a fail-fast error handler
            # that enables straightforward developer experience for those use cases.
            LOGGER.info("Defaulting to use a fast-fail error handler.")
            error_handler = FastFailErrorHandler()

        LOGGER.debug("Handling errors with %s", error_handler)
        error_handler.bind_to_request()

        # Parse and validate the document
        # FIXME not async - use threadpool and async to_thread or equivalent
        # TODO handle errors
        # TODO set max_tokens for safety
        query_ast = parse_graphql(document)

        # FIXME not async
        # TODO handle errors
        # TODO set max_errors
        # TODO do we need to set rules
        # TODO do we need to set type_info
        assert self._ast is not None, "Created when the schema was frozen"
        _validation_errors = validate_graphql(self._ast, query_ast)

        operation = await get_operation(query_ast, operation_name, variables or {})

        # Generate response data for the selected operation
        # TODO choose self._queries or self._mutations based on op kind
        assert self._queries is not None, "Created when the schema was frozen"
        response = await evaluate_operation(operation, self._queries, error_handler)
        return response

    def _build_ast(self) -> None:
        """Build an AST representation of this schema."""
        if not self.is_frozen:
            raise Exception("Schema should be frozen before trying to build an AST.")

        # FIXME build a fake schema
        ast = GraphQLSchema(
            query=GraphQLObjectType(
                "Query", fields={"hero": GraphQLField(GraphQLString)}
            )
        )

        self._ast = ast

    def _build_metadata(self):
        """Construct internal metadata objects for this schema."""
        if not self.is_frozen:
            raise Exception("Schema should be frozen before trying to build metadata.")

        mutations = {}
        queries = {}

        # TODO actually populate the mappings. NB: This is derived from the raw mappings, not from the AST schema
        # TODO use the beastie to write tests and build this up

        # FIXME build a fake schema
        async def _fake_get_hero() -> str:
            return "R2-D2"

        queries["hero"] = DeferredFieldData(evaluator=_fake_get_hero, result_type=str)

        self._mutations = mutations
        self._queries = queries

    def _register_root_field(
        self, field_registry: dict[str, DeferredField], func: DeferredField
    ) -> DeferredField:
        # Checks
        if self.is_frozen:
            raise SchemaFrozenError(
                "Cannot register a new root field on a frozen schema."
            )

        if not inspect.iscoroutinefunction(func):
            raise TypeError(
                f"Deferred field handler {func.__name__!r} must be an async function."
            )

        # Register the function
        # TODO we will want to customise the field name at some point
        field_name = func.__name__
        if field_name in field_registry:
            raise ValueError(f"Duplicate field {field_name}.")
        field_registry[field_name] = func

        return func
