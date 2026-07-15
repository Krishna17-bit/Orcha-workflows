import os
import sys
import json
import subprocess
import csv
from http.server import SimpleHTTPRequestHandler, HTTPServer

# Add scripts directory to path to allow importing local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ingest_inventory import ingest_all

class DashboardAPIHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Disable caching for all assets to ensure updates load instantly
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        # Serve static assets
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        if self.path == "/" or self.path == "/index.html":
            self.path = "/index.html"
            return super().do_GET()
        elif self.path == "/index.css":
            self.path = "/index.css"
            return super().do_GET()
        elif self.path == "/index.js":
            self.path = "/index.js"
            return super().do_GET()
            
        # API Routes
        elif self.path == "/api/inventory":
            self.handle_get_inventory(base_dir)
        elif self.path == "/api/ledger":
            self.handle_get_ledger(base_dir)
        elif self.path == "/api/approvals":
            self.handle_get_approvals(base_dir)
        elif self.path == "/api/verify_paths":
            self.handle_get_verify_paths(base_dir)
        else:
            # Fallback for standard files
            return super().do_GET()

    def do_POST(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        if self.path == "/api/approve":
            self.handle_post_approve(base_dir)
        elif self.path == "/api/run":
            self.handle_post_run(base_dir)
        elif self.path == "/api/edit_stock":
            self.handle_post_edit_stock(base_dir)
        elif self.path == "/api/add_sku":
            self.handle_post_add_sku(base_dir)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Endpoint not found")

    def handle_get_inventory(self, base_dir):
        inv_path = os.path.join(base_dir, "business_data", "inventory", "current_stock.csv")
        thresh_path = os.path.join(base_dir, "business_data", "inventory", "reorder_thresholds.csv")
        supp_path = os.path.join(base_dir, "business_data", "suppliers", "supplier_master.csv")
        
        data = ingest_all(inv_path, thresh_path, supp_path)
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(list(data.values())).encode("utf-8"))

    def handle_get_ledger(self, base_dir):
        tracker_path = os.path.join(base_dir, "business_data", "procurement", "open_purchase_orders.csv")
        orders = []
        if os.path.exists(tracker_path):
            with open(tracker_path, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    orders.append(row)
                    
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(orders).encode("utf-8"))

    def handle_get_approvals(self, base_dir):
        approvals_dir = os.path.join(base_dir, "output", "approvals")
        os.makedirs(approvals_dir, exist_ok=True)
        
        requests_list = []
        # Scan output/approvals/ for approval_request_SKU-XXX.md files
        for filename in os.listdir(approvals_dir):
            if filename.startswith("approval_request_") and filename.endswith(".md"):
                sku = filename.replace("approval_request_", "").replace(".md", "")
                req_path = os.path.join(approvals_dir, filename)
                dec_path = os.path.join(approvals_dir, f"approval_decision_{sku}.txt")
                
                # Read request summary from md file
                req_content = ""
                try:
                    with open(req_path, "r", encoding="utf-8") as f:
                        req_content = f.read()
                except Exception:
                    pass
                    
                # Read current decision
                decision = "PENDING"
                if os.path.exists(dec_path):
                    try:
                        with open(dec_path, "r", encoding="utf-8") as f:
                            decision = f.read().strip().upper()
                            # Strip any comment lines
                            lines = [l.strip() for l in decision.split("\n") if l.strip() and not l.strip().startswith("#")]
                            if lines:
                                decision = lines[0]
                    except Exception:
                        pass
                        
                requests_list.append({
                    "sku": sku,
                    "request_text": req_content,
                    "decision": decision
                })
                
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(requests_list).encode("utf-8"))

    def handle_post_approve(self, base_dir):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        req_body = json.loads(post_data.decode("utf-8"))
        
        sku = req_body.get("sku")
        decision = req_body.get("decision", "PENDING").strip().upper()
        
        if not sku:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing SKU parameter")
            return
            
        approvals_dir = os.path.join(base_dir, "output", "approvals")
        dec_path = os.path.join(approvals_dir, f"approval_decision_{sku}.txt")
        
        try:
            with open(dec_path, "w", encoding="utf-8") as f:
                f.write(decision + "\n")
                
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "SUCCESS", "sku": sku, "decision": decision}).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def handle_post_edit_stock(self, base_dir):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        req_body = json.loads(post_data.decode("utf-8"))
        
        sku = req_body.get("sku")
        new_stock = req_body.get("current_stock")
        
        if not sku or new_stock is None:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing SKU or current_stock parameters")
            return
            
        inv_path = os.path.join(base_dir, "business_data", "inventory", "current_stock.csv")
        
        # Read stock csv
        rows = []
        headers = []
        if os.path.exists(inv_path):
            with open(inv_path, mode="r", encoding="utf-8") as f:
                reader = csv.reader(f)
                headers = next(reader)
                for row in reader:
                    rows.append(row)
                    
        sku_col = headers.index("sku")
        stock_col = headers.index("current_stock")
        
        # Find and update SKU stock
        found = False
        for r in rows:
            if r[sku_col] == sku:
                r[stock_col] = str(new_stock)
                found = True
                break
                
        if not found:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"SKU not found in inventory sheet")
            return
            
        # Write back CSV
        try:
            with open(inv_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
                
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "SUCCESS", "sku": sku, "updated_stock": new_stock}).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))

    def handle_post_run(self, base_dir):
        # Executes python scripts/run_inventoryops.py
        script_path = os.path.join(base_dir, "scripts", "run_inventoryops.py")
        
        try:
            res = subprocess.run(
                [sys.executable, script_path], 
                capture_output=True, text=True, check=True, cwd=base_dir
            )
            stdout_data = res.stdout
            stderr_data = res.stderr
            status = "SUCCESS"
        except subprocess.CalledProcessError as e:
            stdout_data = e.stdout
            stderr_data = e.stderr
            status = "FAILURE"
            
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": status,
            "stdout": stdout_data,
            "stderr": stderr_data
        }).encode("utf-8"))

    def handle_get_verify_paths(self, base_dir):
        paths = {
            "current_stock": os.path.join("business_data", "inventory", "current_stock.csv"),
            "reorder_thresholds": os.path.join("business_data", "inventory", "reorder_thresholds.csv"),
            "supplier_master": os.path.join("business_data", "suppliers", "supplier_master.csv"),
            "open_purchase_orders": os.path.join("business_data", "procurement", "open_purchase_orders.csv")
        }
        
        status = {}
        for key, rel_path in paths.items():
            abs_p = os.path.join(base_dir, rel_path)
            status[key] = {
                "path": rel_path,
                "exists": os.path.exists(abs_p),
                "size_bytes": os.path.getsize(abs_p) if os.path.exists(abs_p) else 0
            }
            
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(status).encode("utf-8"))

    def handle_post_add_sku(self, base_dir):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        req_body = json.loads(post_data.decode("utf-8"))
        
        sku = req_body.get("sku", "").strip()
        item_name = req_body.get("item_name", "").strip()
        category = req_body.get("category", "").strip()
        warehouse = req_body.get("warehouse", "").strip()
        current_stock = str(req_body.get("current_stock", "0")).strip()
        reorder_threshold = str(req_body.get("reorder_threshold", "0")).strip()
        target_stock = str(req_body.get("target_stock", "0")).strip()
        preferred_supplier = req_body.get("preferred_supplier", "").strip()
        unit_cost = str(req_body.get("unit_cost", "0.00")).strip()
        
        if not sku or not item_name or not preferred_supplier:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing required parameters (SKU, Item Name, Preferred Supplier)")
            return
            
        inv_path = os.path.join(base_dir, "business_data", "inventory", "current_stock.csv")
        thresh_path = os.path.join(base_dir, "business_data", "inventory", "reorder_thresholds.csv")
        
        try:
            # 1. Append to current_stock.csv with all 12 columns
            # Column mapping: sku,item_name,category,warehouse,current_stock,reorder_threshold,target_stock,unit_cost,preferred_supplier,last_restocked,average_daily_usage,criticality
            if os.path.exists(inv_path):
                with open(inv_path, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        sku, item_name, category, warehouse, current_stock, 
                        reorder_threshold, target_stock, unit_cost, preferred_supplier,
                        "", "1.0", "MEDIUM"
                    ])
            
            # 2. Append to reorder_thresholds.csv with all 5 columns
            # Column mapping: sku,minimum_stock,target_stock,urgent_threshold,approval_required_above_value
            if os.path.exists(thresh_path):
                # Calculate default urgent threshold as 20% of min stock threshold
                try:
                    thresh_val = float(reorder_threshold)
                    urgent_val = max(1.0, thresh_val * 0.2)
                    urgent_threshold = f"{urgent_val:.2f}"
                except ValueError:
                    urgent_threshold = "5.00"
                    
                with open(thresh_path, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([sku, reorder_threshold, target_stock, urgent_threshold, "5000.00"])
                    
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "SUCCESS", "sku": sku}).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))


def start_server(port=8000):
    server_address = ("", port)
    httpd = HTTPServer(server_address, DashboardAPIHandler)
    print(f"[OrchaInventoryOps Server] Serving dynamic dashboard on http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[OrchaInventoryOps Server] Shutting down.")
        sys.exit(0)

if __name__ == "__main__":
    start_server(8000)
