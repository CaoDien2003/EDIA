"""
Run once to create all n8n workflows via API.
Usage:
  export N8N_API_KEY=<your-key>
  python n8n/setup_workflows.py
"""
import json
import os
import sys
import urllib.request
import urllib.error

N8N_URL = os.getenv("N8N_URL", "http://localhost:5678")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")

if not N8N_API_KEY:
    print("ERROR: Set N8N_API_KEY env var first.")
    sys.exit(1)


def api(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{N8N_URL}/api/v1{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={
            "X-N8N-API-KEY": N8N_API_KEY,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:200]}")
        return {}


def _webhook_node(name: str, path: str, node_id: str) -> dict:
    """Webhook trigger node — responds immediately (onReceived) so no Respond node needed."""
    return {
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.webhook",
        "typeVersion": 2,
        "position": [240, 300],
        "parameters": {
            "httpMethod": "POST",
            "path": path,
            "responseMode": "onReceived",   # instant 200, process in background
            "options": {},
        },
        "webhookId": path,
    }


def _set_node(name: str, node_id: str, assignments: list, position: list) -> dict:
    return {
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.set",
        "typeVersion": 3.4,
        "position": position,
        "parameters": {
            "mode": "manual",
            "assignments": {"assignments": assignments},
        },
    }


def _http_node(name: str, node_id: str, method: str, url: str, position: list) -> dict:
    return {
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2,
        "position": position,
        "parameters": {"method": method, "url": url, "options": {}},
    }


def _if_node(name: str, node_id: str, left: str, right: str, position: list) -> dict:
    return {
        "id": node_id,
        "name": name,
        "type": "n8n-nodes-base.if",
        "typeVersion": 2,
        "position": position,
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict"},
                "conditions": [{
                    "id": "c1",
                    "leftValue": left,
                    "rightValue": right,
                    "operator": {"type": "string", "operation": "equals"},
                }],
                "combinator": "and",
            },
        },
    }


# ── Workflow 1: Document Uploaded → Format → (Slack placeholder) ─
WORKFLOW_DOC_UPLOAD = {
    "name": "WF1: Document Uploaded → Notify",
    "nodes": [
        _webhook_node("Webhook", "document-uploaded", "node-wh1"),
        _set_node("Format Message", "node-fmt1", [
            {
                "id": "msg",
                "name": "slack_message",
                "type": "string",
                "value": (
                    "=📄 New document indexed: *{{ $json.body.data.filename }}*\n"
                    "Chunks: {{ $json.body.data.chunk_count }}"
                ),
            }
        ], [480, 300]),
        # Placeholder: replace with Slack node after adding credentials
        _http_node(
            "Send Slack (configure URL)",
            "node-slack1",
            "POST",
            "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
            [720, 300],
        ),
    ],
    "connections": {
        "Webhook": {"main": [[{"node": "Format Message", "type": "main", "index": 0}]]},
        "Format Message": {"main": [[{"node": "Send Slack (configure URL)", "type": "main", "index": 0}]]},
    },
    "settings": {"executionOrder": "v1"},
}

# ── Workflow 2: Schedule → Fetch Analytics → Log ─────────────────
WORKFLOW_ANALYTICS = {
    "name": "WF2: Daily Analytics Report",
    "nodes": [
        {
            "id": "node-sched",
            "name": "Schedule (Mon-Fri 8AM)",
            "type": "n8n-nodes-base.scheduleTrigger",
            "typeVersion": 1.2,
            "position": [240, 300],
            "parameters": {
                "rule": {
                    "interval": [{"field": "cronExpression", "expression": "0 8 * * 1-5"}]
                }
            },
        },
        _http_node("GET Analytics", "node-fetch", "GET", "http://backend:8000/api/v1/analytics/summary", [480, 300]),
        _set_node("Format Report", "node-fmt2", [
            {
                "id": "report",
                "name": "report",
                "type": "string",
                "value": (
                    "=📊 Daily Report\n"
                    "• Queries (7d): {{ $json.total_queries }}\n"
                    "• Avg response: {{ $json.avg_response_ms }}ms\n"
                    "• Uploads: {{ $json.total_uploads }}\n"
                    "• Total docs: {{ $json.total_documents }}"
                ),
            }
        ], [720, 300]),
    ],
    "connections": {
        "Schedule (Mon-Fri 8AM)": {"main": [[{"node": "GET Analytics", "type": "main", "index": 0}]]},
        "GET Analytics": {"main": [[{"node": "Format Report", "type": "main", "index": 0}]]},
    },
    "settings": {"executionOrder": "v1"},
}

# ── Workflow 3: High Risk → IF → Alert ───────────────────────────
WORKFLOW_HIGH_RISK = {
    "name": "WF3: High Risk Document → Alert",
    "nodes": [
        _webhook_node("Webhook", "high-risk-document", "node-wh3"),
        _if_node("Is High Risk?", "node-if3", "={{ $json.body.data.risk_level }}", "high", [480, 300]),
        _set_node("Format Alert", "node-fmt3", [
            {
                "id": "alert",
                "name": "alert_message",
                "type": "string",
                "value": (
                    "=🚨 HIGH RISK CONTRACT\n"
                    "File: {{ $json.body.data.filename }}\n"
                    "Risks: {{ $json.body.data.risks.join(', ') }}"
                ),
            }
        ], [720, 200]),
        _set_node("Log Low Risk", "node-log3", [
            {"id": "skip", "name": "skipped", "type": "boolean", "value": True}
        ], [720, 400]),
    ],
    "connections": {
        "Webhook": {"main": [[{"node": "Is High Risk?", "type": "main", "index": 0}]]},
        "Is High Risk?": {
            "main": [
                [{"node": "Format Alert", "type": "main", "index": 0}],
                [{"node": "Log Low Risk", "type": "main", "index": 0}],
            ]
        },
    },
    "settings": {"executionOrder": "v1"},
}


def create_and_activate(wf: dict, activate: bool = True) -> str:
    wf.pop("active", None)
    resp = api("POST", "/workflows", wf)
    wf_id = resp.get("id", "")
    name = resp.get("name", wf["name"])

    if not wf_id:
        print(f"  ✗ Failed to create: '{wf['name']}'")
        return ""

    print(f"  ✓ Created: '{name}' → id={wf_id}")

    if activate:
        # get versionId then activate via internal REST API
        version = resp.get("versionId", "")
        import urllib.parse
        token_file = "/tmp/n8n_s.txt"
        token = ""
        try:
            for line in open(token_file):
                if "n8n-auth" in line:
                    token = line.strip().split()[-1]
        except FileNotFoundError:
            pass

        if token and version:
            activate_url = f"{N8N_URL}/rest/workflows/{wf_id}/activate"
            body = json.dumps({"versionId": version}).encode()
            req = urllib.request.Request(
                activate_url, data=body, method="POST",
                headers={"Cookie": f"n8n-auth={token}", "Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(req) as r:
                    data = json.load(r).get("data", {})
                    print(f"    active={data.get('active')} ✓")
            except Exception as e:
                print(f"    activate failed: {e}")

    return wf_id


if __name__ == "__main__":
    print("Setting up n8n workflows...\n")

    ids = {
        "WF1 Document Upload": create_and_activate(WORKFLOW_DOC_UPLOAD),
        "WF2 Daily Analytics": create_and_activate(WORKFLOW_ANALYTICS, activate=False),  # schedule trigger
        "WF3 High Risk Alert": create_and_activate(WORKFLOW_HIGH_RISK),
    }

    print("\n── Summary ─────────────────────────────────────")
    for name, wf_id in ids.items():
        if wf_id:
            print(f"  {name}: http://localhost:5678/workflow/{wf_id}")

    print("\n── Webhook URLs (register in backend) ──────────")
    print("  document.uploaded  → http://localhost:5678/webhook/document-uploaded")
    print("  document.high_risk → http://localhost:5678/webhook/high-risk-document")
    print("\n── Next Steps ───────────────────────────────────")
    print("  1. Open http://localhost:5678 → Login: admin@docai.com / Admin@1234")
    print("  2. WF1: Replace Slack URL with your actual Slack webhook")
    print("  3. Register webhooks in backend:")
    print('     curl -X POST http://localhost:8000/api/v1/webhooks \\')
    print('       -H "X-Admin-Key: your-key" -H "Content-Type: application/json" \\')
    print('       -d \'{"url":"http://localhost:5678/webhook/document-uploaded","events":["document.uploaded"]}\'')
