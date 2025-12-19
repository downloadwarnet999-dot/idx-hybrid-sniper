# 🚀 IDX Hybrid Sniper - Cloud Deployment Guide

Panduan lengkap deploy aplikasi ke cloud dengan persistent database.

---

## 📋 Prerequisites

- ✅ Akun GitHub (gratis)
- ✅ Akun Supabase (gratis) atau Neon (gratis)
- ✅ Akun Streamlit Community Cloud (gratis)
- ✅ 1-1.5 jam waktu setup

---

## Phase 1: Setup Cloud Database (Supabase PostgreSQL)

### Step 1: Create Supabase Account

1. **Buka** https://supabase.com
2. **Sign up** dengan GitHub account
3. **Create new project**:
   - Project name: `idx-sniper-db` (atau nama lain)
   - Database Password: **SIMPAN PASSWORD INI!** (akan dibutuhkan nanti)
   - Region: **Singapore** (terdekat dari Indonesia)
4. **Tunggu** 2-3 menit sampai database ready

### Step 2: Get Database Connection String

1. **Go to**: Project Settings (gear icon di sidebar)
2. **Click**: Database tab
3. **Scroll to**: Connection String section
4. **Select**: URI mode
5. **Copy** connection string:
   ```
   postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres
   ```
6. **Replace** `[YOUR-PASSWORD]` dengan password yang kamu simpan tadi
7. **Save** connection string ini untuk nanti

### Step 3: Initialize Database Tables (Optional)

Database tables akan otomatis dibuat saat aplikasi pertama kali jalan. Tapi jika mau manual:

1. **Go to**: SQL Editor di Supabase dashboard
2. **Run** query ini:

```sql
-- Market Data Table
CREATE TABLE IF NOT EXISTS market_data (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    open NUMERIC(12, 2),
    high NUMERIC(12, 2),
    low NUMERIC(12, 2),
    close NUMERIC(12, 2),
    volume BIGINT,
    adj_close NUMERIC(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date)
);

CREATE INDEX IF NOT EXISTS idx_ticker_date ON market_data(ticker, date DESC);

-- Trading Journal Table
CREATE TABLE IF NOT EXISTS trading_journal (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    entry_date DATE NOT NULL,
    entry_price NUMERIC(12, 2) NOT NULL,
    lot_size INTEGER NOT NULL,
    sl_price NUMERIC(12, 2) NOT NULL,
    tp1_price NUMERIC(12, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'OPEN',
    exit_date DATE,
    exit_price NUMERIC(12, 2),
    pnl_percent NUMERIC(8, 2),
    pnl_amount NUMERIC(15, 2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_status ON trading_journal(status);
```

---

## Phase 2: Setup GitHub Repository

### Step 1: Initialize Git (if not done yet)

```bash
cd "path/to/idx_sniper"
git init
```

### Step 2: Create GitHub Repository

1. **Go to**: https://github.com/new
2. **Repository name**: `idx-hybrid-sniper` (atau nama lain)
3. **Visibility**:
   - **Public** (jika mau share)
   - **Private** (recommended untuk trading system)
4. **DON'T** initialize with README/gitignore (kita sudah punya)
5. **Click**: Create repository

### Step 3: Push to GitHub

```bash
# Add all files
git add .

# Create first commit
git commit -m "Initial commit - cloud deployment ready"

# Add remote origin (replace with YOUR GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/idx-hybrid-sniper.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 4: Verify Upload

1. **Refresh** GitHub repository page
2. **Check**:
   - ✅ All files uploaded
   - ✅ `.streamlit/secrets.toml` **NOT** uploaded (hidden by .gitignore)
   - ✅ `data/*.db` files **NOT** uploaded

---

## Phase 3: Deploy to Streamlit Community Cloud

### Step 1: Streamlit Cloud Account

1. **Go to**: https://share.streamlit.io
2. **Sign in** with GitHub account
3. **Grant access** to your repositories

### Step 2: Deploy App

1. **Click**: "New app" button
2. **Select**:
   - Repository: `your-username/idx-hybrid-sniper`
   - Branch: `main`
   - Main file path: `app.py`
3. **Click**: Advanced settings

### Step 3: Configure Secrets

**PENTING!** Copy-paste ini ke **Secrets** section:

```toml
[database]
type = "postgresql"
url = "postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"

[telegram]
bot_token = "your_telegram_bot_token_if_any"
chat_id = "your_chat_id_if_any"
```

**Replace**:
- `url` dengan connection string Supabase kamu
- `bot_token` dan `chat_id` jika pake Telegram (opsional)

### Step 4: Deploy!

1. **Click**: "Deploy!" button
2. **Wait**: 5-10 menit untuk build
3. **Watch**: Build logs di layar

### Step 5: Success!

Jika sukses, kamu akan lihat:
```
✅ Your app is live at: https://your-app-name.streamlit.app
```

**Click URL** untuk buka aplikasi online!

---

## Phase 4: First Run Setup

### Step 1: Import Watchlist

1. **Open** deployed app
2. **Go to** sidebar → Watchlist section
3. **Click**: "Import/Export CSV" expander
4. **Upload**: `watchlist_template.csv` atau watchlist kamu
5. **Click**: Import

### Step 2: Update Market Data

1. **Click**: "🔄 Update All Data" button di sidebar
2. **Wait**: Proses download data (bisa 10-30 menit tergantung jumlah ticker)
3. **Progress** akan ditampilkan di layar

### Step 3: Run First Scan

1. **Go to**: Market Screener tab
2. **Click**: "🔍 Scan Market Now"
3. **Wait**: Scan complete
4. **Review**: Signals!

---

## 🎯 Post-Deployment

### Local Development vs Cloud

Aplikasi sekarang **hybrid**:

**Local (Laptop):**
```bash
streamlit run app.py
```
- ✅ Uses SQLite database (fast)
- ✅ Data di `data/` folder
- ✅ Development & testing

**Cloud (Deployed):**
```
https://your-app-name.streamlit.app
```
- ✅ Uses PostgreSQL (persistent)
- ✅ Data di Supabase cloud
- ✅ Access from anywhere!

### Update Deployed App

Setiap kali push ke GitHub, app akan auto-redeploy:

```bash
# Make changes to code
git add .
git commit -m "Update feature X"
git push

# Wait 2-3 minutes, app auto-updates!
```

### Monitor App

**Streamlit Cloud Dashboard:**
- Go to: https://share.streamlit.io/
- **View**:
  - App status
  - Logs
  - Resource usage
  - Analytics

**Supabase Dashboard:**
- Go to: https://supabase.com/dashboard
- **View**:
  - Database tables
  - Query statistics
  - Storage usage

---

## 🔧 Troubleshooting

### "Database connection failed"

**Cause**: Invalid connection string or Supabase down

**Fix**:
1. Verify connection string di Streamlit Secrets
2. Check Supabase project status
3. Try regenerating database password

### "Tables not found"

**Cause**: Tables belum dibuat di PostgreSQL

**Fix**:
1. Restart app (will auto-create tables)
2. Or manually run SQL dari Phase 1 Step 3

### "App won't start"

**Cause**: Missing dependency atau error di code

**Fix**:
1. Check build logs di Streamlit Cloud
2. Verify `requirements.txt` complete
3. Test locally first: `streamlit run app.py`

### "Secrets not found"

**Cause**: Streamlit secrets belum diset

**Fix**:
1. Go to: App settings → Secrets
2. Paste secrets.toml content
3. Save & reboot app

---

## 💡 Tips & Best Practices

### Security

✅ **DO:**
- Use strong Supabase password
- Keep secrets.toml private
- Use private GitHub repo for trading systems
- Enable 2FA on all accounts

❌ **DON'T:**
- Commit secrets.toml to git
- Share database credentials
- Use same password for multiple services

### Performance

**Optimize Watchlist:**
- Keep 100-200 stocks max for fast scans
- Remove inactive stocks regularly

**Database Maintenance:**
- Supabase free tier: 500 MB storage
- Monitor usage di Supabase dashboard
- Delete old market data if needed (keep last 1 year)

### Cost

**Free Tier Limits:**

**Streamlit Cloud:**
- ✅ Unlimited apps (public repos)
- ✅ 1 private app
- ✅ 1 GB RAM
- ✅ Unlimited users

**Supabase:**
- ✅ 500 MB database
- ✅ 2 GB bandwidth/month
- ✅ 50,000 requests/month

**Sufficient for** personal trading use!

---

## 🎓 Advanced: Custom Domain (Optional)

Want `trading.yourdomain.com` instead of `app-name.streamlit.app`?

### Requirements:
- Own a domain
- Streamlit Team/Enterprise plan (paid)

### Alternative (Free):
Use URL shortener:
- https://bit.ly
- https://tinyurl.com
- Create: `bit.ly/my-trading-app` → points to Streamlit URL

---

## 📞 Support

### Issues?

1. **Check logs**: Streamlit Cloud → App → Logs
2. **Database**: Supabase Dashboard → Logs
3. **Local test**: Run locally first to isolate issue

### Resources:

- **Streamlit Docs**: https://docs.streamlit.io/
- **Supabase Docs**: https://supabase.com/docs
- **GitHub Help**: https://docs.github.com/

---

## ✅ Deployment Checklist

**Before Deployment:**
- [ ] Database migrated to support PostgreSQL
- [ ] `.gitignore` includes secrets.toml
- [ ] `requirements.txt` includes psycopg2-binary
- [ ] Tested locally with SQLite

**Supabase Setup:**
- [ ] Account created
- [ ] Project created
- [ ] Database password saved
- [ ] Connection string copied

**GitHub Setup:**
- [ ] Repository created
- [ ] Code pushed
- [ ] Secrets NOT committed

**Streamlit Cloud:**
- [ ] App deployed
- [ ] Secrets configured
- [ ] Build successful
- [ ] App running

**First Run:**
- [ ] Watchlist imported
- [ ] Market data updated
- [ ] Scan working
- [ ] Charts displaying

---

**Selamat! Aplikasi kamu sekarang online dan bisa diakses dari mana saja! 🎉**

**App URL**: https://your-app-name.streamlit.app

---

**Version**: 1.0
**Last Updated**: December 2024
**Author**: IDX Hybrid Sniper Team
