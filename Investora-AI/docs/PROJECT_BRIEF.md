# Project Brief

## Product
Investora-AI is an AI-powered investment intelligence product that transforms market data, fundamentals, and news into personalized weekly insights and alerts.

## Business Context
Investors and advisors lose time combining fragmented data across tools and often make decisions on incomplete context. Existing dashboards show data but do not reliably prioritize what matters for a specific user profile.

## Problem Statement
How might we reduce weekly investment analysis time while increasing confidence in the relevance and quality of recommendations?

## Target Users
- Retail and semi-professional investors
- Independent advisors and analyst teams
- AI-first fintech product teams evaluating decision-support workflows

## Stakeholders
- End users: investors/advisors
- Product owner: AI PM (scope, outcomes, prioritization)
- Engineering: frontend + backend contributors
- Operations: deployment/monitoring owners

## Objectives
- Deliver personalized, explainable signals from unified analysis runs.
- Provide reliable UX through streaming progress and clear failure handling.
- Maintain speed of iteration with tests and observability controls.

## Success Metrics
- Time-to-insight: reduction in time to produce weekly shortlist.
- Engagement: repeat dashboard usage and analysis-run completion rate.
- Quality proxy: percentage of signals users keep/watchlist.
- Reliability: API success rate, run completion rate, test pass rate.

## Scope (Current)
- LangGraph pipeline for data collection, scoring, anomalies, evidence synthesis, personalization, delivery, persistence.
- FastAPI endpoints for runs, dashboard data, personalized signals, alerts, market data.
- React dashboard with onboarding, watchlist/discovery views, streaming run state.

## Out of Scope (Current)
- Broker execution/trading automation
- Full compliance/legal workflow automation
- Institutional-scale portfolio optimization
