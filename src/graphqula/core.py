"""Core public interface for the GraphQL execution engine."""

from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

LOGGER = logging.getLogger(__name__)

#: Type for an async function that calculates the value for a deferred field
DeferredField = Callable[..., Awaitable[Any]]


@dataclass(slots=True)
class ExecutionError:
    # TODO rename to not look like an exception class.
    # TODO doesn't this ened line number and whatnot? if you're gonne do somethign, do it properly
    message: str


@dataclass(slots=True)
class ExecutionResult:
    data: dict[str, Any] | None = None
    errors: list[ExecutionError] | None = None


class SchemaFrozenError(Exception):
    """Raised when we try to modify a frozen schema."""


class Schema:
    """A GraphQL schema: a registry of top-level resolvers tagged by operation.

    A schema is *open* while you register entry points — via the ``query`` and
    ``mutation`` decorators, or by folding another schema in with
    ``include_schema``. The first execution freezes it; any later registration
    then raises. A frozen schema is immutable and safe to share as a long-lived
    object.

    Query and mutation share a namespace only within their own kind: ``query``
    and ``mutation`` may each define a field called ``foo``, but two queries
    called ``foo`` collide. The kind is part of a field's identity, which is why
    the two roots are stored separately rather than in one flat map.
    """

    _frozen: bool

    #: Mapping of name -> handler for all mutation fields at the root level.
    #: Note that mutations must always be at the root level, and must always be a deferred field
    #: (not a simple field).
    _root_mutations: dict[str, DeferredField]

    #: Mapping of name -> handler for all query fields at the root level.
    #: Note that root level fields must always be a deferred field (not a simple field).
    _root_queries: dict[str, DeferredField]

    def __init__(self) -> None:
        self._frozen = False
        self._root_queries = {}
        self._root_mutations = {}

    def freeze(self):
        """Explicitly freeze the schema, which will block registering any more fields."""
        if self._frozen:
            LOGGER.warning("Freezing an already-frozen schema.")

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

        May be called directly or used as a decorator.
        """
        if func is None:
            # Decorator was called first before decorating the target
            return lambda f: self._register_root_field(self._root_queries, f)
        return self._register_root_field(self._root_queries, func)

    def register_mutation(
        self, func: DeferredField | None = None
    ) -> DeferredField | Callable[[DeferredField], DeferredField]:
        """Register the handler for a top-level "root" mutation field.

        May be called directly or used as a decorator.

        By convention, fields that modify data are registered as mutations rather than queries
        (similar to the distinction between GET and POST/PATCH in RESTful API's). Stated
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
        variables: dict[str, Any] | None = None,
        operation_name: str | None = None,
        # TODO I think we may nee dmore params here?
    ) -> ExecutionResult:
        """Execute a GraphQL operation against this schema.

        This will implicitly freeze the schema if it's not frozen yet.
        """
        if not self.is_frozen:
            self.freeze()

        if not self._root_queries:
            raise ValueError("A schema must define at least one query field.")
        # TODO tweak response type. want ot just return the data, but also need a way to sideload the known exceptions.
        # TODO note that unhandled exceptions may be propagated too. Or should we catch them all here?
        # TODO build the engine. Unhandled resolver exceptions vs. known errors
        #   sideloaded onto ExecutionResult still needs designing.
        return ExecutionResult(data=None, errors=None)

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
