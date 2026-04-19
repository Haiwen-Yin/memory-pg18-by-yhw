# PostgreSQL 18 + pgvector + Apache AGE Deployment Guide

**版本**: v0.2.0  
**适用系统**: RHEL 8.x / CentOS Stream 8 / Ubuntu 24.04

---

## 📋 **环境要求**

| Component | Minimum | Recommended |
|--|--|--:|
| CPU | 4 cores | 8+ cores |
| RAM | 8 GB | 16+ GB |
| Disk | 50 GB SSD | 100+ GB NVMe |
| OS | RHEL 8 / Ubuntu 22.04 | Ubuntu 24.04 LTS |

---

## 🐳 **Option A: Docker Deployment (推荐)**

### Step 1: Pull PostgreSQL 18 Image
```bash
docker pull postgres:18-alpine
```

### Step 2: Create Custom Image with Extensions
```Dockerfile
FROM postgres:18-alpine

# Install dependencies for pgvector and AGE
RUN apk add --no-cache git make gcc musl-dev linux-headers cmake ninja

# Clone and build pgvector
RUN git clone https://github.com/pgvector/pgvector.git /tmp/pgvector \
    && cd /tmp/pgvector \
    && make PG_CONFIG=/usr/local/bin/pg_config \
    && make install PG_CONFIG=/usr/local/bin/pg_config

# Clone and build Apache AGE
RUN git clone https://github.com/apache/age.git /tmp/age \
    && cd /tmp/age \
    && git checkout tags/v1.7.0 \
    && make PG_CONFIG=/usr/local/bin/pg_config \
    && make install PG_CONFIG=/usr/local/bin/pg_config

# Clean up
RUN rm -rf /tmp/pgvector /tmp/age
```

### Step 3: Build and Run Container
```bash
docker build -t memory-pg18 .

docker run -d --name pg-memory \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -v pg-data:/var/lib/postgresql/data \
  --memory=4g --memory-swap=4g \
  memory-pg18

# Verify installation
docker exec -it pg-memory psql -U postgres << 'EOSQL'
CREATE EXTENSION vector;
CREATE EXTENSION age;
CREATE DATABASE memory_graph;
EOSQL
```

---

## 💻 **Option B: Native Installation (Linux)**

### Step 1: Install PostgreSQL 18

#### RHEL/CentOS Stream 8
```bash
# Enable PGDG repository
sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-8-x86_64/pgdg-redhat-repo-latest.noarch.rpm

# Install PostgreSQL 18
sudo dnf install -y postgresql18-server postgresql18-contrib

# Initialize cluster
sudo /usr/pgsql-18/bin/postgresql-18-setup initdb
sudo systemctl enable --now postgresql-18
```

#### Ubuntu 24.04+
```bash
# Add PGDG repository
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

# Install PostgreSQL 18
sudo apt-get update
sudo apt-get install -y postgresql-18 postgresql-contrib-18
```

### Step 2: Install pgvector

```bash
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector

# Build and install
make PG_CONFIG=/usr/bin/pg_config
sudo make install PG_CONFIG=/usr/bin/pg_config

# Verify installation
psql -U postgres -c "CREATE EXTENSION vector;"
```

### Step 3: Install Apache AGE

#### Option A: From Source (Recommended)
```bash
cd /tmp
git clone https://github.com/apache/age.git
cd age
git checkout tags/v1.7.0

# Build and install
make PG_CONFIG=/usr/bin/pg_config
sudo make install PG_CONFIG=/usr/bin/pg_config
```

#### Option B: From RPM (CentOS/RHEL)
```bash
wget https://apache.jfrog.io/artifactory/age/rpm/latest/el8/x86_64/apache-age-1.7.0.rpm
sudo rpm -ivh --force apache-age-1.7.0.rpm
```

### Step 4: Configure PostgreSQL

Edit `/etc/postgresql/18/main/postgresql.conf`:
```ini
shared_preload_libraries = 'age, vector'
listen_addresses = '*'
max_connections = 200
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql-18
```

---

## 🔐 **Security Hardening**

### Step 1: Configure pg_hba.conf
Allow local connections only:
```
host    all             all             127.0.0.1/32            scram-sha-256
local   all             all                                     scram-sha-256
```

### Step 2: Set Strong Password
```bash
psql -U postgres << 'EOSQL'
ALTER USER postgres WITH PASSWORD 'your_strong_password_here';
EOSQL
```

---

## 📊 **Monitoring & Maintenance**

### Check Extension Versions
```bash
psql -U postgres << 'EOSQL'
SELECT extname, extversion, n.nspname as schema_name
FROM pg_extension e
JOIN pg_namespace n ON e.extnamespace = n.oid
WHERE e.extname IN ('vector', 'age')
ORDER BY e.extname;
EOSQL
```

### Backup Strategy
```bash
# Daily backup
pg_dump -d memory_graph -f /backup/memory_graph_$(date +%Y%m%d).sql
```

---

## 🚨 **Troubleshooting**

### Issue: "extension 'vector' is not available"
**Solution**: Verify pgvector installation with `psql -U postgres -c "\\dx vector"`

### Issue: "could not load library 'age.so'"
**Solution**: Check that age.so exists in extension directory

---

**版本**: v0.2.0  
**最后更新**: 2026-04-19 CST
