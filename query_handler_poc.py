# fast API handler
import inspect
from typing import Any

from pydantic import BaseModel


async def handle_graphql_post():
    # Example for a query operation
    query_string = get_graphql_operation_content_from_http_request()

    # Get an object hierarchy modelling the actual queried fields and the input variables for each field
    # mayeb use graphql-core implementation if it is decent
    # this embeds the final vars in the hierarchy. that would be most useful, let's assume so...
    query_sturcture = await get_queried_field_hierarchy(query_string)

    # construct a response dictionary based on walking the query structure recursively
    root_model = schema_from_some_fastapi_dependency.Query()
    response: dict = await get_schema_fields(
        query_sturcture, root_model
    )

    return response


async def get_schema_fields(query, model: BaseModel) -> dict[str, Any]:

    # Important design criteria here: this is the visitor pattern, so  the tree walking logic is entirely contained in this code, and is not visible to the schema models (don't pollute models) or the query sturcture

    # NB: here we have query and schema, but not response object. so get a response

    # NB: in future Want to cahce identical response objects and re-export them. not sure this really makes sense though

    result = {}
    async_fields = {}

    # TODO want to wrap this loop up in a pooled await to minimise wlal-clock time
    # TODO sensible exception handling and None-insertion

    for field in query:
        # TODO do we wanna use the pydantic export stuff? Not sure it makes sense, makes it a bit more inconsistent with the experience for function resolvers
        model_field = getattr(model, field.name)
        if inspect.isawaitable(model_field):
            # a bit of a fudge to look for awaitables, a field might do this. but it prob works out in the wash
            #   mebbe look for coro instead, makes more sense
            # Also implies that we don't support non-async. thta's a mess anyway (using a threadpool safely; propagating context into another thread)

            # TODO this needs to be wrapped in a task
            async_fields[field.name] = get_value_for_resolver_function(
                field, model_field
            )
        else:
            # TODO I think we need to deal with the difference between how the field is represented on the model (perhaps native type like datetime), and how it gets exported. pydanitc may have the answers here, but woudl need to do the export thing.
            #   -> i think it makes sense to do a bulk export of pydantic fields here
            result[field.name] = model_field

    # TODO try anyio
    if async_fields:
        # TODO do we wait for all to complete, or wait for firat failure
        #   first failure makes sense, but that has implications for error reporting
        #   we would also need to cancel all the remaining tasks.
        await batch_await(async_fields.values())

        for fieldname, task in async_fields.items():
            # TODO check for NOne where not allowed, and cascade up
            # TODO do we handle exceptions here? I think not, get_value_for_resolver_function does that. an exception here means that tihs entire object gets invalidated
            #   if multiple exceptions, which one gets cascaded?
            #       mebbe choose one arbitrarily and log the rest?
            #       what if other exceptions *would* occur except execution got short-circuited?
            #       -> does it really matter?? What are we expecting the client to do if there are multiple reasons why an object couldnt be resolved? Mebbe more info is nice, coudl do in future but meh
            result[fieldname] = await task  # raises exception, or returns valid value

    # TODO iterate through fields and recurse if any of them are non-scalras
    #   not sure we want ot recurse here though
    #       how does that work with cascading exceptions?
    #       how about improving our ability to multi-task by not blocking at this levle
    #       we must recurse here if we allow non-function fiuelds to return a model instance
    #           although we could recurse here as a fallback tier... but that's just anonying duplication and complexity
    # TODO the whole structure is a bit flawed because we are buklding up the result dictionary, but adding thigns to it that are not the correct type.
    for field in query:
        # recurse if:
        #   result is a model instance
        #   query suggests we need child fields
        #   NB: either piece of logic appears ot be adequate on its own
        if item_should_be_recursed(field):
            result[field.name] = await get_schema_fields(field, result[field.name])

    return result


async def get_value_for_resolver_function(field, coro):
    # Get a valid value for this field, or raise an exception

    # TODO this func name is too long

    # TODO i would expect to see recursion somewhere here
    #   i think the problem is that we start with a bASEmodel class, but after the first level we get basemodel instances
    FIXME

    params: dict[str, Any] = field.params
    # Looks in some hidden global thingummy, doesn;t try to mash in a dependency thatr conflicts with a param. prob better off using typed values for func params like fastapi
    dependencies: dict[str, Any] = find_dependencies_for_resolver(
        coro, excluded=params.keys()
    )

    params.update(dependencies)

    try:
        model_field = await coro(**params)
    except BaseException as ex:
        # Have to deal with BaseException, mutter mutter
        # TODO hook into customised exception handlers, possibly customised on the current model (or a parent model in the hierarchy)
        # TODO if not handled by custom logic and we can convert thsi field into a None, do so
        # TODO else re-raise
        raise

    # TODO resolver funcitons don't ge tpydantics strict value checking, so we need tocheck for NOne where not allowed, and cascade up (raise an exception?)
