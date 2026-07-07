"""Tools for working with the Document AST from the `graphql-core` library."""

from typing import Any, Optional

from graphql import DocumentNode

from .._structures.document import Operation, OperationKind, FieldGroup, ResponseField

# TODO needs tests for everything
# TODO rename to be private


# TODO get a standard union type for var values based on recursive dict of RawLeafType
# TODO rename mebbe?
async def get_operation(
    query_ast: DocumentNode, operation_name: Optional[str], variables: dict[str, Any]
) -> Operation:
    """Extract the named operation from this document, converting it to a cleaner data structure."""
    # FIXME just build a fake operation for now
    return Operation(
        kind=OperationKind.QUERY,
        name=operation_name,
        children=FieldGroup(
            fields=[
                ResponseField(
                    name_in_schema="hero", name_in_response="hero", arguments=dict()
                )
            ]
        ),
    )
