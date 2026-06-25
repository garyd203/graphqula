from graphqula.core import Schema


async def test_simple_query_should_return_data():
    """Happy-path test for a minimal query."""
    # Setup
    schema = Schema()

    @schema.register_query()
    async def hero() -> str:
        return "R2-D2"

    query = "query { hero }"

    # Exercise
    result = await schema.execute(query)

    # Verify
    assert result == {"hero": "R2-D2"}
