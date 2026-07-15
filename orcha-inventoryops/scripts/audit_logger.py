import os
import json
from datetime import datetime

class AuditLogger:
    def __init__(self, run_id=None, output_dir=None):
        if not run_id:
            self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        else:
            self.run_id = run_id
            
        if not output_dir:
            # Default directory structure
            self.output_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                "output", "audit_logs"
            )
        else:
            self.output_dir = output_dir
            
        os.makedirs(self.output_dir, exist_ok=True)
        self.log_filepath = os.path.join(self.output_dir, f"run_{self.run_id}.jsonl")

    def log_event(self, sku, node_name, status, input_summary, output_summary, 
                  error="", retry_count=0, human_review_required=False, 
                  approval_status="NOT_STARTED", workflow_state="IN_PROGRESS"):
        """
        Logs a structured event in JSONL format for the workflow execution.
        """
        event = {
            "timestamp": datetime.now().isoformat(),
            "run_id": self.run_id,
            "sku": sku,
            "node_name": node_name,
            "status": status,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "error": error,
            "retry_count": retry_count,
            "human_review_required": human_review_required,
            "approval_status": approval_status,
            "workflow_state": workflow_state
        }
        
        # Append the JSON event to the audit log file
        try:
            with open(self.log_filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            print(f"[AuditLogger Error] Failed to write audit event: {e}")
            
        return event
