"""Classes to represent a GraphQL Schema.

The module is deliberately decoupled from `graphql-core`, and is intended to provide an
independent representation of our internal objects that are used to implement a schema
and use it for executing requests.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..types import DeferredField
from ..types import RawLeafType

# TODO I think we want these to be full classes, no poiint trying to make it abstract and poiintlessly decoupled.
#   probably means evaluation will end up in here


@dataclass(frozen=True)
class DeferredFieldData:
    """Schema metadata for a deferred field, that needs to execute a custom function in order to get the result."""

    #: Function used to evaluate the value for the field
    evaluator: DeferredField

    #: Type of the value returned, expressed as the SDL (GraphQL Schema) type
    # TODO RawLeafType is entirely the wrong type
    # TODO that descritpiin is still wrong - iyt;s nto the actual SDL type, it's the python type that maps to the SDL type
    # TODO also note about it being the most abstract definition of that type
    result_type_sdl: type[RawLeafType]

    # TODO result_type_json
    # TODO dependencies
    # TODO params
