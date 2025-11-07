# Quick Start Guide - BankState Backend

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Step 1: Installation (2 minutes)
```powershell
# Navigate to backend directory
cd c:\pythoncod\BankState\backend

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configuration (1 minute)
```powershell
# Copy environment template
Copy-Item .env.example .env

# Edit .env file (optional for development)
# Notepad .env
```

### Step 3: Start the Server (30 seconds)
```powershell
# Run the application
uvicorn main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 4: Test the API (1 minute)

**Open your browser and visit:**
- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

**Test with curl:**
```powershell
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/
```

---

## 📤 Upload Your First Statement

### Using Swagger UI (Easiest)
1. Go to http://localhost:8000/docs
2. Find `POST /v1/upload-statement`
3. Click "Try it out"
4. Upload a PDF or Excel bank statement
5. Select mode: `local`
6. Click "Execute"

### Using curl
```powershell
# Upload a PDF statement
curl -X POST "http://localhost:8000/v1/upload-statement" `
  -F "files=@C:\path\to\statement.pdf" `
  -F "mode=local" `
  -F "output_format=xml"
```

### Using Python
```python
import requests

url = "http://localhost:8000/v1/upload-statement"
files = {"files": open("statement.pdf", "rb")}
data = {"mode": "local", "output_format": "xml"}

response = requests.post(url, files=files, data=data)
print(response.json())
```

---

## 🧪 Run Tests

```powershell
# Run all tests
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# Run specific test
pytest tests/test_basic.py -v
```

---

## 🐳 Docker Quick Start

```powershell
# Build image
docker build -t bankstate-backend .

# Run container
docker run -p 8000:8000 bankstate-backend

# Access at http://localhost:8000
```

---

## 📝 Common Operations

### List Processed Statements
```powershell
curl http://localhost:8000/v1/statements
```

### Retrieve Specific Statement
```powershell
# Replace {file_id} with actual ID from upload response
curl http://localhost:8000/v1/statement/{file_id}?format=xml
```

### Register Webhook
```powershell
curl -X POST "http://localhost:8000/v1/webhook/register" `
  -H "Content-Type: application/json" `
  -d '{
    "url": "https://your-erp.com/webhook",
    "events": ["processing_complete"],
    "secret": "your-secret"
  }'
```

---

## 🔍 Troubleshooting

### Port Already in Use
```powershell
# Use a different port
uvicorn main:app --reload --port 8080
```

### Module Import Errors
```powershell
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Permission Errors (Windows)
```powershell
# Run PowerShell as Administrator
# Or create directories manually:
New-Item -ItemType Directory -Force uploads, processed, temp, logs, models
```

---

## 📚 Next Steps

1. **Read Full Documentation**: See `DEPLOYMENT.md`
2. **Explore API**: Visit http://localhost:8000/docs
3. **Customize Configuration**: Edit `.env` file
4. **Add Your Banks**: Extend `bank_format_detector.py`
5. **Deploy to Production**: Follow production checklist in `DEPLOYMENT.md`

---

## 💡 Pro Tips

**Development:**
- Use `--reload` flag for auto-reload during development
- Check logs in `logs/bankstate.log`
- Monitor health at `/health` endpoint

**Testing:**
- Keep test bank statements in `tests/fixtures/` (create this folder)
- Use different modes: `local`, `docuclipper`
- Test with both PDF and Excel files

**Production:**
- Never use `--reload` in production
- Set `API_DEBUG=False` in `.env`
- Use multiple workers: `--workers 4`
- Set up reverse proxy (Nginx) with SSL

---

## 🆘 Getting Help

**Check Documentation:**
- `DEPLOYMENT.md` - Full deployment guide
- `IMPLEMENTATION_SUMMARY.md` - Technical overview
- `README.md` - Feature documentation

**Common Issues:**
See troubleshooting section in `DEPLOYMENT.md`

**API Reference:**
Interactive docs at http://localhost:8000/docs

---

## ✅ Verification Checklist

After starting the server, verify:
- [ ] Health endpoint responds: http://localhost:8000/health
- [ ] Swagger UI loads: http://localhost:8000/docs
- [ ] Can upload a file via Swagger UI
- [ ] Logs appear in console
- [ ] Tests pass: `pytest`

---

**You're all set! 🎉**

The backend is now running and ready to process bank statements.

For production deployment, see `DEPLOYMENT.md` for detailed instructions.
