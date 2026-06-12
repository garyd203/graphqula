import pytest

from purql import Schema, SchemaFrozenError


def test_register_query_direct_call_should_register_function():
    # Setup
    schema = Schema()

    async def hero():
        return "R2-D2"

    # Exercise
    returned = schema.register_query(hero)

    # Verify
    assert returned is hero
    assert schema._root_queries["hero"] is hero


def test_register_mutation_direct_call_should_register_function():
    # Setup
    schema = Schema()

    async def update_hero():
        return "R2-D2"

    # Exercise
    returned = schema.register_mutation(update_hero)

    # Verify
    assert returned is update_hero
    assert schema._root_mutations["update_hero"] is update_hero


def test_register_query_decorator_should_register_function_when_not_called():
    # Setup
    schema = Schema()

    # Exercise
    @schema.register_query
    async def hero():
        return "R2-D2"

    # Verify
    assert schema._root_queries["hero"] is hero


def test_register_mutation_decorator_should_register_function_when_not_called():
    # Setup
    schema = Schema()

    # Exercise
    @schema.register_mutation
    async def update_hero():
        return "R2-D2"

    # Verify
    assert schema._root_mutations["update_hero"] is update_hero


def test_register_query_decorator_should_register_function_when_called():
    # Setup
    schema = Schema()

    # Exercise
    @schema.register_query()
    async def hero():
        return "R2-D2"

    # Verify
    assert schema._root_queries["hero"] is hero


def test_register_mutation_decorator_should_register_function_when_called():
    # Setup
    schema = Schema()

    # Exercise
    @schema.register_mutation()
    async def update_hero():
        return "R2-D2"

    # Verify
    assert schema._root_mutations["update_hero"] is update_hero


def test_register_query_should_reject_sync_function():
    # Setup
    schema = Schema()

    def not_async():
        return "nope"

    # Exercise / Verify
    with pytest.raises(TypeError, match="must be an async"):
        schema.register_query(not_async)


def test_register_mutation_should_reject_sync_function():
    # Setup
    schema = Schema()

    def not_async():
        return "nope"

    # Exercise / Verify
    with pytest.raises(TypeError, match="must be an async"):
        schema.register_mutation(not_async)


def test_register_query_should_reject_duplicate_field():
    # Setup
    schema = Schema()

    @schema.register_query()
    async def hero():
        return "R2-D2"

    # Exercise / Verify
    with pytest.raises(ValueError, match=r"(?i)duplicate.*hero"):
        schema.register_query(hero)


def test_register_mutation_should_reject_duplicate_field():
    # Setup
    schema = Schema()

    @schema.register_mutation()
    async def update_hero():
        return "R2-D2"

    # Exercise / Verify
    with pytest.raises(ValueError, match=r"(?i)duplicate.*update_hero"):
        schema.register_mutation(update_hero)


def test_schema_should_allow_same_name_across_kinds():
    # Setup / Exercise
    # The same field name in each kind is allowed: kind is part of identity.
    schema = Schema()

    async def hero():
        return "R2-D2"

    schema.register_query(hero)
    schema.register_mutation(hero)

    # Verify
    assert schema._root_queries["hero"] is hero
    assert schema._root_mutations["hero"] is hero


async def test_execute_should_freeze_the_schema():
    # Setup
    schema = Schema()

    @schema.register_query()
    async def hero():
        return "R2-D2"

    # Exercise
    await schema.execute("{ hero }")

    # Verify
    assert schema.is_frozen


async def test_execute_should_require_at_least_one_root_query_field():
    # Setup
    empty_schema = Schema()

    # Exercise & Verify
    with pytest.raises(ValueError, match="at least one query field"):
        await empty_schema.execute("{ hero }")

    # Verify
    assert empty_schema.is_frozen, "Should have been frozen before executing"


def test_include_schema_should_copy_fields():
    # Setup sub schema
    sub_schema = Schema()

    @sub_schema.register_query()
    async def hero():
        return "R2-D2"

    @sub_schema.register_mutation()
    async def update_hero():
        return "R2-D2"

    # Setup main schema
    root_schema = Schema()

    @root_schema.register_query()
    async def ping():
        return "R2-D2"

    # Exercise
    include_result = root_schema.include_schema(sub_schema)

    # Verify
    assert "hero" in root_schema._root_queries
    assert "update_hero" in root_schema._root_mutations
    assert "ping" in root_schema._root_queries

    assert include_result is root_schema, "Should return same schema for call-chaining"
    assert (
        not root_schema.is_frozen
    ), "Root schema should still allow farther registration"


def test_include_schema_should_freeze_the_included_schema():
    # Setup
    sub_schema = Schema()

    @sub_schema.register_query()
    async def hero():
        return "R2-D2"

    async def late_arrival():
        return "R2-D2"

    root_schema = Schema()

    # Exercise
    root_schema.include_schema(sub_schema)

    # Verify
    assert sub_schema.is_frozen


def test_include_schema_should_reject_name_collisions():
    # Setup
    sub_schema = Schema()

    @sub_schema.register_query()
    async def hero():
        return "R2-D2"

    root_schema = Schema()

    @root_schema.register_query()
    async def hero():
        return "C3P0"

    # Exercise / Verify
    with pytest.raises(ValueError, match=r"(?i)duplicate.*hero"):
        root_schema.include_schema(sub_schema)


def test_include_schema_should_allow_sub_schemas_to_be_included_twice():
    # Setup sub schema
    sub_schema = Schema()

    @sub_schema.register_query()
    async def hero():
        return "R2-D2"

    @sub_schema.register_mutation()
    async def update_hero():
        return "R2-D2"

    # Setup main schemas
    root_schema1 = Schema()
    root_schema2 = Schema()

    # Exercise
    root_schema1.include_schema(sub_schema)
    root_schema2.include_schema(sub_schema)

    # Verify
    assert "hero" in root_schema1._root_queries
    assert "hero" in root_schema2._root_queries


def test_include_schema_should_accept_sub_schema_with_only_mutations():
    # Setup sub schema
    sub_schema = Schema()

    @sub_schema.register_mutation()
    async def update_hero():
        return "R2-D2"

    # Setup main schema
    root_schema = Schema()

    # Exercise
    root_schema.include_schema(sub_schema)

    # Verify
    assert "update_hero" in root_schema._root_mutations


def test_new_schema_should_not_be_frozen():
    # Exercise
    schema = Schema()

    # Verify
    assert not schema.is_frozen


def test_freeze_should_be_idempotent():
    # Setup
    schema = Schema()
    schema.freeze()

    # Exercise
    schema.freeze()

    # Verify
    assert schema.is_frozen


def test_freeze_should_preserve_registered_fields():
    # Setup
    schema = Schema()

    @schema.register_query()
    async def hero():
        return "R2-D2"

    @schema.register_mutation()
    async def update_hero():
        return "R2-D2"

    # Exercise
    schema.freeze()

    # Verify
    assert schema._root_mutations["update_hero"] is update_hero
    assert schema._root_queries["hero"] is hero


def test_freeze_empty_schema_is_okay():
    # Setup
    schema = Schema()

    # Exercise & Verify
    schema.freeze()


def test_freeze_should_not_require_any_root_query_fields():
    # Setup
    empty_schema = Schema()

    # Exercise
    empty_schema.freeze()

    # Verify
    assert empty_schema.is_frozen


def test_frozen_schema_should_prevent_farther_schema_changes():
    # Setup
    schema = Schema()

    sub_schema = Schema()

    @sub_schema.register_query()
    async def hero():
        return "R2-D2"

    @sub_schema.register_mutation()
    async def update_hero():
        return "R2-D2"

    async def villain():
        return "Jar Jar Binks"

    async def update_villain():
        return "Jar Jar Binks"

    # Exercise
    schema.freeze()

    with pytest.raises(SchemaFrozenError):
        schema.include_schema(sub_schema)
    with pytest.raises(SchemaFrozenError):
        schema.register_query(villain)
    with pytest.raises(SchemaFrozenError):
        schema.register_mutation(update_villain)

    # Verify
    assert schema._root_mutations == {}
    assert schema._root_queries == {}
