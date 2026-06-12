"""FastAPI binding.

This module is the only place ``fastapi`` is imported, and nothing inside
``purql`` imports it — keeping FastAPI an optional dependency.
"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from ..core import ExecutionResult, Schema

# TODO flesh out with all the funcitonality in https://graphql.org/learn/serving-over-http/


class GraphQLRequest(BaseModel):
    """A GraphQL-over-HTTP request body."""

    model_config = ConfigDict(populate_by_name=True)

    query: str
    variables: dict[str, Any] | None = None
    operation_name: str | None = Field(default=None, alias="operationName")


class GraphQLRouter(APIRouter):
    """A FastAPI router exposing a single GraphQL POST endpoint.

    No GET handling and no bundled GraphiQL — production-ready by default.

        router = GraphQLRouter(schema)
        app.include_router(router)
    """

    def __init__(
        self,
        schema: Schema,
        *,
        path: str = "/graphql",
        **router_kwargs: Any,
    ) -> None:
        super().__init__(**router_kwargs)
        self.schema = schema
        self.add_api_route(path, self._handle, methods=["POST"])

    async def _handle(self, request: GraphQLRequest) -> dict[str, Any]:
        result = await self.schema.execute(
            document=request.query,
            variables=request.variables,
            operation_name=request.operation_name,
        )
        return _serialise(result)


def _serialise(result: ExecutionResult) -> dict[str, Any]:
    body: dict[str, Any] = {}
    if result.data is not None:
        body["data"] = result.data
    if result.errors:
        body["errors"] = [{"message": error.message} for error in result.errors]
    return body
