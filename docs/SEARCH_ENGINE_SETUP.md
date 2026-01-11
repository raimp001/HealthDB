# Search Engine Setup Guide for HealthDB

This guide walks you through submitting HealthDB to major search engines for indexing.

---

## 1. Google Search Console

### Step 1: Access Search Console
1. Go to [Google Search Console](https://search.google.com/search-console)
2. Sign in with your Google account (preferably the one associated with your domain)

### Step 2: Add Your Property
1. Click **"Add property"**
2. Choose **"URL prefix"** option
3. Enter: `https://www.healthdb.ai`
4. Click **"Continue"**

### Step 3: Verify Ownership
Google offers several verification methods. The easiest options:

**Option A: HTML Tag (Recommended)**
1. Google will give you a meta tag like:
   ```html
   <meta name="google-site-verification" content="YOUR_CODE_HERE" />
   ```
2. Add this to `public/index.html` in the `<head>` section
3. Deploy the change
4. Click **"Verify"** in Search Console

**Option B: DNS Record**
1. Add a TXT record to your domain's DNS settings
2. Record value will be provided by Google
3. Wait for DNS propagation (up to 48 hours)
4. Click **"Verify"**

### Step 4: Submit Sitemap
1. In the left sidebar, click **"Sitemaps"**
2. Enter: `sitemap.xml`
3. Click **"Submit"**
4. You should see "Success" status

### Step 5: Request Indexing
1. Go to **"URL Inspection"** in the left sidebar
2. Enter: `https://www.healthdb.ai/`
3. Click **"Request Indexing"**
4. Repeat for key pages:
   - `https://www.healthdb.ai/marketplace`
   - `https://www.healthdb.ai/researchers`
   - `https://www.healthdb.ai/patients`
   - `https://www.healthdb.ai/resources`

### Step 6: Monitor Performance
After a few days, check:
- **Performance** tab for search queries and clicks
- **Coverage** tab for indexing issues
- **Core Web Vitals** for page speed issues

---

## 2. Bing Webmaster Tools

### Step 1: Access Bing Webmaster Tools
1. Go to [Bing Webmaster Tools](https://www.bing.com/webmasters)
2. Sign in with Microsoft account

### Step 2: Add Your Site
1. Click **"Add a Site"**
2. Enter: `https://www.healthdb.ai`

### Step 3: Verify Ownership
**Option A: XML File**
1. Download the BingSiteAuth.xml file provided
2. Add it to `public/` folder
3. Deploy
4. Click **"Verify"**

**Option B: Meta Tag**
1. Add the provided meta tag to `public/index.html`
2. Deploy
3. Click **"Verify"**

**Option C: Import from Google (Easiest)**
1. If you've already set up Google Search Console
2. Click **"Import from GSC"**
3. Authorize the connection
4. Sites are automatically imported and verified

### Step 4: Submit Sitemap
1. Go to **"Sitemaps"** in the dashboard
2. Click **"Submit sitemap"**
3. Enter: `https://www.healthdb.ai/sitemap.xml`
4. Click **"Submit"**

### Step 5: Submit URLs
1. Go to **"URL Submission"**
2. Enter key URLs to prioritize indexing

---

## 3. Other Search Engines

### DuckDuckGo
- Uses Bing's index, so Bing submission covers this

### Yahoo
- Also uses Bing's index

### Yandex (Russian market)
1. Go to [Yandex Webmaster](https://webmaster.yandex.com)
2. Add site and verify
3. Submit sitemap

### Baidu (Chinese market)
1. Go to [Baidu Zhanzhang](https://zhanzhang.baidu.com)
2. Requires Chinese business registration

---

## 4. Rich Results Testing

### Test Structured Data
1. Go to [Rich Results Test](https://search.google.com/test/rich-results)
2. Enter: `https://www.healthdb.ai`
3. Check for any errors in the JSON-LD structured data

### Schema Markup Validator
1. Go to [Schema.org Validator](https://validator.schema.org/)
2. Test your structured data markup

---

## 5. Social Media Debuggers

### Facebook/LinkedIn
1. Go to [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/)
2. Enter your URL
3. Click **"Scrape Again"** to refresh cached data

### Twitter
1. Go to [Twitter Card Validator](https://cards-dev.twitter.com/validator)
2. Enter your URL
3. Preview how links will appear

---

## 6. Ongoing SEO Tasks

### Weekly
- [ ] Check Search Console for crawl errors
- [ ] Monitor Core Web Vitals
- [ ] Review top search queries

### Monthly
- [ ] Update sitemap with new pages
- [ ] Publish new blog/resource content
- [ ] Check for broken links

### Quarterly
- [ ] Review and update meta descriptions
- [ ] Audit page speed
- [ ] Review competitor keywords

---

## 7. Quick Wins for Faster Indexing

1. **Share on social media** - Links from Twitter/LinkedIn help discovery
2. **Get backlinks** - Reach out to healthcare/biotech directories
3. **Submit to directories**:
   - [AngelList](https://angel.co)
   - [Crunchbase](https://crunchbase.com)
   - [Product Hunt](https://producthunt.com)
   - Healthcare-specific directories

4. **Press releases** - Announce launches via PR services

---

## Verification Codes

Add these to `public/index.html` after you get them:

```html
<!-- Google Search Console -->
<meta name="google-site-verification" content="YOUR_CODE" />

<!-- Bing Webmaster Tools -->
<meta name="msvalidate.01" content="YOUR_CODE" />

<!-- Yandex (if needed) -->
<meta name="yandex-verification" content="YOUR_CODE" />
```

---

## Support

For technical SEO issues, check:
- [Google Search Central](https://developers.google.com/search)
- [Bing Webmaster Guidelines](https://www.bing.com/webmasters/help/webmaster-guidelines-30fba23a)
