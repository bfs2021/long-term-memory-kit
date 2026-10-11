---
schema: 1
id: aB3cD4eF5g
memory_type: Decision
title: Shared queue for events
status: accepted
date: 2026-03-02
summary: Services publish domain events to the shared message queue.
last_confirmed: 2026-09-01
applies_to: [domain:commerce, domain:billing, domain:fulfillment, service:order-service, service:billing-service, system:messaging]
owners: [team:platform-engineering]
tags: [messaging]
---

## Context
Point-to-point calls coupled services.

## Decision
Publish events to the shared queue.

## Consequences
*   Consumers subscribe independently.
*   Producers stop knowing their consumers.
