import os
import json
from datetime import datetime

class AuditLogger:
    def __init__(self, run_id=None):
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../output/audit_logs"))
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, f"run_{self.run_id}.jsonl")
        
    def log(self, lead_id, node_name, status, input_summary=None, output_summary=None, error=None, retry_count=0, human_review_required=False):
        timestamp = datetime.utcnow().isoformat() + "Z"
        log_entry = {
            "timestamp": timestamp,
            "run_id": self.run_id,
            "lead_id": lead_id,
            "node_name": node_name,
            "status": status,
            "input_summary": input_summary or {},
            "output_summary": output_summary or {},
            "error": str(error) if error else None,
            "retry_count": retry_count,
            "human_review_required": human_review_required
        }
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
            
        # Format CLI status indicators
        if status == "SUCCESS":
            symbol = "[OK]"
        elif status == "FAILURE":
            symbol = "[ERR]"
        elif status == "RETRY":
            symbol = "[TRY]"
        elif status == "PENDING" or human_review_required:
            symbol = "[WAIT]"
        else:
            symbol = "[*]"
            
        lead_str = f"[{lead_id}]" if lead_id else "[SYSTEM]"
        print(f"{symbol} {node_name:<28} {lead_str:<10} | {status:<8} | Retry: {retry_count}")
        if error:
            print(f"    +- Error: {error}")
        elif output_summary and "details" in output_summary:
            print(f"    +- Details: {output_summary['details']}")

if __name__ == "__main__":
    logger = AuditLogger("test_run")
    logger.log("lead_000", "TEST_NODE", "SUCCESS", {"test": "input"}, {"details": "Self-test passed"})
