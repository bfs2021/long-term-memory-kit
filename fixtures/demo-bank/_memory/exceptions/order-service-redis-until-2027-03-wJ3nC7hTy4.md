---
schema: 1
id: wJ3nC7hTy4
memory_type: Exception
title: order-service may use Redis until 2027-03
status: accepted
date: 2026-05-05
summary: Order-service may run its own Redis cache for cart sessions until 2027-03-31, despite the no-cross-service-DB-reads boundary rules.
effective_to: 2027-03-31
review_by: 2027-02-15
applies_to: [service:order-service]
owners: [team:commerce-architecture]
related: [constrained_by::cA9wE6uJr3]
---

Order-service keeps cart sessions in a private Redis until the session store moves to Postgres. No other service may read it.
