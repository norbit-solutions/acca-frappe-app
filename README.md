# ACCA LMS - Secure Video Learning Management System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Frappe](https://img.shields.io/badge/Frappe-v14%2B-orange.svg)](https://frappeframework.com)
[![Mux](https://img.shields.io/badge/Mux-Integrated-purple.svg)](https://mux.com)

A professional Learning Management System built on Frappe Framework with secure video streaming powered by Mux.

## 🎯 Features

### Core Functionality
- ✅ Public landing page with course catalog
- ✅ Course detail pages with syllabus
- ✅ Enrollment request workflow (admin approval)
- ✅ Video upload interface within LMS (no separate Mux login)
- ✅ Secure video streaming with Mux integration

### Security Features
- ✅ **Signed Playback URLs** - Time-limited, authenticated video access
- ✅ **Dynamic Watermarking** - User ID + timestamp overlay
- ✅ **Usage Limits** - Configurable view limits per video
- ✅ **Single Device Login** - One active session at a time
- ✅ **Download Prevention** - Disabled downloads and screen casting
- ✅ **Preview Lessons** - Allow sample videos without enrollment

### Additional Features
- ✅ Video view analytics and tracking
- ✅ Email notifications for enrollment workflow
- ✅ Mobile-responsive design
- ✅ Admin dashboard for course management

---

## 📋 Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Mux Account Setup](#mux-account-setup)
4. [Configuration](#configuration)
5. [Usage Guide](#usage-guide)
6. [Architecture](#architecture)
7. [Development](#development)
8. [Troubleshooting](#troubleshooting)
9. [License](#license)

---

## 🔧 Requirements

### System Requirements
- **Frappe Framework**: v14 or v15
- **Frappe LMS**: Latest version (must be installed first)
- **Python**: 3.9+
- **Node.js**: 14+
- **MariaDB**: 10.6+
- **Redis**: 6+

### Third-Party Services
- **Mux Account** (free tier available)
- **Email Service** (Gmail for dev, SendGrid/SES for production)

---

## 📦 Installation

### Step 1: Install Frappe LMS

If you haven't already installed Frappe LMS:

```bash
cd ~/frappe-bench
bench get-app lms
bench --site your-site.local install-app lms
```

### Step 2: Install ACCA LMS

Clone this repository:

```bash
cd ~/frappe-bench
bench get-app https://github.com/your-org/acca-frappe-app
```

Install the app on your site:

```bash
bench --site your-site.local install-app acca_lms
```

### Step 3: Install Python Dependencies

```bash
cd ~/frappe-bench/apps/acca_lms
bench --site your-site.local pip install -r requirements.txt
```

### Step 4: Run Migrations

```bash
bench --site your-site.local migrate
```

### Step 5: Add Custom Fields

Execute the custom fields setup:

```bash
bench --site your-site.local console
```

Then in the console:

```python
from acca_lms.custom_fields.course_lesson_fields import execute
execute()
exit()
```

### Step 6: Restart Bench

```bash
bench restart
```

---

## 🎬 Mux Account Setup

### Create Mux Account

1. Go to [https://mux.com](https://mux.com)
2. Click **Sign Up** (Free tier available)
3. Verify your email
4. Complete account setup

### Get API Credentials

#### Step 1: Create Access Token

1. Login to Mux Dashboard
2. Go to **Settings** → **Access Tokens**
3. Click **Generate New Token**
4. Name it: `ACCA LMS API Token`
5. Select permissions:
   - ✅ **Mux Video** - Full Access
   - ✅ **Mux Data** - Read only
6. Click **Generate Token**
7. **IMPORTANT**: Copy both:
   - `Token ID` (starts with your Mux environment ID)
   - `Token Secret` (shown only once - save it securely!)

#### Step 2: Create Signing Key (for Secure Playback)

1. Go to **Settings** → **Signing Keys**
2. Click **Generate New Key**
3. Name it: `ACCA LMS Playback Key`
4. Click **Generate**
5. Copy both:
   - `Signing Key ID`
   - `Private Key` (Base64-encoded RSA key)

**⚠️ Important**: Save these credentials securely. The secret and private key are shown only once!

### Mux Pricing

- **Free Tier**: $20 credit (good for testing)
- **Video Encoding**: ~$0.005/minute
- **Video Delivery**: ~$0.01/GB
- **Expected Cost**: ~$10-30/month for 100 students

---

## ⚙️ Configuration

### Step 1: Configure Mux Settings

1. Login to your Frappe site
2. Go to: **ACCA LMS** → **Mux Settings**
3. Enter your credentials from Mux setup:

**Mux API Credentials:**
- **Mux Token ID**: Paste your Token ID
- **Mux Token Secret**: Paste your Token Secret
- **Mux Signing Key ID**: Paste your Signing Key ID
- **Mux Signing Private Key**: Paste your Private Key (Base64)

**Security Features:**
- ✅ **Enable Dynamic Watermark**: Checked
- **Watermark Text Template**: `{user_mobile}` (default)

**Usage Limits:**
- ✅ **Enable View Limits**: Checked
- **Max Views Per Video**: `2` (default)
- **Minimum Completion Percent**: `80` (default - 80% watched to count as view)

**Single Device Login:**
- ✅ **Enable Single Device Login**: Checked
- **Logout Message**: "You have been logged out because you logged in from another device."

4. Click **Save**

### Step 2: Configure Email

1. Go to: **Email Account** → **New**
2. Configure based on your provider:

**For Gmail (Development):**
```
Email ID: your-email@gmail.com
Password: [App-specific password]
SMTP Server: smtp.gmail.com
Port: 587
Use TLS: Yes
```

**For SendGrid (Production):**
```
Email ID: apikey
Password: [Your SendGrid API Key]
SMTP Server: smtp.sendgrid.net
Port: 587
Use TLS: Yes
```

3. Click **Save**
4. Click **Test Email** to verify

---

## 📖 Usage Guide

### For Administrators

#### 1. Create a Course

1. Go to **LMS** → **Course** → **New**
2. Fill in:
   - Title
   - Short Introduction
   - Description
   - Upload course image
   - Set level (Beginner/Intermediate/Advanced)
3. Check **Published**
4. Save

#### 2. Add Course Chapters

1. Open your course
2. Click **Add Chapter**
3. Enter chapter title and description
4. Save

#### 3. Upload Video Lessons

1. Go to **LMS** → **Course Lesson** → **New**
2. Fill in:
   - Title
   - Select your course and chapter
   - **Content Type**: Video
3. Save the lesson first
4. Click **Actions** → **Upload Video to Mux**
5. Select your video file (MP4, MOV, AVI, WebM)
6. Click **Upload**
7. Wait for processing (check status with **Actions** → **Check Status**)
8. Once status is **Ready**, video is available!

**Optional:**
- Check **Include in Preview** to allow unenrolled users to watch

#### 4. Manage Enrollment Requests

1. Go to **ACCA LMS** → **Enrollment Request**
2. Filter by **Status**: Pending
3. Click on a request
4. Review student details
5. Click **Approve** or **Reject**
6. Student receives email notification

#### 5. View Analytics

1. Go to **ACCA LMS** → **Video View Log**
2. Filter by:
   - Lesson
   - User
   - Date range
   - View status
3. Export to Excel for detailed reports

### For Students

#### 1. Browse Courses

1. Visit your LMS homepage (e.g., `https://your-site.com`)
2. Browse featured courses
3. Click **View All Courses**

#### 2. Request Enrollment

1. Click on a course
2. Click **Request Enrollment**
3. Optionally add notes for admin
4. Click **Submit**
5. Wait for approval email

#### 3. Watch Videos

1. After approval, go to **Dashboard** → **My Courses**
2. Click on your course
3. Click on a lesson
4. Video plays automatically with watermark
5. Progress is tracked automatically

**View Limits:**
- You can watch each video up to the configured limit (default: 2 complete views)
- A view counts as "complete" after watching 80% (configurable)
- Check remaining views in the video player

---

## 🏗️ Architecture

### Technology Stack

**Backend:**
- Frappe Framework (Python)
- Frappe LMS (base functionality)
- MariaDB (database)
- Redis (caching)

**Frontend:**
- Jinja2 templating
- Bootstrap 5 + Custom CSS
- Vanilla JavaScript
- Mux Player (web component)

**Third-Party Services:**
- Mux (video hosting and streaming)
- Email service (configurable)

### Key Components

```
acca_lms/
├── api/                      # Backend APIs
│   ├── mux_integration.py   # Mux operations
│   ├── enrollment.py        # Enrollment workflow
│   ├── analytics.py         # View tracking
│   └── auth.py              # Single device login
│
├── doctype/                  # Database models
│   ├── mux_settings/        # Configuration
│   ├── video_view_log/      # Analytics
│   └── enrollment_request/  # Enrollment workflow
│
├── public/                   # Static assets
│   ├── css/                 # Styles
│   ├── js/                  # JavaScript
│   └── images/              # Assets
│
├── templates/                # HTML templates
│   ├── pages/               # Public pages
│   └── includes/            # Reusable components
│
└── www/                      # Web controllers
    ├── index.py             # Landing page
    ├── courses.py           # Course listing
    └── courses/[course].py  # Course detail
```

### Data Flow

```
User Request
    ↓
Public Web Page (Jinja2)
    ↓
API Endpoint (Python)
    ↓
Mux Integration (mux_python SDK)
    ↓
Generate Signed URL + JWT Token
    ↓
Secure Video Player (JavaScript)
    ↓
Mux CDN (Video Delivery)
    ↓
User watches video
    ↓
Analytics tracking (every 30s)
    ↓
Database (Video View Log)
```

---

## 🛠️ Development

### Local Development Setup

```bash
# Start development server
bench start

# Watch for changes
bench watch

# View logs
bench --site your-site.local console

# Run tests (when available)
bench --site your-site.local run-tests --app acca_lms
```

### Code Structure

- **DocTypes**: Database models with business logic
- **APIs**: Whitelisted functions for frontend calls
- **Templates**: Jinja2 HTML templates
- **Public Assets**: CSS, JS, images served statically

### Adding New Features

1. Create DocType if needed: `bench --site your-site.local new-doctype`
2. Add API endpoints in `api/` directory
3. Create templates in `templates/`
4. Add styles in `public/css/`
5. Add JavaScript in `public/js/`
6. Run migrations: `bench --site your-site.local migrate`

---

## 🐛 Troubleshooting

### Video Upload Fails

**Problem**: "Failed to create upload URL"

**Solution**:
1. Check Mux Settings credentials
2. Verify Mux Token has "Mux Video - Full Access" permission
3. Check error log: `bench --site your-site.local logs`

### Video Not Playing

**Problem**: "Video not available"

**Solution**:
1. Check video processing status in Course Lesson
2. Wait for status to become "Ready"
3. Verify Mux Signing Keys are configured
4. Check browser console for errors

### Enrollment Request Not Sending Email

**Problem**: Admin not receiving notifications

**Solution**:
1. Check Email Account configuration
2. Send test email from Email Account
3. Verify system managers exist
4. Check error log

### Single Device Login Not Working

**Problem**: Can login from multiple devices

**Solution**:
1. Verify "Enable Single Device Login" is checked in Mux Settings
2. Check hooks.py has `on_session_creation` hook
3. Restart bench: `bench restart`

### Usage Limit Not Enforced

**Problem**: Can watch more than limit

**Solution**:
1. Verify "Enable View Limits" is checked
2. Check completion percent requirement (default 80%)
3. Views must reach completion threshold to count

---

## 📝 License

MIT License - see [license.txt](license.txt)

Copyright (c) 2025 NorBit Solutions

---

## 🤝 Support

For issues and questions:
- Create an issue on GitHub
- Email: info@norbitsolutions.com

---

## 🙏 Credits

Built with:
- [Frappe Framework](https://frappeframework.com)
- [Frappe LMS](https://github.com/frappe/lms)
- [Mux Video](https://mux.com)

---

**Made with ❤️ by NorBit Solutions**
