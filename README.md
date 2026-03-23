# File Upload Server — EC2 Deployment Guide

## Project Structure
```
server/
├── main.py                 # FastAPI app
├── requirements.txt        # Python deps
├── templates/
│   └── index.html          # Upload UI
├── uploads/                # Created automatically at runtime
└── upload-server.service   # systemd unit (for auto-start)
```

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Upload UI |
| POST | `/upload` | Upload a file (multipart/form-data) |
| GET | `/files` | List all uploaded files |
| DELETE | `/files/{filename}` | Delete a file |
| GET | `/health` | Health check |

---

## EC2 Setup (step by step)

### 1. Launch an EC2 instance
- **AMI**: Ubuntu 22.04 LTS (free tier eligible)
- **Instance type**: t2.micro or t3.micro
- **Security Group — open these ports**:
  - Port 22 (SSH) — your IP only
  - Port 8000 (HTTP) — 0.0.0.0/0 (or use port 80 with nginx below)

### 2. SSH into the instance
```bash
ssh -i your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

### 3. Install Python & copy files
```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv

# Copy your server files (run this from your local machine)
scp -i your-key.pem -r ./server ubuntu@<EC2_PUBLIC_IP>:/home/ubuntu/
```

### 4. Set up the virtual environment
```bash
cd /home/ubuntu/server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Test it runs
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
# Visit http://<EC2_PUBLIC_IP>:8000 in your browser
```

### 6. Run as a system service (auto-start on reboot)
```bash
sudo cp upload-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable upload-server
sudo systemctl start upload-server

# Check status
sudo systemctl status upload-server
```

---

## Optional: Put nginx in front (port 80)

```bash
sudo apt install -y nginx

sudo tee /etc/nginx/sites-available/upload-server <<EOF
server {
    listen 80;
    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/upload-server /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx
```

Now the server is accessible at `http://<EC2_PUBLIC_IP>` (port 80).

---

## Uploading files via curl (no UI)
```bash
curl -X POST http://<EC2_PUBLIC_IP>:8000/upload \
  -F "file=@/path/to/your/file.txt"
```
