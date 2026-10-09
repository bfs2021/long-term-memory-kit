# ltm Never Calls a Model

Hydration needs judgment, and `ltm` has to stay deterministic. So the LLM comes from the agent the person is already running. Skills and the hydrator agent do the extract, draft, and reconcile steps, and `ltm` does the mechanical ones (discover, query, validate, propose).

We rejected an `ltm hydrate` command that calls a provider API. It would need API keys and a provider choice, and its output would vary between runs. It would also break the zero-install rule, which says a team with only an agent and plain files can still hydrate by following the skills by hand.
