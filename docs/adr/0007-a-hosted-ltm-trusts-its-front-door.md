# A Hosted ltm mcp Trusts Its Front Door

`ltm mcp --http` serves one Bank's read tools to Copilot Studio and declarative agents. It never authenticates callers and never filters Records by who is asking. A front door validates the caller's Entra token, such as Easy Auth on Container Apps or App Service, or APIM. Everyone the front door lets through can read every Record in the Bank, so the agent's audience is the Bank's audience. A team that needs a narrower audience runs a separate Bank and server.

`ltm` has no per-Record access control, and the Bank's git permissions already set who may read it. Filtering by caller would turn `ltm` into an authorization system layered over that boundary. Validating Entra tokens inside `ltm` was the other option, but it adds security code that every front door already handles, and it ties `ltm` to one identity provider.

A server deployed without a front door would hand the Bank to anyone who finds the URL, so `ltm mcp --http` refuses to bind a non-loopback host unless `--trust-proxy-auth` says a front door is in place.
