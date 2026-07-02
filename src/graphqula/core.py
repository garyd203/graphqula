"""Core public interface for the GraphQL execution engine."""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from typing import Any
from graphql import GraphQLSchema

from .error_handler import FastFailErrorHandler, BaseErrorHandler
from .exceptions import SchemaFrozenError
from .types import DeferredField

LOGGER = logging.getLogger(__name__)

# TODO needs tests for almost everything


# TODO dataclass it
class Schema:
    """A GraphQL schema representing query + mutation root fields with rich nested response types.

    The schema is mutable whilst root fields are being registered. Once it is first
    used (for execution or otherwise) then the schema is frozen and cannot be modified.
    """

    #: The `graphql-core` AST for the schema, created lazily on demand.
    _ast: GraphQLSchema | None

    # TODO needs doc
    _frozen: bool

    #: Mapping of schema_name -> handler for all mutation fields at the root level.
    #: Note that mutations must always be at the root level, and must always be a deferred field
    #: (not a simple field).
    # todo call these raw
    _root_mutations: dict[str, DeferredField]

    #: Mapping of schema_name -> handler for all query fields at the root level.
    #: Note that root level fields must always be a deferred field (not a simple field).
    # todo call these raw
    _root_queries: dict[str, DeferredField]

    def __init__(self) -> None:
        self._ast = None
        self._frozen = False
        self._root_queries = {}
        self._root_mutations = {}

    def freeze(self):
        """Explicitly freeze the schema, which will block registering any more fields."""
        if self._frozen:
            LOGGER.warning("Freezing an already-frozen schema.")

        # TODO this should actually fully process the linked field to pull out types and other
        #   internal structure, then store that ratehr than the raw functon. Then (maybe) update
        #   include_schema as well to use the internal structure.
        # TODO build the type registry here (walk resolver return types) so the
        #   type graph can be validated and emitted as SDL. Deferred until
        #   type-name resolution lands.

        self._frozen = True

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

    async def initialise(self):
        """Ensure once-off initialisation has all been completed."""
        # Freeze the schema, before we build internal structures
        if not self.is_frozen:
            LOGGER.debug("Implicitly freezing schema at initialisation time")
            self.freeze()

        # TODO Create internal schema representation using our own (actually useful) data structures

        # Create internal AST representation
        if self._ast is None:
            self._ast = await self._build_ast()

        # TODO need to validate the schema - see `graphql.validate_schema`

    async def execute(
        self,
        document: str,
        *,
        # TODO we will eventually need more parameters here
        error_handler: BaseErrorHandler | None = None,
        operation_name: str | None = None,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Execute a GraphQL operation against this schema, returning just the result data.

        Any errors during field evaluation will be reported to `error_handler`.
        The caller should extract them from there for returning to the GraphQL client,
        if necessary.

        This will implicitly freeze the schema if it's not frozen yet.

        Raises:
            Any unhandled errors during field evaluation.
        """
        # Executing a request will automatically freeze the schema and build internal structures
        await self.initialise()

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

        # TODO note that unhandled exceptions may be propagated out of this function
        # TODO actually execute the query :-)
        return None  # FIXME

    async def _build_ast(self) -> GraphQLSchema:
        """Build an AST representation of the root fields in this schema."""
        # TODO dont like this structure. can we do property access or soemthign

        # TODO needs sto be frozen

        # TODO will prob end up compling the gql-core schema object, and this check will fall out as part of that.
        if not self._root_queries:
            # TODO need a test for this
            raise ValueError("A schema must define at least one query field.")

        raise NotImplementedError("_build_ast")

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
