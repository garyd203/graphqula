from pydantic import BaseModel


class Hero(BaseModel):
    """This docstring becomes the documentation in GQL Schema."""

    # TODO need terminology to distinguish between simple fields and function-resolver-bsed fields (even sync vs async)
    #   simple and deferred

    # TODO do we want a compulsory `id` field? Or jsut use hashing (implementers need to make your hashing correct!)

    # A field known at time of instnaitating this object, possibly with straightforward transofrmation fromthe source field
    # TODO calrify whether this *must* be a scalar, or can be anything. no reason it can't be anything
    #: Shebang-based docstring becomes the documentation in GQL Schema
    name: str  # TODO example usage of non-empty; other config

    # TODO need an example of a hidden (non-response) field.
    #   What does pydantic offer us -> https://pydantic-docs.helpmanual.io/usage/models/#private-model-attributes

    # TODO need an example of a simple field that returns a BaseModel, which itself contasin function resolvers

    # TODO do we need a decorator here?
    # TODO do we want dependency injection here (arbitrary dependencies, not the crappy graphql-core ones)
    async def friends(self):
        # A field not known at instantiation time, that has non-trivial implementaiton (eg. dataabse access, compelxx data combination) and/or accepts GQL parameters

        # Note that return type (Python annotation) is non-compulsory, and is not the same as the response type

        # Note that function resovlers are a fundamentally different and independent way of getting a field, compared to apydantic object.

        # Note that this is a normal pydanitc model, so `self` genuinely is an instance of this class. MOreover, it corresponds to *the*
        # response object, not  acopy or source for the repsonse object. (response object is transforemed into JSON to go over the wire, but otheriwsie is this object)

        # Object hierarchy is an inherent part of grapohql object reosluiton, so we don't attempt to decompose field resolvers into standalonae functions separated frm a class
        # Resolvers are reused by having standalone internal funcitons, or by using the same class at different points in the hierarchy

        return []

    # TODO example of using pydantic Config class
    #   eg. specify extra resolver beahviour. Does this belong in a separate Config class? or a subclass under COnfig


# TODO example of an input type - probably a bit different?

# TODO provide base classes with soem common config set?


class Query(BaseModel):
    # NB: Query is a baseModel, but has a specila meaning. hence it needs ot be able t be instantiated with no arguments. In general we'd expect there to only be resolver fucntions, and no pydantic fields
    pass  # FIXME `hero` with diff parametrs.
    # TODO example deprecation


class Mutation(BaseModel):
    # todo demonstrate good-practice pattern (input, not splatting at top-level)
    pass  # FIXME


schema = make_schema(
    query=Query,
)
