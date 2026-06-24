# Customer & Product 360 Platform

A self-service analytics platform unifying **Customer 360** (account demographics, segmentation, contract terms, health) with **Product 360** (feature adoption, plan utilization, consumption trends) across 10,000+ business accounts.

🔗 **[Live Demo](https://ajantika-customer-360.streamlit.app/)**

## The problem
Before this platform, pricing, product, and customer success teams each worked from their own data. Usage lived in one tool, MRR in another, segmentation in a spreadsheet. No single place to see a customer's health, utilization, or expansion potential.

## What it does
- **Customer 360 view** — stitches account demographics, segmentation, contract terms, and health scores into one record per account
- **Product 360 view** — exposes feature adoption, plan utilization, and consumption trends down to the SKU and pricing dimension
- **Self-service workflow** — a sales rep can open the app, find an account, and instantly see which products are consuming at 140% of plan limit, then walk into a renewal with the right expansion pitch — no analyst request needed

## Architecture
Owned end-to-end: source ingestion → dbt models → canonical customer/product semantic layer → serving layer keeping every downstream consumer (Streamlit, Tableau, Salesforce) consistent.

🧩 **Framework: Canonical 360 Semantic Layer** — one customer/product source of truth feeding every downstream tool

## Impact
- 💡 Surfaced a **$3M+ MRR recovery opportunity** through behavioral segmentation of 2,000+ over-utilized customers
- 📈 Contributed to **24% YoY MRR increase**
- 🚀 Self-serve adoption across pricing, product, and customer success teams

## Stack
Python · Streamlit · Plotly · dbt · BigQuery · Snowflake

---

Built by [Ajantika Paul](https://ajantika.github.io) · Lead Product Data Analyst @ Cloudflare
