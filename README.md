# F5 AI Guardrail Proxy – Installation Guide
This repository contains a Python FastAPI–based Guardrail Proxy that acts as an AI policy enforcement gateway between frontend applications and F5 AI Guardrail.

The proxy does not communicate with the LLM directly.
All inference is executed by F5 AI Guardrail, which then connects to the configured LLM provider (e.g., Ollama via /api/chat).

## 1. Architecture Overview
```
Browser (UI)
   ↓
Flask Frontend App (/api/chat)
   ↓
Python Guardrail Gateway (/v1/chat/completions)
   ↓
F5 Calypso AI Guardrail (SaaS)
   ↓
F5 BIG-IP (Enforce System prompt)
   ↓
LLM Runtime (Ollama /api/chat)
```

## 2. System Requirements
- OS: Ubuntu 22.04+ (tested)
- Python: 3.10+
- Network access to:
  - Guardrail Gateway (local)
  - F5 AI Guardrail (outbound HTTPS)
- LLM runtime (e.g., Ollama) reachable by F5 AI Guardrail

## 3. Directory Structure
```
/opt/guardrail-proxy
├── app.py        # FastAPI proxy code
├── venv/
└── README.md
```

## 4. Installation Steps
## 4.1 Create Application Directory
```
sudo mkdir -p /opt/guardrail-proxy
sudo chown -R $USER:$USER /opt/guardrail-proxy
cd /opt/guardrail-proxy
```
## 4.2 Clone the Repository
```
git clone https://github.com/<your-org>/<your-repo>.git .
```
## 4.3 Create Python Virtual Environment
```
python3 -m venv venv
source venv/bin/activate
```
## 4.4 Install Dependencies
```
pip install fastapi uvicorn pydantic
pip install https://docs.calypsoai.com/calypsoai-2.72.4-py3-none-any.whl
```
Please note that the download link of the calypso AI Guardrail can be updated regularly. Please check the official API docs from F5 if the above link doesn't work. 

## 5. Environment Variables
The Guardrail Proxy requires F5 AI Guardrail API Key credentials.
## 5.1 Required Variables
```
export CALYPSOAI_TOKEN="<your-ai-guardrail-api-token>"
export CALYPSOAI_URL="<your-ai-guardrail-url>"
export DEFAULT_PROVIDER="<your-ai-guardrail-provider>"
export CALYPSOAI_PROJECT_ID="<your-guardrail-project-id>"
```

## 6. Run the Proxy Manually (Test)
```
source /opt/guardrail-proxy/venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 18080
```

## 7. Health Check
```
curl http://127.0.0.1:18080/health
```
Expected response:
```
{"status":"ok"}
```

## 8. Test Chat Completion API
```
curl -X POST http://127.0.0.1:18080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "<your-ai-guardrail-provider>",
    "messages": [
      {"role": "user", "content": "Hello. Answer in one sentence."}
    ]
  }'
```

## 9. Run as a Systemd Service (Recommended)
## 9.1 Create Service File
```
sudo nano /etc/systemd/system/f5-ai-guardrail-proxy.service
```
Paste:
```
[Unit]
Description=F5 AI Guardrail Proxy (FastAPI)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/guardrail-proxy
Environment=CALYPSOAI_TOKEN=<your-calypso-api-token>
Environment=DEFAULT_PROVIDER=<your-guardrail-provide>
ExecStart=/opt/guardrail-proxy/venv/bin/uvicorn app:app --host 0.0.0.0 --port 18080
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
## 9.2 Enable and Start Service
```
sudo systemctl daemon-reload
sudo systemctl enable f5-ai-guardrail-proxy
sudo systemctl start f5-ai-guardrail-proxy
```
## 9.3 Verify Service
```
sudo systemctl status f5-ai-guardrail-proxy
```
Logs:
```
journalctl -u f5-ai-guardrail-proxy -f
```

## 10. Security Notes
- This proxy never exposes the LLM directly
- All prompt & response decisions are enforced by F5 AI Guardrail
- Frontend applications cannot bypass AI security policies

## 11. Troubleshooting
### Proxy fails to start
- Check CALYPSOAI_TOKEN
- Verify Python version
- Inspect logs via journalctl

### Requests rejected unexpectedly
- Confirm provider name matches Calypso configuration
- Check policy outcome in Calypso console
