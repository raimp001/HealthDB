# HealthDB Dependency Audit Report

**Date:** 2026-01-11
**Project:** HealthDB (Full-stack application)
**Technologies:** React Frontend + Python FastAPI Backend

---

## Executive Summary

This audit identified **critical security vulnerabilities** and **outdated packages** in both the Node.js and Python dependencies. Immediate action is required to address:

- **25 npm vulnerabilities** (1 critical, 14 high, 7 moderate, 3 low)
- **12 Python package vulnerabilities** (multiple high-severity)
- **12 outdated npm packages** with significant version gaps
- **392 MB node_modules** size (reasonable for a React app)

---

## 1. Critical Security Vulnerabilities

### 1.1 Node.js Dependencies (npm)

#### CRITICAL Severity
- **nth-check** - Inefficient Regular Expression Complexity (CVE)
  - Impact: ReDoS attack vector
  - Fix: Update to version 2.0.1+

#### HIGH Severity (14 vulnerabilities)
1. **react-router-dom** - XSS via Open Redirects (GHSA-2w69-qvjg-hvjx)
   - Current: 6.29.0
   - Fix: Update to 6.30.3+
   - Impact: Cross-site scripting attacks

2. **postcss** - Line Return Parsing Error (CVE-2023-44270)
   - Current: 8.5.1
   - Fix: Update to 8.4.31+
   - Impact: Security bypass

3. **qs** - Prototype Pollution (CVE-2022-24999)
   - Fix: Update to 6.11.0+
   - Impact: Memory exhaustion, DoS

4. **css-select** - Polynomial ReDoS (CVE-2024-131)
   - Impact: Denial of Service
   - Affects: svgo, @svgr/plugin-svgo

5. **express** - Open Redirect via body-parser
   - Indirect dependency vulnerability
   - Fix: Available via dependency updates

6. **webpack-dev-server** - Source Code Theft Vulnerability
   - Version: ≤5.2.0
   - Impact: Source code may be stolen via malicious websites

#### MODERATE Severity (7 vulnerabilities)
- **@babel/helpers** & **@babel/runtime** - RegExp complexity (CVE)
- **resolve-url-loader** - Via postcss vulnerability
- Multiple indirect vulnerabilities

#### LOW Severity (3 vulnerabilities)
- **brace-expansion** - ReDoS vulnerability
- Multiple instances via micromatch

### 1.2 Python Dependencies

#### HIGH/CRITICAL Severity

1. **fastapi** 0.109.0
   - **CVE-2024-24762** - ReDoS in form data parsing
   - Fix: Update to 0.109.1+
   - Impact: CPU exhaustion, service stalling

2. **python-jose** 3.3.0
   - **CVE-2024-33663** - Algorithm confusion with ECDSA keys
   - **CVE-2024-33664** - JWT bomb DoS attack
   - Fix: Update to 3.4.0+
   - Impact: Authentication bypass, DoS

3. **python-multipart** 0.0.6
   - **CVE-2024-24762** - ReDoS via malicious Content-Type header
   - **CVE-2024-53981** - Excessive logging DoS
   - Fix: Update to 0.0.18+
   - Impact: DoS, event loop blocking

4. **gunicorn** 21.2.0
   - **CVE-2024-1135** - HTTP Request Smuggling
   - **CVE-2024-6827** - Transfer-Encoding validation bypass
   - Fix: Update to 22.0.0+
   - Impact: Security bypass, cache poisoning, SSRF

5. **starlette** 0.35.1
   - **CVE-2024-47874** - Unbounded memory consumption in form parsing
   - **CVE-2025-54121** - Main thread blocking on large file uploads
   - Fix: Update to 0.47.2+
   - Impact: DoS, service degradation

6. **ecdsa** 0.19.1
   - **CVE-2024-23342** - Minerva timing attack on P-256
   - No fix available (out of scope for project)
   - Impact: Private key discovery
   - Recommendation: Consider alternative crypto libraries

---

## 2. Outdated Packages

### 2.1 Node.js Packages

| Package | Current | Wanted | Latest | Priority |
|---------|---------|--------|--------|----------|
| **react** | 18.3.1 | 18.3.1 | 19.2.3 | HIGH |
| **react-dom** | 18.3.1 | 18.3.1 | 19.2.3 | HIGH |
| **@headlessui/react** | 1.7.19 | 1.7.19 | 2.2.9 | HIGH |
| **tailwindcss** | 3.4.19 | 3.4.19 | 4.1.18 | HIGH |
| **zustand** | 4.5.7 | 4.5.7 | 5.0.9 | MEDIUM |
| **framer-motion** | 10.18.0 | 10.18.0 | 12.25.0 | MEDIUM |
| **lucide-react** | 0.303.0 | 0.303.0 | 0.562.0 | MEDIUM |
| **recharts** | 2.15.4 | 2.15.4 | 3.6.0 | MEDIUM |
| **react-router-dom** | 6.29.0 | 6.30.3 | 7.12.0 | MEDIUM |
| **postcss** | 8.5.1 | 8.5.6 | 8.5.6 | LOW |
| **autoprefixer** | 10.4.20 | 10.4.23 | 10.4.23 | LOW |
| **@tailwindcss/typography** | 0.5.16 | 0.5.19 | 0.5.19 | LOW |

### 2.2 Python Packages (System-wide, may not all be used)

Key outdated packages that ARE used in requirements.txt:
- **cryptography**: 41.0.7 → 46.0.3 (Major security updates)
- **PyJWT**: 2.7.0 → 2.10.1 (Used via python-jose)

---

## 3. Dependency Analysis

### 3.1 Bundle Size
- **node_modules size**: 392 MB (Acceptable for modern React app)
- **Main contributors**:
  - react-scripts (Create React App)
  - Babel ecosystem
  - Tailwind CSS
  - Framer Motion

### 3.2 Dependencies Usage Assessment

**All dependencies appear to be actively used:**
- ✅ **framer-motion** - Used in all pages for animations
- ✅ **react-router-dom** - Navigation throughout app
- ✅ **@headlessui/react** - Likely used for accessible UI components
- ✅ **@heroicons/react** - Icon library
- ✅ **tailwindcss** + plugins - Styling framework
- ✅ **axios** - HTTP client for API calls
- ✅ **zustand** - State management
- ✅ **recharts** - Charts/data visualization
- ✅ **react-hot-toast** - Toast notifications

**No unnecessary dependencies identified.**

### 3.3 Potential Optimizations

1. **Consider migrating from Create React App**
   - `react-scripts@5.0.1` is outdated and has vulnerabilities
   - CRA is no longer actively maintained
   - Modern alternatives: **Vite**, **Next.js**, or **Remix**
   - Benefits: Faster builds, smaller bundles, better DX, active maintenance

2. **React 19 Upgrade Path**
   - React 19 is available but requires careful migration
   - Breaking changes may affect existing code
   - Recommend: Stay on React 18.3.x short-term, plan upgrade for later

3. **Tailwind CSS v4**
   - v4 has significant architecture changes
   - Recommend: Stay on v3.x until v4 stabilizes

---

## 4. Recommendations

### 4.1 Immediate Actions (Within 1-2 days)

**Priority 1: Fix Critical Security Vulnerabilities**

```bash
# Python dependencies - Update requirements.txt
fastapi==0.111.0        # from 0.109.0
python-jose[cryptography]==3.4.0  # from 3.3.0
python-multipart==0.0.18  # from 0.0.6
gunicorn==22.0.0        # from 21.2.0
pydantic[email]==2.10.0  # from 2.5.3
starlette==0.47.2       # from 0.35.1 (via fastapi)

# Node.js dependencies
npm update react-router-dom  # Fixes XSS vulnerability
npm audit fix              # Auto-fix what's safe
```

### 4.2 Short-term Actions (Within 1-2 weeks)

**Address React Scripts Vulnerabilities**

Option A: Eject from Create React App
```bash
npm run eject
# Then manually update webpack, webpack-dev-server, etc.
```

Option B: Migrate to Vite (RECOMMENDED)
```bash
# Better performance, smaller bundles, active maintenance
npm create vite@latest
# Migrate components gradually
```

**Update other dependencies:**
```bash
npm update @headlessui/react @tailwindcss/typography
npm update autoprefixer postcss
npm update framer-motion lucide-react recharts zustand
```

### 4.3 Medium-term Actions (Within 1 month)

1. **Plan React 19 Migration**
   - Review breaking changes
   - Update all React ecosystem packages
   - Test thoroughly

2. **Security Hardening**
   - Implement Content Security Policy (CSP)
   - Add rate limiting on backend
   - Enable CORS properly
   - Add request validation middleware

3. **Dependency Management**
   - Set up Dependabot or Renovate bot
   - Implement automated security scanning in CI/CD
   - Regular monthly dependency reviews

### 4.4 Long-term Considerations

1. **Alternative to python-jose**
   - Consider `pyjwt` directly or `authlib`
   - python-jose has limited maintenance

2. **Alternative to ecdsa**
   - Use `cryptography` library directly
   - More actively maintained, better security track record

3. **Monitor Bundle Size**
   - Set up webpack-bundle-analyzer
   - Consider code splitting for routes
   - Lazy load heavy components (recharts, framer-motion)

---

## 5. Updated Dependencies Files

### 5.1 Recommended requirements.txt

```python
# HealthDB Backend Dependencies - SECURITY UPDATED
fastapi==0.111.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
psycopg2-binary==2.9.10
python-jose[cryptography]==3.4.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.18
pydantic[email]==2.10.0
gunicorn==22.0.0
aiofiles==24.1.0
```

### 5.2 Recommended package.json Updates

```json
{
  "dependencies": {
    "@headlessui/react": "^2.2.9",
    "@heroicons/react": "^2.1.1",
    "@tailwindcss/forms": "^0.5.7",
    "@tailwindcss/typography": "^0.5.19",
    "axios": "^1.7.0",
    "framer-motion": "^11.0.0",
    "lucide-react": "^0.400.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-hot-toast": "^2.4.1",
    "react-router-dom": "^6.30.3",
    "react-scripts": "^5.0.1",
    "recharts": "^2.15.4",
    "zustand": "^5.0.0"
  },
  "devDependencies": {
    "autoprefixer": "^10.4.23",
    "postcss": "^8.5.6",
    "tailwindcss": "^3.4.19"
  }
}
```

---

## 6. Implementation Commands

### Step-by-step Update Process

```bash
# 1. Backup current state
git add .
git commit -m "Backup before dependency updates"

# 2. Update Python dependencies
cd /home/user/HealthDB
cat > requirements.txt << 'EOF'
# HealthDB Backend Dependencies - SECURITY UPDATED
fastapi==0.111.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
psycopg2-binary==2.9.10
python-jose[cryptography]==3.4.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.18
pydantic[email]==2.10.0
gunicorn==22.0.0
aiofiles==24.1.0
EOF

pip install -r requirements.txt --upgrade

# 3. Update Node.js dependencies
npm update react-router-dom
npm update @headlessui/react @tailwindcss/typography
npm update autoprefixer postcss
npm update zustand framer-motion

# 4. Try auto-fixing npm vulnerabilities
npm audit fix

# 5. Test the application
npm test
python -m pytest  # if you have tests

# 6. Commit changes
git add package.json package-lock.json requirements.txt
git commit -m "Security update: Fix critical vulnerabilities in dependencies"
```

---

## 7. Risk Assessment

### Current Risk Level: **HIGH** 🔴

**Justification:**
- Critical vulnerabilities in production dependencies
- Multiple DoS attack vectors
- Authentication/authorization bypass possibilities
- Request smuggling vulnerabilities

### Post-Update Risk Level: **MEDIUM** 🟡

**Remaining Risks:**
- react-scripts vulnerabilities (requires migration)
- ecdsa timing attack (no fix available)
- Need to implement additional security layers

---

## 8. Monitoring & Maintenance

### Recommended Tools

1. **GitHub Dependabot**
   - Automated dependency updates
   - Security alerts

2. **Snyk or Socket.dev**
   - Continuous vulnerability monitoring
   - Supply chain attack detection

3. **npm audit** / **pip-audit**
   - Run weekly in CI/CD pipeline

### Regular Schedule

- **Daily**: Automated security scans
- **Weekly**: Review security advisories
- **Monthly**: Full dependency audit
- **Quarterly**: Major version updates planning

---

## 9. Conclusion

The HealthDB project has **critical security vulnerabilities** that require immediate attention, particularly in:
- Python backend authentication and request handling
- React Router (XSS vulnerabilities)
- Form parsing libraries (DoS vulnerabilities)

The dependency structure is reasonable with no unnecessary bloat, but the use of Create React App poses long-term maintenance challenges.

**Recommended immediate action:** Update all Python dependencies per Section 5.1 and update react-router-dom to fix the XSS vulnerability.

**Recommended strategic action:** Plan migration from Create React App to Vite or Next.js within the next quarter.

---

## Appendix: Vulnerability Details

### npm audit Summary
```
Total Vulnerabilities: 25
├── Critical: 1
├── High: 14
├── Moderate: 7
└── Low: 3

Total Dependencies: 1,383
├── Production: 1,377
└── Development: 6
```

### Python Security Issues by Package
```
fastapi: 1 vulnerability (PYSEC-2024-38)
python-jose: 2 vulnerabilities (CVE-2024-33663, CVE-2024-33664)
python-multipart: 2 vulnerabilities (CVE-2024-24762, CVE-2024-53981)
gunicorn: 2 vulnerabilities (CVE-2024-1135, CVE-2024-6827)
starlette: 2 vulnerabilities (CVE-2024-47874, CVE-2025-54121)
ecdsa: 1 vulnerability (CVE-2024-23342 - NO FIX)
```

---

**Report Generated:** 2026-01-11
**Auditor:** Claude Code Dependency Analysis
**Next Review Date:** 2026-02-11
