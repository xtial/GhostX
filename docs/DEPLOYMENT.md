# GhostX Deployment Guide

This guide provides detailed instructions for deploying GhostX in a production environment.

## Prerequisites

- Linux server (Ubuntu 22.04 LTS recommended)
- Python 3.11 or higher
- PostgreSQL 14 or higher
- Nginx
- SSL certificate
- Domain name

## System Requirements

- CPU: 2+ cores
- RAM: 4GB minimum
- Storage: 20GB minimum
- Bandwidth: Depends on email volume

## Security Checklist

- [ ] Secure server access (SSH keys only)
- [ ] Firewall configured
- [ ] SSL certificates installed
- [ ] Database passwords set
- [ ] Application secrets generated
- [ ] File permissions set
- [ ] Security headers configured
- [ ] Rate limiting enabled
- [ ] Monitoring set up

## Installation Steps

### 1. Server Setup

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv nginx postgresql postgresql-contrib
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev

# Create application user
sudo useradd -m -s /bin/bash ghostx
sudo usermod -aG sudo ghostx
```

### 2. PostgreSQL Setup

```bash
# Create database and user
sudo -u postgres psql

postgres=# CREATE DATABASE ghostx;
postgres=# CREATE USER ghostx WITH PASSWORD 'your_secure_password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE ghostx TO ghostx;
postgres=# \q

# Test connection
psql -h localhost -U ghostx -d ghostx
```

### 3. Application Setup

```bash
# Switch to application user
sudo su - ghostx

# Clone repository
git clone https://github.com/xtial/GhostX.git
cd GhostX

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.template .env
nano .env  # Edit configuration

# Initialize database
python create_db.py --remake
```

### 4. Gunicorn Setup

```bash
# Install Gunicorn
pip install gunicorn

# Create systemd service
sudo nano /etc/systemd/system/ghostx.service
```

```ini
[Unit]
Description=GhostX Gunicorn Service
After=network.target

[Service]
User=ghostx
Group=www-data
WorkingDirectory=/home/ghostx/GhostX
Environment="PATH=/home/ghostx/GhostX/venv/bin"
ExecStart=/home/ghostx/GhostX/venv/bin/gunicorn --workers 4 --bind unix:ghostx.sock -m 007 run:app

[Install]
WantedBy=multi-user.target
```

```bash
# Start and enable service
sudo systemctl start ghostx
sudo systemctl enable ghostx
```

### 5. Nginx Configuration

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/ghostx
```

```nginx
server {
    listen 80;
    server_name localhost;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name localhost;

    ssl_certificate /etc/letsencrypt/live/localhost/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/localhost/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:;" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=ghostx_limit:10m rate=10r/s;
    limit_req zone=ghostx_limit burst=20 nodelay;

    location / {
        proxy_pass http://unix:/home/ghostx/GhostX/ghostx.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/ghostx/GhostX/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /favicon.ico {
        alias /home/ghostx/GhostX/static/favicon_io/favicon.ico;
        expires 30d;
    }

    # Deny access to sensitive files
    location ~ \.(py|pyc|ini|log|cfg|db)$ {
        deny all;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ghostx /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d localhost
```

### 7. Monitoring Setup

```bash
# Install monitoring tools
sudo apt install -y prometheus node-exporter

# Configure Prometheus
sudo nano /etc/prometheus/prometheus.yml
```

Add monitoring configuration for your application.

### 8. Backup Configuration

```bash
# Create backup directory
sudo mkdir -p /var/backups/ghostx

# Create backup script
sudo nano /usr/local/bin/backup-ghostx.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/ghostx"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="ghostx"
DB_USER="ghostx"

# Backup database
pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/db_$DATE.sql

# Backup application files
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /home/ghostx/GhostX

# Keep only last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -delete
```

```bash
# Make script executable
sudo chmod +x /usr/local/bin/backup-ghostx.sh

# Add to crontab
sudo crontab -e
```

Add: `0 2 * * * /usr/local/bin/backup-ghostx.sh`

## Maintenance

### Regular Updates

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Update application
cd /home/ghostx/GhostX
git pull
source venv/bin/activate
pip install -r requirements.txt
python create_db.py
sudo systemctl restart ghostx
```

### Log Rotation

```bash
sudo nano /etc/logrotate.d/ghostx
```

```
/home/ghostx/GhostX/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ghostx www-data
    sharedscripts
    postrotate
        systemctl reload ghostx
    endscript
}
```

## Troubleshooting

### Common Issues

1. **Application Not Starting**
   ```bash
   sudo systemctl status ghostx
   sudo journalctl -u ghostx
   ```

2. **Database Connection Issues**
   ```bash
   sudo -u postgres psql -d ghostx
   \dt  # Check tables
   ```

3. **Nginx Issues**
   ```bash
   sudo nginx -t
   sudo tail -f /var/log/nginx/error.log
   ```

### Performance Tuning

1. **Gunicorn Workers**
   ```python
   workers = multiprocessing.cpu_count() * 2 + 1
   ```

2. **PostgreSQL Configuration**
   ```bash
   sudo nano /etc/postgresql/14/main/postgresql.conf
   ```

   ```ini
   shared_buffers = 256MB
   work_mem = 8MB
   maintenance_work_mem = 64MB
   effective_cache_size = 1GB
   ```

## Scaling

### Horizontal Scaling

1. Set up load balancer
2. Configure multiple application servers
3. Use centralized session storage
4. Implement caching layer

### Vertical Scaling

1. Increase server resources
2. Optimize database queries
3. Implement caching
4. Use CDN for static files

## Security Hardening

1. **Firewall Rules**
   ```bash
   sudo ufw allow ssh
   sudo ufw allow 'Nginx Full'
   sudo ufw enable
   ```

2. **Fail2Ban**
   ```bash
   sudo apt install fail2ban
   sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
   sudo systemctl restart fail2ban
   ```

## Monitoring

1. **Application Logs**
   ```bash
   tail -f /home/ghostx/GhostX/logs/app.log
   ```

2. **System Monitoring**
   ```bash
   htop
   df -h
   free -m
   ```

## Support

For deployment support:
- Discord: xtxry
- Documentation: http://localhost:5000/docs 