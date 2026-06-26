"""Tools for working with the Schema and Document AST's from `graphql-core` library."""

from typing import Any, Optional

from graphql import DocumentNode

from ._document import Operation, OperationKind, FieldGroup, ResponseField


# TODO gte a standard union type for var values mebbe. is it worth it?
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
