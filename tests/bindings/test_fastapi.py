from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.status import (
    HTTP_200_OK,
    HTTP_405_METHOD_NOT_ALLOWED,
    HTTP_422_UNPROCESSABLE_ENTITY,
)
from fastapi.testclient import TestClient
from pydantic import BaseModel

from purql import make_schema
from purql.bindings.fastapi import GraphQLRouter
from purql.execution import ExecutionError, ExecutionResult


class Query(BaseModel):
    pass


@pytest.fixture()
def test_client() -> TestClient:
    app = FastAPI()
    app.include_router(GraphQLRouter(make_schema(query=Query)))
    yield TestClient(app)


def test_forwards_parsed_request_to_execute(test_client):
    # Setup
    with patch(
        "purql.bindings.fastapi.execute", new_callable=AsyncMock
    ) as mock_execute:
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
    assert kwargs["query"] == "{ hero }"
    assert kwargs["operation_name"] == "GetHero"
    assert kwargs["variables"] == {"episode": "EMPIRE"}


def test_unhandled_errors_should_return_a_graphql_error(test_client):
    # Setup
    with patch(
        # TODO patch on module, not name
        "purql.bindings.fastapi.execute", new_callable=AsyncMock
    ) as mock_execute:
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
