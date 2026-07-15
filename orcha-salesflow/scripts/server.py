import os
import csv
import json
import glob
import sys
import subprocess
import threading
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

PORT = 8000

# Global tracking variables for the background pipeline runner
pipeline_process = None
pipeline_lock = threading.Lock()

def is_pipeline_running():
    global pipeline_process
    if pipeline_process is None:
        return False
    # Check if process is still active
    poll = pipeline_process.poll()
    if poll is None:
        return True
    return False

class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress console logging to keep stdout clean
        return

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        
        # 1. API Routing
        if path == "/api/crm":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            crm_file = os.path.join(base_dir, "business_data/crm/sales_pipeline.csv")
            data = []
            if os.path.exists(crm_file):
                with open(crm_file, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        data.append(row)
            self.wfile.write(json.dumps(data).encode("utf-8"))
            return
            
        elif path == "/api/leads":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            inbox_dir = os.path.join(base_dir, "business_data/inbox")
            leads = []
            if os.path.exists(inbox_dir):
                files = sorted(glob.glob(os.path.join(inbox_dir, "*.txt")))
                for f in files:
                    base = os.path.basename(f)
                    # Extract lead_id
                    match_id = re.search(r"lead_email_(\d+)", base)
                    if match_id:
                        lead_id = f"LEAD-{match_id.group(1)}"
                    else:
                        lead_id = f"LEAD-{base.replace('.txt', '').upper()}"
                        
                    company = "Unknown"
                    with open(f, "r", encoding="utf-8") as file:
                        content = file.read()
                        for line in content.splitlines():
                            if "company name" in line.lower() or "company:" in line.lower():
                                company = line.split(":")[-1].strip().strip("-").strip()
                                break
                    leads.append({
                        "lead_id": lead_id,
                        "file_name": base,
                        "company_name": company
                    })
            self.wfile.write(json.dumps(leads).encode("utf-8"))
            return
            
        elif path == "/api/logs":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            logs_dir = os.path.join(base_dir, "output/audit_logs")
            log_entries = []
            if os.path.exists(logs_dir):
                log_files = sorted(glob.glob(os.path.join(logs_dir, "run_*.jsonl")), reverse=True)
                if log_files:
                    latest_log = log_files[0]
                    with open(latest_log, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                log_entries.append(json.loads(line))
            self.wfile.write(json.dumps(log_entries).encode("utf-8"))
            return
            
        elif path == "/api/pipeline-status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            running = is_pipeline_running()
            self.wfile.write(json.dumps({"running": running}).encode("utf-8"))
            return
            
        elif path.startswith("/api/proposal/"):
            lead_id = path.split("/")[-1]
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            
            proposals_dir = os.path.join(base_dir, "output/proposals")
            proposal_file = os.path.join(proposals_dir, f"proposal_{lead_id}.md")
            clarify_file = os.path.join(proposals_dir, f"clarification_request_{lead_id}.md")
            
            content = "No proposal compiled yet."
            if os.path.exists(proposal_file):
                with open(proposal_file, "r", encoding="utf-8") as f:
                    content = f.read()
            elif os.path.exists(clarify_file):
                with open(clarify_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    
            self.wfile.write(content.encode("utf-8"))
            return
            
        elif path.startswith("/api/approval/"):
            lead_id = path.split("/")[-1]
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            
            approvals_dir = os.path.join(base_dir, "output/approvals")
            approval_file = os.path.join(approvals_dir, f"approval_request_{lead_id}.md")
            
            content = "No active approval checkpoint requests found."
            if os.path.exists(approval_file):
                with open(approval_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    
            self.wfile.write(content.encode("utf-8"))
            return

        # 2. Static File Routing (Serves from root folder)
        dashboard_dir = base_dir
        if path == "/" or path == "/index.html":
            file_to_serve = os.path.join(dashboard_dir, "index.html")
            content_type = "text/html"
        else:
            clean_path = path.lstrip("/")
            file_to_serve = os.path.join(dashboard_dir, clean_path)
            if clean_path.endswith(".css"):
                content_type = "text/css"
            elif clean_path.endswith(".js"):
                content_type = "application/javascript"
            elif clean_path.endswith(".svg"):
                content_type = "image/svg+xml"
            else:
                content_type = "text/plain"

        if os.path.exists(file_to_serve) and os.path.isfile(file_to_serve):
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            with open(file_to_serve, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Resource not found")

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        if path == "/api/run-pipeline":
            global pipeline_process
            with pipeline_lock:
                if is_pipeline_running():
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "Workflow pipeline is already running"}).encode("utf-8"))
                    return
                
                # Delete any old decision files to ensure checkpoint triggers
                approvals_dir = os.path.join(base_dir, "output/approvals")
                if os.path.exists(approvals_dir):
                    for f in os.listdir(approvals_dir):
                        if f.startswith("approval_decision_") and f.endswith(".txt"):
                            try:
                                os.remove(os.path.join(approvals_dir, f))
                            except Exception:
                                pass
                
                # Launch run_salesflow.py with --dashboard flag in background
                python_exe = sys.executable
                script_path = os.path.join(base_dir, "scripts/run_salesflow.py")
                
                try:
                    pipeline_process = subprocess.Popen([python_exe, script_path, "--dashboard"],
                                                        cwd=base_dir,
                                                        stdout=subprocess.DEVNULL,
                                                        stderr=subprocess.DEVNULL)
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": f"Failed to start pipeline: {str(e)}"}).encode("utf-8"))
                    return
                
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": "Sales operations workflow pipeline started"}).encode("utf-8"))
                return

        elif path.startswith("/api/approve/"):
            lead_id = path.split("/")[-1]
            decision_file = os.path.join(base_dir, f"output/approvals/approval_decision_{lead_id}.txt")
            
            os.makedirs(os.path.dirname(decision_file), exist_ok=True)
            with open(decision_file, "w", encoding="utf-8") as f:
                f.write("# Decision file\nAPPROVE\n")
                
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "message": f"Lead {lead_id} approved at checkpoint"}).encode("utf-8"))
            return
            
        elif path.startswith("/api/reject/"):
            lead_id = path.split("/")[-1]
            decision_file = os.path.join(base_dir, f"output/approvals/approval_decision_{lead_id}.txt")
            
            os.makedirs(os.path.dirname(decision_file), exist_ok=True)
            with open(decision_file, "w", encoding="utf-8") as f:
                f.write("# Decision file\nREJECT\n")
                
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "message": f"Lead {lead_id} rejected at checkpoint"}).encode("utf-8"))
            return

        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Endpoint not found")

def run(server_class=HTTPServer, handler_class=DashboardHandler):
    server_address = ("", PORT)
    httpd = server_class(server_address, handler_class)
    print(f"[OK] Dashboard Server active at http://localhost:{PORT}")
    print("Press Ctrl+C to terminate...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

if __name__ == "__main__":
    run()
