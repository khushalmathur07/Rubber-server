from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime
import uuid

app = FastAPI(title="File Upload Server")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Max file size: 100MB
MAX_FILE_SIZE = 100 * 1024 * 1024


# ✅ Root route
@app.get("/")
async def home():
    return {"message": "File Upload Server is running 🚀"}


# 📤 Upload file
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 100MB)")

    ext = Path(file.filename).suffix
    unique_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    save_path = UPLOAD_DIR / unique_name

    with open(save_path, "wb") as f:
        f.write(contents)

    return JSONResponse({
        "status": "success",
        "original_name": file.filename,
        "saved_as": unique_name,
        "size_bytes": len(contents),
        "content_type": file.content_type,
    })


# 📂 List files
@app.get("/files")
async def list_files():
    files = []
    for f in sorted(UPLOAD_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        stat = f.stat()
        files.append({
            "name": f.name,
            "size_bytes": stat.st_size,
            "uploaded_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return {"files": files, "total": len(files)}


# 📥 Download file
@app.get("/download/{filename}")
async def download_file(filename: str):
    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, filename=filename)


# 🗑 Delete file
@app.delete("/files/{filename}")
async def delete_file(filename: str):
    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    path.unlink()
    return {"status": "deleted", "filename": filename}


# ❤️ Health check
@app.get("/health")
async def health():
    return {"status": "ok"}
