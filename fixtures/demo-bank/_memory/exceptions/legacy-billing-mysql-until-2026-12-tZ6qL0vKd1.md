---
schema: 1
id: tZ6qL0vKd1
memory_type: Exception
title: billing-service may keep MySQL until 2026-12
status: accepted
date: 2026-03-02
summary: Billing-service may stay on MySQL until 2026-12-31 while its migration to Postgres completes.
effective_to: 2026-12-31
review_by: 2026-11-15
applies_to: [service:billing-service]
owners: [team:commerce-architecture]
related: [constrained_by::kQ7vN2xLp4]
---

Billing-service migrates in Q4. Until then it keeps its MySQL instance and may not add new tables.
