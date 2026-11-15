-- KAPDA BAZAAR — Production PostgreSQL / Supabase Migration (All 27 Core Entities)
CREATE TABLE IF NOT EXISTS organizations (
  id TEXT PRIMARY KEY,
  org_name TEXT NOT NULL,
  org_type TEXT NOT NULL,
  primary_role TEXT NOT NULL CHECK (primary_role IN ('BUYER','SELLER','ADMIN','LOGISTICS','INSPECTOR')),
  gstin TEXT,
  pan TEXT,
  business_address TEXT,
  city TEXT,
  state TEXT,
  pin_code TEXT,
  country TEXT DEFAULT 'India',
  website TEXT,
  verification_status TEXT NOT NULL DEFAULT 'Not Submitted',
  rating REAL DEFAULT 4.5,
  on_time_delivery_pct REAL DEFAULT 92.0,
  quality_pass_pct REAL DEFAULT 95.0,
  avg_response_hours REAL DEFAULT 3.5,
  is_demo INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  full_name TEXT NOT NULL,
  mobile_number TEXT,
  role TEXT NOT NULL CHECK (role IN ('BUYER','SELLER','ADMIN','LOGISTICS','INSPECTOR')),
  organization_id TEXT REFERENCES organizations(id),
  email_verified INTEGER DEFAULT 1,
  account_status TEXT DEFAULT 'ACTIVE',
  reset_token TEXT
);
CREATE TABLE IF NOT EXISTS product_categories (
  id TEXT PRIMARY KEY,
  parent_group TEXT NOT NULL,
  category_name TEXT NOT NULL,
  slug TEXT NOT NULL,
  applicable_specs TEXT
);
CREATE TABLE IF NOT EXISTS products (
  id TEXT PRIMARY KEY,
  product_code TEXT UNIQUE NOT NULL,
  seller_org_id TEXT REFERENCES organizations(id),
  category_id TEXT REFERENCES product_categories(id),
  product_name TEXT NOT NULL,
  parent_group TEXT NOT NULL,
  subcategory TEXT NOT NULL,
  composition TEXT NOT NULL,
  gsm INTEGER,
  width_inches REAL,
  yarn_count TEXT,
  spinning_type TEXT,
  ply TEXT,
  fabric_construction TEXT,
  finish TEXT,
  colour TEXT,
  size_range TEXT,
  garment_type TEXT,
  moq_qty REAL NOT NULL,
  moq_unit TEXT NOT NULL,
  price_per_unit REAL NOT NULL,
  sample_available INTEGER DEFAULT 1,
  manufacturing_location TEXT,
  lead_time_days INTEGER DEFAULT 10,
  moderation_status TEXT DEFAULT 'PUBLISHED',
  is_demo INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS product_images (
  id TEXT PRIMARY KEY,
  product_id TEXT REFERENCES products(id),
  image_url TEXT NOT NULL,
  alt_text TEXT,
  view_angle TEXT NOT NULL,
  is_primary INTEGER DEFAULT 0,
  visual_signature_hash TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS inventory (
  id TEXT PRIMARY KEY,
  product_id TEXT REFERENCES products(id),
  seller_org_id TEXT REFERENCES organizations(id),
  available_stock_qty REAL NOT NULL,
  reserved_stock_qty REAL DEFAULT 0,
  monthly_production_capacity REAL NOT NULL,
  unit TEXT NOT NULL,
  warehouse_location TEXT,
  batch_age_days INTEGER DEFAULT 15
);
