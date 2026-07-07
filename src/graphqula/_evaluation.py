"""Tools to evaluate field values from their document and matching schema specification."""

from .error_handler import ErrorHandler
from ._structures.schema import DeferredFieldData
from ._document import Operation, ResponseField
from .types import JSONDict, JSONValue

# TODO needs tests for everything


async def evaluate_operation(
    operation: Operation,
    schema_fields: dict[str, DeferredFieldData],
    error_handler: ErrorHandler,
) -> JSONDict:
    """Evaluate all selected fields for an operation.

    Params:
        error_handler: Controls how to handle errors.
        operation: The operation to evaluate.
        schema_fields: All root fields in the Schema that match this operation kind
            (ie. query or mutation), keyed by the field's schema name.

    Returns:
        A complete response for this operation, expressed as a dictionary that is
        directly JSON-compatible and uses response_field_name as the keys. The
        iteration order of the dictionary corresponds to the selection order of the
        fields, and hence reflects the order in which the fields should appear in a
        stringified response.

    Raises:
        Any errors evaluating the operation, unless they are suppressed by
        `error_handler`.
    """

    # todo Response types are basic JSON-compatible primitives that need no further conversin/coercion, you just send them mindlessly to `json.dumps`. This is achieved by:
    #   simple fields are converted as part of their pydantic spec
    #   deferred fields are converted by an extra optional arg to their deferrred_field decorator (if conversion is not default), like in fastAPI
    #   don't do per-type registration - that's just silly and doesn't scale because you might want the same python type to be dumped in different ways in different places
    # TODO read through notes in POC to check this all maeks sense and doesnt miss some corner case

    # TODO update comment
    # An operation consists of 1 or more top-level fields, which means it is 100% deferred fields.
    # NB: We need the special case because of the sequential vs parallel evaluation semantics
    result = {}

    # TODO handle mutation/query variation of sequential/parallel evluation
    for response_field in operation.children.fields_for_type():
        # TODO assuem no lookup errors here - schema has been checked
        schema_field = schema_fields[response_field.name_in_schema]
        # TODO do genuine parallel eva;luation with async tasks
        result[response_field.name_in_response] = await evaluate_deferred_field(
            response_field, schema_field, error_handler
        )

    return result


async def evaluate_deferred_field(
    response_field: ResponseField,
    schema_field: DeferredFieldData,
    error_handler: ErrorHandler,
) -> JSONValue:
    """Evaluate the over-the-wire value for this deferred field, recursively evaluating any child fields.

    Returns:
        Either a primitive value (if the response field is a leaf node), or a
        dictionary that is directly JSON-compatible and uses response_field_name as
        the keys. The iteration order of the dictionary corresponds to the selection
        order of the fields.

    Raises:
        Any errors evaluating this field or it's children, unless they are suppressed
        by `error_handler`
    """
    # TODO call deferred field function and get response value, then handle response value appropriately based on schema_field.result_type
    #   If response is pydantic model, then evaluate_structured_response
    #   if response is flat, then marshal to JSONValue
    result = await schema_field.evaluator()
    return result

    # ---
    # TODO these notes are for evaluate_structured_response...
    # TODO get simple fields (mebbe as a batch?)
    #   - note they may or may not be leaf nodes, so have to recurse potentially
    #   - note they may or may not be JSON-style output value, so schema definer has to ensure this is compatible

    # TODO get deferred fields - looks like the loop code that calls this from evaluate_operation(), except always query-style
