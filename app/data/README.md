\# CapitalOS Data Boundary



External Provider

&#x20;   -> Connector (fetch: provider-specific raw records)

&#x20;   -> Connector (normalize: raw records -> CanonicalFinancialFact)

&#x20;   -> Ingestion Service (validates + persists via existing FinancialFact model)

&#x20;   -> FinancialFact (canonical structured observation)

&#x20;   -> Research / Intelligence (ResearchCase, Claim, Challenger - untouched by this layer)



\## Rules

\- A connector's `normalize()` output is the ONLY thing the rest of the

&#x20; system ever sees. Provider-specific field names, symbols, or ID formats

&#x20; must never leak past a connector.

\- `CanonicalFinancialFact` intentionally has no provider-specific fields.

&#x20; If a future provider has data that doesn't fit this shape, extend the

&#x20; canonical contract deliberately - don't smuggle it through as an extra

&#x20; field on one connector.

\- Entity resolution is NOT part of this layer. Connectors receive/require

&#x20; an already-resolved `entity\_id`. Mapping a provider's own company

&#x20; identifiers to CapitalOS entities is a separate, future capability.

\- No connector in this codebase makes a real network call yet. Adding a

&#x20; real provider means adding one new connector class implementing

&#x20; `FinancialDataConnector` - the ingestion service and everything

&#x20; downstream needs zero changes.

