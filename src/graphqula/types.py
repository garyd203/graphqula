"""General-purpose shared types."""

from __future__ import annotations

from enum import Enum

from typing import TypeAlias, Union, Callable, Awaitable, Any

#: Type of any raw non-structured value that is passed over-the-wire in a GraphQL
#: document, variable or response. This is any of the built-in scalars + any enum.
#: Note that this represents data that has not been converted to any custom scalar
#: type.
RawLeafType: TypeAlias = Union[bool | float | int | str, Enum]

#: Primitive types that can appear as a JSON value.
JSONPrimitive: TypeAlias = bool | float | int | str

#: Structured types that can appear as a JSON value.
JSONValue: TypeAlias = JSONPrimitive | None | list["JSONValue"] | dict[str, "JSONValue"]

#: A top-level JSON object.
#: We intentionally don't include None (this should be a specific type declaration if
#: it is intended), or lists (since we don't use/support top-level JSON lists).
JSONDict: TypeAlias = dict[str, JSONValue]

#: Type for a function that calculates the value for a deferred field
DeferredField = Callable[..., Awaitable[Any]]
