# BusinessFlow CRM — Portfolio Case Study

**Live interface:** https://businessflow-crm.pages.dev/cloud.html  
**Sample dashboard:** https://businessflow-crm.pages.dev/  
**Code:** https://github.com/disCrybee/HTMLProjects/tree/main/businessflow

## Project overview

BusinessFlow is a portfolio CRM prototype for tracking contacts, opportunities and daily follow-up tasks. It combines a responsive browser interface with a Python REST API.

## Problem

Sales information is often fragmented between spreadsheets, notes and separate task lists. BusinessFlow explores a simpler workflow that keeps customer records, deals and tasks in one place.

## Delivered functionality

- Account registration and login with hashed passwords and signed session tokens
- User-scoped contact, sales deal and task operations
- Pipeline value and won-deal metrics calculated from API records
- Deal stage changes and task completion
- Cloud deployment blueprint for Python FastAPI and PostgreSQL
- Responsive interface, mobile navigation and simple pipeline chart
- Standalone sample dashboard using fictional data without authentication
- Automated API tests, cross-user isolation tests, frontend syntax checks

## Technical approach

Frontend: semantic HTML, CSS and vanilla JavaScript.  
Backend: Python, FastAPI, SQLAlchemy.  
Persistence: PostgreSQL on Render for the deployed API, SQLite for development.  
Deployment: Cloudflare Pages for the frontend; Render for API and database.  
Automation: GitHub Actions for tests and continuous frontend deployment.

## What this project demonstrates

API integration, SQL-backed CRUD, browser forms, responsive UI, authentication fundamentals, isolation of user-owned records, GitHub-based deployment and automated checks.

## Limitations and disclosure

BusinessFlow is a **portfolio prototype, not a production SaaS**. It lacks email confirmation, password recovery, robust session management, abuse prevention, formal database migrations and production security review. Do not store sensitive customer data in the demo. The sample dashboard uses fictional data.

## Suggested demo walkthrough

1. Explore the sample dashboard without an account.
2. Open Cloud Workspace and sign into your own test account.
3. Create a fictional customer, add a deal and change its stage to Won.
4. Add a follow-up task and mark it complete.
5. Refresh to demonstrate server-side persistence.

## Suggested Fiverr portfolio description

**BusinessFlow — CRM dashboard and Python API**

Designed and developed a responsive CRM prototype with customer records, sales opportunities, task management, account login and a PostgreSQL-backed API. The interface connects to a FastAPI backend, and automated tests cover core workflows and data access boundaries.

**Services illustrated:** frontend development, dashboard UI, REST API implementation and CRM prototyping.
