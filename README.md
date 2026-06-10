# PurQL

Server-side GraphQL, purely Pythonic.

Pronounced like "purl" or "pearl".


## Motivation

I've used quite[graphene] a[tartiflette] few[strawberry] different Python GraphQL server libraries in my time.
Trivial Star Wars examples are all well and good, but when push comes to shove and I have to monitor a system under load, 
whilst implementing the 23rd inter-related resolver, they all seemed to be ... lacking

This project is a proof-of-concept to materialise some ideas that are bubblign around in my head. The hypothesis is
that it's possible to build a graphql server implementation in a way that is significnatly more intuitive 
for a native Python developer (or, at least, intuitive for me ;-), adn that this will allow the use of features
for rapidly developing and running relibaly production systems.


## Goal
Create a distinctive GraphQL server library, written in and for idiomatic Python,
with an emphasis on the experience of the backend developer and SRE.


## Inspirations & Thanks

* Guido van Rossum, and the core python team - of course.
* Kenneth Reitz, for showing us how to build simple-but-sophisticated tools that developers actually love.
* FastAPI and tiangolo, who opened the door to thinking about low-effort API implementations.
* tartiflette, for showing that you can implement a python server without graphql-core
* strawberry

## Principles


## Motivating Example


## Unstructured notes
written in and for idomaitc python

python native. a developer who is moderately expereienced in both graphql and python should not encunter surprising behaviour,and should be able to do most thigns without reading much doco.

no-surprise

low-boilerplate

focus on (server) developer experience as first priority. if we get tha right, everythign else will follow. If we don't get that right, there's no point doing this - there's plenty of toher frameworks already.
	- not that thigns like performance, reliability are unimportant - just not the first priority

view the queried object graph as a hierarchy when executed. propagate state down the hierarchy, propagate problems back up the hierarchy

logging:
	- set and propagate log context (and other context) into all resolvers
	- propagate context from parent resolver -> npt sure this makes sense

execptions
	- use exceptions
	- be able to understand them
	- be able to see them
	- be able to handle them in parent resolvers. <<--
	- it's just error handling, should be able to cusotmise. mebbe a generic handler type arrangment

caching of nodes already resovled (include cache errors to re-raise)

avoid reinventing wheels if there's a good one already, or it's not really core. eg. caching, data loader.

try to avoid using the common pattern of passing in root, info, context. etc.

try to do somehting very similar to a fastapi handler and/or router

use DI

standalone class hierarchy for defining the response classes and their code (the shcema)
 - code to walk the tree and turn it into a concrete JSON response is separate. it's a visitor pattern, not a monster 2-in-1 hierarhcy

What's in a response class
* fields known at instantiation time, with straioghtforward transofrmations
* fields with deferred execution (eg. takes non-trivial CPU time, or complex lookup from other fields)
* unique name
* server-side config for how to handle errors from child resolvers.

intended for building  general-purpose API's, not BFF or other server-side rendered paradigms

don't do unhelpful things by default.
	prod-ready by default, and make it easy to find out and do anything you might want in devel (what even is in this category?)
	don't even offer things that are stupid (like bundling graphiql, or handling GET)

batteries included
	error reporting, name your technique

dependencies
	- we do want sophisticated dependency injection, fasatapi style
	- do we want ot be coupled to fastapi dependencies (neat for shared REST + GQL implementations, annoyign for everyone else) -> nah

dont make type mappings global. do per-field using shared functions
