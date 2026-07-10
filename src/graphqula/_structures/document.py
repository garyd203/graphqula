"""Clean representation of a valid GraphQL Document and it's Operation's.

The module is deliberately decoupled from `graphql-core`, and is intended to provide an
independent representation that is easy to work with when executing the request.
"""

# TODO shiould this be dumb data containers, or do we want ot add (our very specific?) logic onto the classes?
# TODO i think we at least want factory helpers to simplify construction for common cases
# TODO needs tests for constructing everything, but they're fairly minimal
# TODO needs tests for any helper methods

from __future__ import annotations

import enum
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from typing import Optional
from typing import Sequence


class OperationKind(enum.Enum):
    """The type of operation - that is, which root the operation runs against."""

    #: In a query, all fields may be evaluated in parallel. By convention these are used for read-only data.
    QUERY = "query"

    #: In a mutation, if there's multiple root-level fields they must be evaluated sequentially. By convention these are used for writing data.
    MUTATION = "mutation"

    #: Subscription fields provide a streaming response type.
    SUBSCRIPTION = "subscription"


@dataclass(frozen=True)
class Document:
    """Top-level GraphQL document."""

    #: All operations in this document, keyed by the operation name (or potentially None if it is the sole un-named operation).
    #: A document may define several named operations, even though in practice exactly one will be selected for
    #: execution
    # TODO wrap in MappingProxyType when we create it, for actual immutability
    operations: Mapping[Optional[str], Operation]


@dataclass(frozen=True)
class Operation:
    """An executable operation."""

    # TODO can we refactor this so that operation is related to ResponseField?

    kind: OperationKind

    #: The operation's name, if it's not anonymous.
    name: Optional[str]

    #: Root fields that need to be evaluated. Evaluation needs to follow the correct semantics for `kind` (ie. parallel vs sequential)
    children: FieldGroup


@dataclass(frozen=True)
class ResponseField:
    """A single field for the response.

    This may represent either a leaf node with a single value (eg. enum or string) or a nested object.
    """

    #: The field name as defined in the schema.
    name_in_schema: str

    #: The name this field is mapped to in the response.
    name_in_response: str

    #: Argument values that must be used to evaluate this field.
    # TODO wrap in MappingProxyType when we create it, for actual immutability
    arguments: Mapping[str, Any]

    #: Child fields iff this field is an object.
    children: Optional[FieldGroup] = None

    def is_leaf_node(self) -> bool:
        """Whether this field is a leaf node in the response"""
        return self.children is None


@dataclass(frozen=True)
class FieldGroup:
    """A collection of subclass-dependent fields to be evaluated on an object for inclusion in the response."""

    #: Ordered list of fields to be evaluated
    # TODO at some point this needs to be a dictionary by response subclass. Note that it will still need to be sorted by order of declaration
    # TODO it'd be good if this was immutable - a set
    fields: list[ResponseField]

    def fields_for_type(self) -> Sequence[ResponseField]:
        """Get all fields that need to be returned for this concrete response type.

        The fields are sorted in the order they should be returned in the result.
        """
        # FIXME need a compulsory parameter for the actual schema subclass.
        #   Nedd a way to deal with the secanrio when we don't have one
        return self.fields
