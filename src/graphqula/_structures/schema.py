"""Classes to represent a GraphQL Schema.

The module is deliberately decoupled from `graphql-core`, and is intended to provide an
independent representation of our internal objects that are used to implement a schema
and use it for executing requests.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..types import DeferredField


@dataclass(frozen=True)
class DeferredFieldData:
    """Schema metadata for a deferred field, that needs to execute a custom function in order to get the result."""

    #: Function used to evaluate the value for the field
    evaluator: DeferredField

    #: Type of the value returned
    # TODO determine if this is a python type, or a schema type -> schema type i think
    # TODO can probably do a better job of the Any type
    result_type: Any

    # TODO dependencies
    # TODO params
