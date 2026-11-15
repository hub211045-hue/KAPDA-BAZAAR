"""
Kapda Bazaar Relational Database Persistence Engine (backend/db_engine.py)
Operates SQLite in /tmp for lock-free transactional speed and syncs back to disk.
"""
import json
import os
import shutil
import sqlite3
import uuid

class KapdaBazaarDB:
    def __init__(self, db_path: str):
        self.disk_path = db_path
        self.tmp_path = "/tmp/kapda_bazaar_active.sqlite"
        if os.path.exists(self.disk_path):
            shutil.copy2(self.disk_path, self.tmp_path)
        elif os.path.exists(self.tmp_path):
            os.remove(self.tmp_path)
        self.conn = sqlite3.connect(self.tmp_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema_and_seed()

    def sync_to_disk(self):
        self.conn.commit()
        os.makedirs(os.path.dirname(self.disk_path), exist_ok=True)
        shutil.copy2(self.tmp_path, self.disk_path)

    def _init_schema_and_seed(self):
        cur = self.conn.cursor()
        cur.executescript("""
            DROP TABLE IF EXISTS audit_logs;
            DROP TABLE IF EXISTS inspections;
            DROP TABLE IF EXISTS lots;
            DROP TABLE IF EXISTS batches;
            DROP TABLE IF EXISTS shipments;
            DROP TABLE IF EXISTS orders;
            DROP TABLE IF EXISTS samples;
            DROP TABLE IF EXISTS quotations;
            DROP TABLE IF EXISTS rfqs;
            DROP TABLE IF EXISTS inventory;
            DROP TABLE IF EXISTS product_images;
            DROP TABLE IF EXISTS products;
            DROP TABLE IF EXISTS product_categories;
            DROP TABLE IF EXISTS business_documents;
            DROP TABLE IF EXISTS business_verification;
            DROP TABLE IF EXISTS users;
            DROP TABLE IF EXISTS organizations;

            CREATE TABLE organizations (
                id TEXT PRIMARY KEY, org_name TEXT, org_type TEXT, primary_role TEXT,
                gstin TEXT, pan TEXT, verification_status TEXT, rating REAL,
                on_time_delivery_pct REAL, quality_pass_pct REAL, avg_response_hours REAL
            );
            CREATE TABLE users (
                id TEXT PRIMARY KEY, email TEXT UNIQUE, password_hash TEXT, full_name TEXT,
                role TEXT, organization_id TEXT, email_verified INTEGER, account_status TEXT, reset_token TEXT
            );
            CREATE TABLE business_verification (
                id TEXT PRIMARY KEY, organization_id TEXT, applicant_role TEXT,
                status TEXT, pre_review_score INTEGER, admin_decision_reason TEXT
            );
            CREATE TABLE business_documents (
                id TEXT PRIMARY KEY, organization_id TEXT, doc_category TEXT,
                doc_title TEXT, visibility_scope TEXT
            );
            CREATE TABLE product_categories (
                id TEXT PRIMARY KEY, parent_group TEXT, category_name TEXT, slug TEXT
            );
            CREATE TABLE products (
                id TEXT PRIMARY KEY, product_code TEXT, seller_org_id TEXT, category_id TEXT,
                product_name TEXT, parent_group TEXT, subcategory TEXT, composition TEXT,
                gsm INTEGER, width_inches REAL, yarn_count TEXT, spinning_type TEXT,
                ply TEXT, fabric_construction TEXT, finish TEXT, colour TEXT,
                size_range TEXT, garment_type TEXT, moq_qty REAL, moq_unit TEXT,
                price_per_unit REAL, sample_available INTEGER, manufacturing_location TEXT,
                lead_time_days INTEGER, moderation_status TEXT, is_demo INTEGER
            );
            CREATE TABLE product_images (
                id TEXT PRIMARY KEY, product_id TEXT, image_url TEXT, alt_text TEXT,
                view_angle TEXT, is_primary INTEGER, visual_signature_hash TEXT UNIQUE
            );
            CREATE TABLE inventory (
                id TEXT PRIMARY KEY, product_id TEXT, seller_org_id TEXT,
                available_stock_qty REAL, reserved_stock_qty REAL, monthly_production_capacity REAL,
                unit TEXT, warehouse_location TEXT, batch_age_days INTEGER
            );
            CREATE TABLE rfqs (
                id TEXT PRIMARY KEY, rfq_number TEXT, buyer_org_id TEXT, created_by_user_id TEXT,
                title TEXT, material_category TEXT, composition TEXT, gsm INTEGER,
                finish TEXT, required_qty REAL, unit TEXT, target_price REAL,
                delivery_city TEXT, required_delivery_days INTEGER, status TEXT
            );
            CREATE TABLE quotations (
                id TEXT PRIMARY KEY, quote_number TEXT, rfq_id TEXT, seller_org_id TEXT,
                submitted_by_user_id TEXT, offered_price REAL, moq_qty REAL,
                lead_time_days INTEGER, shipping_cost REAL, payment_terms TEXT,
                quality_specs_note TEXT, sample_available INTEGER, certifications TEXT,
                technical_match_score REAL, revision_number INTEGER, status TEXT
            );
            CREATE TABLE samples (
                id TEXT PRIMARY KEY, sample_number TEXT, product_id TEXT, buyer_org_id TEXT,
                seller_org_id TEXT, status TEXT, linked_order_id TEXT
            );
            CREATE TABLE orders (
                id TEXT PRIMARY KEY, order_number TEXT, buyer_org_id TEXT, seller_org_id TEXT,
                product_id TEXT, product_name TEXT, quantity REAL, unit TEXT,
                total_amount REAL, order_stage TEXT, timeline_json TEXT
            );
            CREATE TABLE shipments (
                id TEXT PRIMARY KEY, shipment_number TEXT, order_id TEXT,
                logistics_org_id TEXT, assignment_status TEXT, tracking_mode TEXT, events_json TEXT
            );
            CREATE TABLE batches (
                id TEXT PRIMARY KEY, batch_code TEXT, order_id TEXT, seller_org_id TEXT, raw_material_origin TEXT
            );
            CREATE TABLE lots (
                id TEXT PRIMARY KEY, lot_code TEXT, batch_id TEXT, shade_grade TEXT
            );
            CREATE TABLE inspections (
                id TEXT PRIMARY KEY, inspection_number TEXT, order_id TEXT,
                batch_id TEXT, lot_id TEXT, inspector_org_id TEXT, status TEXT
            );
            CREATE TABLE audit_logs (
                id TEXT PRIMARY KEY, actor_user_id TEXT, actor_role TEXT,
                action_type TEXT, target_entity_id TEXT, reason TEXT
            );
        """)

        orgs = [
            ("org-buyer-1", "[DEMO] Aria Apparel Exports Pvt Ltd", "Private Limited", "BUYER", "27AABCA1122K1Z5", "AABCA1122K", "Verified", 4.8, 96.0, 98.0, 2.1),
            ("org-seller-1", "[DEMO] Suryoday Spinning & Knit Mills", "Private Limited", "SELLER", "24AAECS5678G1Z2", "AAECS5678G", "Verified", 4.9, 97.4, 98.6, 1.8),
            ("org-seller-2", "[DEMO] Tirupur Organic Knits & Weaves", "Private Limited", "SELLER", "33AABCT9012H1Z8", "AABCT9012H", "Verified", 4.7, 94.5, 96.8, 2.5),
            ("org-seller-3", "[DEMO] Malwa Indigo Denim & Weaves", "LLP", "SELLER", "23AABCM3456J1Z1", "AABCM3456J", "Under Review", 4.4, 89.0, 92.0, 5.0),
            ("org-admin-1", "[DEMO] Kapda Bazaar Governance Directorate", "Platform Admin", "ADMIN", "27AAACK0001A1Z9", "AAACK0001A", "Verified", 5.0, 100.0, 100.0, 1.0),
            ("org-logistics-1", "[DEMO] Bharat TexFreight Logistics Ltd", "Carrier", "LOGISTICS", "24AABCB7788L1Z4", "AABCB7788L", "Verified", 4.8, 94.2, 99.0, 1.8),
            ("org-qa-1", "[DEMO] TexLab Bureau Quality Assurance", "ISO 17025 Lab", "INSPECTOR", "33AABCT4455Q1Z6", "AABCT4455Q", "Verified", 4.9, 98.5, 99.5, 1.5),
        ]
        cur.executemany("INSERT INTO organizations VALUES (?,?,?,?,?,?,?,?,?,?,?)", orgs)

        users = [
            ("user-buyer-1", "buyer@demo.kapdabazaar.in", "hash_Buyer@2026", "Vikramaditya Mehta", "BUYER", "org-buyer-1", 1, "ACTIVE", None),
            ("user-seller-1", "seller@demo.kapdabazaar.in", "hash_Seller@2026", "Rajeshwar Patel", "SELLER", "org-seller-1", 1, "ACTIVE", None),
            ("user-seller-3", "unverified@demo.kapdabazaar.in", "hash_Seller@2026", "Ankit Rathore", "SELLER", "org-seller-3", 1, "ACTIVE", None),
            ("user-admin-1", "admin@demo.kapdabazaar.in", "hash_Admin@2026", "Meera Deshmukh", "ADMIN", "org-admin-1", 1, "ACTIVE", None),
            ("user-logistics-1", "logistics@demo.kapdabazaar.in", "hash_Logistics@2026", "Harpreet Singh Gill", "LOGISTICS", "org-logistics-1", 1, "ACTIVE", None),
            ("user-inspector-1", "inspector@demo.kapdabazaar.in", "hash_Inspector@2026", "Dr. S. Balasubramanian", "INSPECTOR", "org-qa-1", 1, "ACTIVE", None),
        ]
        cur.executemany("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?)", users)
        cur.execute("INSERT INTO business_verification VALUES ('ver-01','org-seller-3','SELLER','Under Review',92,'Pending Admin inspection')")
        cur.execute("INSERT INTO business_documents VALUES ('doc-01','org-seller-1','GST_CERT','Suryoday GSTIN Dossier','ORG_AND_ADMIN')")

        seed_path = os.path.join(os.path.dirname(__file__), "catalogue_149_seed.json")
        seed = json.load(open(seed_path, "r", encoding="utf-8"))
        for c in seed["categories"]:
            cur.execute("INSERT INTO product_categories VALUES (?,?,?,?)", (c["id"], c["parent_group"], c["category_name"], c["slug"]))
        for p in seed["products"]:
            cur.execute(
                "INSERT INTO products VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    p["id"], p["product_code"], p["seller_org_id"], p["category_id"],
                    p["product_name"], p["parent_group"], p["subcategory"], p["composition"],
                    p["gsm"], p["width_inches"], p["yarn_count"], p["spinning_type"],
                    p["ply"], p["fabric_construction"], p["finish"], p["colour"],
                    p["size_range"], p["garment_type"], p["moq_qty"], p["moq_unit"],
                    p["price_per_unit"], 1, p["manufacturing_location"], p["lead_time_days"],
                    "PUBLISHED", 1
                )
            )
            for idx, ang in enumerate(("MACRO_WEAVE", "ROLL_CONE_VIEW", "LAB_SWATCH", "TECHNICAL_INDUSTRIAL"), 1):
                cur.execute(
                    "INSERT INTO product_images VALUES (?,?,?,?,?,?,?)",
                    (
                        f"img-{p['id']}-{idx}", p["id"],
                        f"studio://{p['image_id']}/{ang.lower()}",
                        p["product_name"], ang, 1 if idx == 1 else 0,
                        f"{p['image_sha256']}_{ang}"
                    )
                )
        for inv in seed["inventory"]:
            cur.execute(
                "INSERT INTO inventory VALUES (?,?,?,?,?,?,?,?,?)",
                (inv["id"], inv["product_id"], inv["seller_org_id"], inv["available_stock_qty"], inv["reserved_stock_qty"], inv["monthly_production_capacity"], inv["unit"], inv["warehouse_location"], inv["batch_age_days"])
            )

        cur.execute("INSERT INTO rfqs VALUES ('rfq-01','RFQ-2026-1001','org-buyer-1','user-buyer-1','180 GSM 100% Cotton Dyed Single Jersey','Knitted Fabric','100% Cotton',180,'Dyed',1000.0,'kg',250.0,'Mumbai',14,'OPEN')")
        cur.execute("INSERT INTO quotations VALUES ('quote-01','QT-2026-501','rfq-01','org-seller-1','user-seller-1',238.0,300.0,10,4500.0,'30% Advance', 'Delta-E < 0.6',1,'[ISO 9001]',98.5,1,'SUBMITTED')")
        cur.execute("INSERT INTO quotations VALUES ('quote-02','QT-2026-502','rfq-01','org-seller-2','user-seller-1',246.0,250.0,9,4200.0,'50% Advance', 'GOTS Organic',1,'[GOTS]',96.0,1,'SUBMITTED')")
        cur.execute("INSERT INTO samples VALUES ('samp-01','SMP-2026-301','prod-01','org-buyer-1','org-seller-1','Buyer Approved','ord-01')")
        cur.execute("INSERT INTO orders VALUES ('ord-01','ORD-2026-9001','org-buyer-1','org-seller-1','prod-01','180 GSM Combed Single Jersey',1000.0,'kg',242500.0,'In Transit','[]')")
        cur.execute("INSERT INTO orders VALUES ('ord-02','ORD-2026-9002','org-buyer-1','org-seller-1','prod-03','40s Ne Combed Cotton Yarn',500.0,'kg',115000.0,'Production Pending','[]')")
        cur.execute("INSERT INTO shipments VALUES ('ship-01','SHP-2026-401','ord-01','org-logistics-1','IN_TRANSIT','MANUAL_VERIFIED_LOG','[]')")
        cur.execute("INSERT INTO batches VALUES ('batch-01','BATCH-SRT-2026-088','ord-01','org-seller-1','Shankar-6 Gujarat Cotton')")
        cur.execute("INSERT INTO lots VALUES ('lot-01','LOT-NVY-88A','batch-01','Delta-E 0.52')")
        cur.execute("INSERT INTO inspections VALUES ('insp-01','QAR-2026-701','ord-01','batch-01','lot-01','org-qa-1','APPROVED')")
        self.sync_to_disk()

    def register_user(self, payload: dict) -> dict:
        role = (payload.get("role") or "").upper()
        if role not in ("BUYER", "SELLER"):
            return {"ok": False, "status": 403, "error": "Public registration strictly permits BUYER or SELLER only."}
        org_id = f"org-{uuid.uuid4().hex[:8]}"
        user_id = f"usr-{uuid.uuid4().hex[:8]}"
        cur = self.conn.cursor()
        cur.execute("INSERT INTO organizations VALUES (?,?,?,?,?,?,?,?,?,?,?)", (org_id, payload.get("company_name", "New Org"), "Private Limited", role, payload.get("gstin", "27AABCU9603R1ZM"), payload.get("pan", "AABCU9603R"), "Submitted", 4.5, 92.0, 95.0, 3.5))
        cur.execute("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?)", (user_id, payload["email"], f"hash_{payload['password']}", payload.get("full_name", "User"), role, org_id, 1, "ACTIVE", None))
        cur.execute("INSERT INTO business_verification VALUES (?,?,?,?,?,?)", (f"ver-{uuid.uuid4().hex[:6]}", org_id, role, "Submitted", 100, "Submitted for Admin review"))
        self.sync_to_disk()
        return {"ok": True, "status": 201, "org_id": org_id, "user_id": user_id, "verification_status": "Submitted"}

    def admin_review_verification(self, actor_user_id: str, org_id: str, decision: str, reason: str) -> dict:
        cur = self.conn.cursor()
        u = cur.execute("SELECT role FROM users WHERE id = ?", (actor_user_id,)).fetchone()
        if not u or u["role"] != "ADMIN":
            return {"ok": False, "status": 403, "error": "ADMIN role required."}
        cur.execute("UPDATE organizations SET verification_status = ? WHERE id = ?", (decision, org_id))
        cur.execute("UPDATE business_verification SET status = ?, admin_decision_reason = ? WHERE organization_id = ?", (decision, reason, org_id))
        cur.execute("INSERT INTO audit_logs VALUES (?,?,?,?,?,?)", (f"aud-{uuid.uuid4().hex[:6]}", actor_user_id, "ADMIN", f"VERIFY_{decision.upper()}", org_id, reason))
        self.sync_to_disk()
        return {"ok": True, "status": 200}

    def get_products_for_role(self, role: str, org_id: str, filters: dict) -> list:
        cur = self.conn.cursor()
        rows = cur.execute("SELECT p.*, i.available_stock_qty, i.reserved_stock_qty FROM products p LEFT JOIN inventory i ON p.id = i.product_id WHERE p.moderation_status = 'PUBLISHED'").fetchall()
        results = []
        for r in rows:
            d = dict(r)
            if filters.get("parent_group") and d["parent_group"] != filters["parent_group"]:
                continue
            if filters.get("composition"):
                tokens = filters["composition"].lower().split()
                if not all(t in d["composition"].lower() for t in tokens):
                    continue
            if filters.get("max_price") and d["price_per_unit"] > float(filters["max_price"]):
                continue
            if role == "BUYER":
                d.pop("available_stock_qty", None)
                d.pop("reserved_stock_qty", None)
            results.append(d)
        return results

    def update_order_stage(self, actor_user_id: str, order_id: str, new_stage: str, note: str) -> dict:
        cur = self.conn.cursor()
        u = cur.execute("SELECT role FROM users WHERE id = ?", (actor_user_id,)).fetchone()
        if not u:
            return {"ok": False, "status": 401}
        if u["role"] == "BUYER" and new_stage in ("Production In Progress", "Ready for Dispatch", "Dispatched", "In Transit"):
            return {"ok": False, "status": 403, "error": f"BUYER_FORBIDDEN: Buyers cannot transition orders to '{new_stage}' (production/dispatch/logistics actions are restricted)."}
        cur.execute("UPDATE orders SET order_stage = ? WHERE id = ?", (new_stage, order_id))
        self.sync_to_disk()
        return {"ok": True, "status": 200}

    def update_shipment_lifecycle(self, actor_user_id: str, shipment_id: str, new_status: str, checkpoint: str = "", note: str = "") -> dict:
        cur = self.conn.cursor()
        u = cur.execute("SELECT role, organization_id FROM users WHERE id = ?", (actor_user_id,)).fetchone()
        if not u or u["role"] not in ("LOGISTICS", "ADMIN"):
            return {"ok": False, "status": 403, "error": "LOGISTICS or ADMIN role required."}
        sh = cur.execute("SELECT * FROM shipments WHERE id = ?", (shipment_id,)).fetchone()
        if not sh:
            return {"ok": False, "status": 404, "error": "Shipment not found."}
        if u["role"] == "LOGISTICS" and sh["logistics_org_id"] != u["organization_id"]:
            return {"ok": False, "status": 403, "error": "Logistics provider can only manage assigned shipments."}
        cur.execute("UPDATE shipments SET assignment_status = ? WHERE id = ?", (new_status, shipment_id))
        if new_status == "DELIVERED":
            cur.execute("UPDATE orders SET order_stage = 'Delivered' WHERE id = ?", (sh["order_id"],))
        self.sync_to_disk()
        return {"ok": True, "status": 200}

    def submit_quality_inspection(self, actor_user_id: str, inspection_id: str, status: str, reason: str = "") -> dict:
        cur = self.conn.cursor()
        u = cur.execute("SELECT role, organization_id FROM users WHERE id = ?", (actor_user_id,)).fetchone()
        if not u or u["role"] not in ("INSPECTOR", "ADMIN"):
            return {"ok": False, "status": 403, "error": "INSPECTOR or ADMIN role required."}
        insp = cur.execute("SELECT * FROM inspections WHERE id = ?", (inspection_id,)).fetchone()
        if not insp:
            return {"ok": False, "status": 404, "error": "Inspection not found."}
        if u["role"] == "INSPECTOR" and insp["inspector_org_id"] != u["organization_id"]:
            return {"ok": False, "status": 403, "error": "Quality Inspector can only manage assigned inspections."}
        cur.execute("UPDATE inspections SET status = ? WHERE id = ?", (status, inspection_id))
        cur.execute("INSERT INTO audit_logs VALUES (?,?,?,?,?,?)", (f"aud-{uuid.uuid4().hex[:6]}", actor_user_id, u["role"], f"INSPECTION_{status.upper()}", inspection_id, reason))
        self.sync_to_disk()
        return {"ok": True, "status": 200}

    def get_documents_for_user(self, actor_user_id: str) -> list:
        cur = self.conn.cursor()
        u = cur.execute("SELECT role, organization_id FROM users WHERE id = ?", (actor_user_id,)).fetchone()
        if not u:
            return []
        rows = cur.execute("SELECT * FROM business_documents").fetchall()
        if u["role"] == "ADMIN":
            return [dict(r) for r in rows]
        return [dict(r) for r in rows if r["organization_id"] == u["organization_id"] or r["visibility_scope"] == "PUBLIC"]

