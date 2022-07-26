# gryphter (name TBC)
Yet another graphql server framework

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
