# gryphter

Server-side GraphQL for Pythonistas.

## Purpose

A GraphQL server library written in and for idiomatic Python, prioritising the experience of 
the backend developer, along with observability.


## Design principles

These are load-bearing — they should win arguments about how to implement things.

- **Developer experience first.** If the server-dev DX isn't excellent, there's no reason for this library to exist over strawberry/tartiflette/graphene. Performance and reliability matter but are not the *first* priority.
- **No surprises.** A dev moderately experienced in both GraphQL and Python should be able to do most things without reading much documentation, and never hit surprising behaviour.
- **Low boilerplate.** Lean on Pydantic and FastAPI-style ergonomics.
- **Production-ready by default.** Don't do unhelpful things by default; don't even offer footguns (no bundled GraphiQL, no GET handling).
- **Visitor pattern, not a 2-in-1 hierarchy.** Schema/response models are a standalone class hierarchy. The tree-walking logic that turns them into a JSON response lives separately and must not pollute the models.
- **Async-only resolvers.** Sync resolution is intentionally unsupported (threadpool + context propagation is a mess).
- **Don't reinvent wheels** for non-core concerns (caching, dataloader, DI mechanics) when a good option exists.


## Glossary

- **Simple fields** — Fields in a response object that are known at the time the parent object is instantiated. They may have a straightforward transformation, but are otherwise trivial to determine.
- **Deferred fields** — Fields in a response object that are clacualted using an async method.


## Architecture / structure

Key concepts:

- **Hierarchy semantics** — Propagate state *down* the object graph; propagate errors *up* to parent resolvers for handling.
- **Dependency injection** — FastAPI-style, but NOT coupled to FastAPI's dependency system.


<!-- FILL IN: target package layout once you commit to one, e.g. src/gryphter/... -->


## Tooling

- **Packaging:** Poetry (`pyproject.toml`, `poetry.lock`).
- **Python:** v3.10 or later
- **Runtime dep:** Pydantic v2
- **Formatting:** `black`
- **Style Checks:** `ruff`
- **Tests:** in the `/tests/` directory, run using pytest


## Conventions for Claude

<!-- FILL IN: how you want me to behave in this repo specifically. Examples:
     - terminology to use/avoid (simple vs deferred fields, etc.)
     - whether to write tests alongside changes
     - style preferences beyond black
     - things to never touch -->
