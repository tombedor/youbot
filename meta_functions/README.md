# Meta Functions

Functions which enable the agent to understand it's capabilities better, and to extend them.

I used this with GPT-4.

For dynamically creating functions, I edited MemGPT code such that rather than requiring functions to be specifically listed in the preset YAML, all implemented functions were made available to the agent.

I attempted to have the agent implement it's own task tracker with these functions.

## Outcome

### Good

The agent was able to utilize the `reload_functions`, `introspect_function`, and `list_functions` commands and understand output. The `debugger` function was also helpful in enabling the agent to understand what I was doing - placing debuggers in other functions often resulted in the agent's internal monologue wondering what was going on.

Simple functions also loaded correctly. I was concerned with the agent accidentally overwriting functions it needed.

The first approach I tried was to put each function in it's own `agent_defined_` prefixed file, but this quickly became disorganized, especially where `import` statements were needed.

### Problems

The agent had a difficult time consistently authoring functions that conformed to MemGPT's requirements - that it has a docstring, type hints, and only `int`, `str`, and `bool` return and argument types. 

The iteration on basic requirements made it difficult for the agent to compose functions that worked together well. Often it would author placeholder functions that had names that sounded right, but didn't really do anything.

As the number of functions grew, so did the agent's tendency to get them confused. Functions also consume context window space, so making a large library of functions to any particular agent doesn't see promising.

## Next steps

This experiment points me back to a multi-agent approach. Having narrowly scoped helper agents available to the primary agent seems like the most promising route. 

As I want to push a deployment of MemGPT to a server anyway, I am going to try to have a deployment with multiple agents that can talk to each other.

This is similar to Autogen's approach, though I think Autogen's groupchat management is too primitive to be useful.




### Installation

These functions work when run with my [MemGPT fork](https://github.com/tombedor/MemGPT). The primary change is [this PR](https://github.com/cpacker/MemGPT/pull/734)

Dependencies will need to be installed in the relevant python environment




