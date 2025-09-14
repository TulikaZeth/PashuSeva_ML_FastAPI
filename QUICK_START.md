# 🚀 Quick Reference Guide

## Essential Commands

### Start Development Server
```bash
python start_dev.py
```
**Access**: http://localhost:8001/docs

### Test Database Connection
```bash
python test_db_direct.py
```

### Check Server Status
```bash
curl http://localhost:8001/database/health
```

---

## Key API Endpoints

### Animal-Centric APIs (Replace `{tag_no}` with actual tag number)

| Endpoint | Purpose | Example |
|----------|---------|---------|
| `GET /animal/{tag_no}` | Animal overview | `/animal/105319726733` |
| `GET /animal/{tag_no}/rag?question=...` | RAG analysis | `/animal/105319726733/rag?question=health` |
| `GET /animal/{tag_no}/amu` | AMU tracking | `/animal/105319726733/amu` |
| `GET /animal/{tag_no}/mrl` | MRL compliance | `/animal/105319726733/mrl` |
| `GET /animal/{tag_no}/amr` | AMR risk | `/animal/105319726733/amr` |
| `GET /animal/{tag_no}/comprehensive` | Complete analysis | `/animal/105319726733/comprehensive` |
| `POST /animal/{tag_no}/chat` | Interactive chat | Body: `{"message": "status?"}` |

### Database APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /database/health` | Database status |
| `GET /database/animals` | List all animals |
| `GET /database/animals/{tag_no}` | Get specific animal |
| `POST /database/animals` | Add new animal |

---

## Test Animal Tag Numbers

Use these for testing:
- `105319726733` - Primary test animal
- `150010127947` - Secondary test animal

---

## Environment Setup

### .env File Template
```env
# MongoDB (encode special chars: @ becomes %40)
MONGODB_URL=mongodb+srv://username:password%40123@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0

# API Keys
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
LOG_LEVEL=info
ENVIRONMENT=development
```

---

## Quick Testing

### 1. Health Check
```bash
curl http://localhost:8001/database/health
```

### 2. Animal Overview
```bash
curl http://localhost:8001/animal/105319726733
```

### 3. RAG Question
```bash
curl "http://localhost:8001/animal/105319726733/rag?question=is%20this%20animal%20healthy"
```

### 4. Comprehensive Analysis
```bash
curl http://localhost:8001/animal/105319726733/comprehensive
```

---

## Troubleshooting

### Port Issues
```bash
netstat -ano | findstr :8001
taskkill /F /PID <process_id>
```

### MongoDB Issues
- Check `.env` file has correct `MONGODB_URL`
- Ensure password is URL-encoded (`@` → `%40`)
- Test with: `python test_db_direct.py`

### Missing Dependencies
```bash
pip install -r requirements.txt
```

---

## Development Workflow

1. **Start**: `python start_dev.py`
2. **Test**: Open http://localhost:8001/docs
3. **Debug**: Check `logs/app.log`
4. **Verify**: Test key endpoints

---

## Important Files

- `start_dev.py` - Development server
- `start_production.py` - Production server  
- `.env` - Environment variables
- `backend/main.py` - Main application
- `test_db_direct.py` - Database test utility

---

**Need Help?** Check the full README.md for detailed instructions!