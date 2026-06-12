from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from starlette.status import (
    HTTP_200_OK,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_422_UNPROCESSABLE_ENTITY,
)
from fastapi.testclient import TestClient

from purql import Schema
from purql.bindings.fastapi import GraphQLRouter
from purql.core import ExecutionError, ExecutionResult

# TODO check through this file, not convinced about it
#   patch on module pbject
#   do we _really_ need to patch
#   at least 1 proper integration test

# TODO redo this setup to just use a real schema with real resovlers - no need for patching, but we may want to add some spies

# TODO do we need to try hypothesis or parametrisation ehre to it4erate through variations of valid input params?

# TODO mroe test case:
#   trailing `/` sigh
#   request type
#   response type
#   request accept type
#   actually accept GET
#   0->many nested known exceptions vs. unhandled top-levle exception
#   variations of bad input data



@pytest.fixture()
def schema() -> Schema:
    schema = Schema()

    @schema.register_query()
    async def hero() -> str:
        return "R2-D2"

    @schema.register_mutation()
    async def update_hero() -> str:
        return "R2-D2"

    return schema


@pytest.fixture()
def test_client(schema) -> TestClient:
    app = FastAPI()
    app.include_router(GraphQLRouter(schema))
    yield TestClient(app)


def test_post_request_should_return_result(schema, test_client):
    # Setup
    with patch.object(schema, "execute", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = ExecutionResult(data={"hero": "R2-D2"})

        # Exercise
        response = test_client.post(
            "/graphql",
            json={
                "query": "{ hero }",
                "operationName": "GetHero",
                "variables": {"episode": "EMPIRE"},
            },
        )

    # Verify
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"data": {"hero": "R2-D2"}}

    mock_execute.assert_awaited_once()
    kwargs = mock_execute.await_args.kwargs
    assert kwargs["document"] == "{ hero }"
    assert kwargs["operation_name"] == "GetHero"
    assert kwargs["variables"] == {"episode": "EMPIRE"}


def test_post_request_should_return_internal_graphql_errors(schema, test_client):
    # Setup
    with patch.object(schema, "execute", new_callable=AsyncMock) as mock_execute:
        # TODO this is incorrect - the funciton interface needs to be improved
        mock_execute.return_value = ExecutionResult(
            errors=[ExecutionError(message="boom")]
        )

        # Exercise
        response = test_client.post("/graphql", json={"query": "{ hero }"})

    # Verify
    assert response.status_code == HTTP_200_OK
    assert response.json() == {"errors": [{"message": "boom"}]}


def test_get_is_not_allowed(test_client):
    # Exercise
    status_code = test_client.get("/graphql").status_code

    # Verify
    assert status_code == HTTP_405_METHOD_NOT_ALLOWED


def test_missing_query_is_rejected(test_client):
    # Exercise
    status_code = test_client.post("/graphql", json={}).status_code

    # Verify
    assert status_code == HTTP_422_UNPROCESSABLE_ENTITY
