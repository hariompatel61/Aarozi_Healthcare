# Aarozi Healthcare — Cloud Platform SaaS Service

This folder contains the **Hosted Cloud Platform** backend and database schema for managing commercial SaaS operations.

## Architecture

- **Target Deployment**: Vercel / Railway / Render / AWS ECS / Fly.io
- **Target Database**: PostgreSQL 14+ on **Neon / Supabase / AWS RDS / Railway**
- **Zero Clinical Data**: This database contains **NO patient records or clinical tests**. All patient data stays 100% on the customer laboratory's local computer.

## Quick Setup

### 1. Database Schema
Execute the SQL DDL directly in your hosted PostgreSQL instance (e.g. Supabase SQL Editor or Neon Console):
```bash
psql $DATABASE_URL -f database/cloud_schema.sql
```

### 2. Seed Initial Data
Seeds the default Super Admin (`superadmin@aarozi.in`), commercial plans, and v2.4.0 desktop release:
```bash
DATABASE_URL="postgresql://user:pass@ep-host.neon.tech/neondb" python database/seed_cloud.py
```

### 3. Run API Server
```bash
uvicorn main:app --reload --port 8001
```

