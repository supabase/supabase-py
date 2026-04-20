# LifesVibe.NET — 3-Step Launch Setup

---

## ✅ TASK 1 — Supabase Environment Variables in Vercel

Go to: https://vercel.com/matthew-bryan-projects/lifesvibeplatform-/settings/environment-variables

Add these 4 variables. Set each one to apply to **Production + Preview + Development**.

| Variable Name | Value |
|---|---|
| `VITE_SUPABASE_URL` | `https://sprctvxtibrwcdunbogg.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNwcmN0dnh0aWJyd2NkdW5ib2dnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzA0NzIxNzYsImV4cCI6MjA4NjA0ODE3Nn0.gEfHQ81HEWOzkBgAQUkAg6YKcfVSUo8pppxAbuMRQ8c` |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | `sb_publishable_e8MYRMFbAwu6zODuv_dfAg_GPruORoo` |
| `VITE_APP_URL` | `https://www.lifesvibe.net` |

After adding all 4, click **"Redeploy"** on your latest deployment so the new env vars take effect.

---

## ✅ TASK 2 — Connect lifesvibe.net Domain (GoDaddy → Vercel)

### Step A — Add domain in Vercel
Go to: https://vercel.com/matthew-bryan-projects/lifesvibeplatform-/settings/domains

Click **"Add Domain"** and enter: `lifesvibe.net`
Then add a second entry: `www.lifesvibe.net`

Vercel will show you DNS records to add. They will look like the ones below.

### Step B — Update DNS in GoDaddy
Go to: https://dcc.godaddy.com/control/portfolio/lifesvibe.net/settings?subtab=dnssettings

**Delete any existing A records and CNAME records for @ and www, then add these:**

#### For the root domain (lifesvibe.net):
| Type | Name | Value | TTL |
|---|---|---|---|
| `A` | `@` | `76.76.21.21` | 600 |

#### For www subdomain:
| Type | Name | Value | TTL |
|---|---|---|---|
| `CNAME` | `www` | `cname.vercel-dns.com` | 600 |

### Step C — Set www as primary (recommended)
Back in Vercel domains settings, click the arrows next to `www.lifesvibe.net` to set it as primary.
Vercel will auto-redirect `lifesvibe.net` → `www.lifesvibe.net`.

**DNS propagation takes 5–30 minutes.** You can check status at: https://dnschecker.org/#A/lifesvibe.net

---

## ✅ TASK 3 — Protect vite.config.ts from Figma Make Overwrites

Every time Figma Make auto-syncs, it can reset your `vite.config.ts` changes.
Add this file to your GitHub repo root to prevent that:

### Create file: `.figmaignore` (in repo root)
```
vite.config.ts
package.json
```

### Also add a `vercel.json` to lock your build config:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    },
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
```

The `vercel.json` also:
- Fixes SPA routing (all routes → index.html) so page refreshes don't 404
- Caches all assets for 1 year (massive performance boost)
- Adds security headers (required for HIPAA-adjacent wellness platform)

---

## Order of operations

1. Add env vars in Vercel → Redeploy
2. Add `.figmaignore` + `vercel.json` + updated `vite.config.ts` in GitHub (one commit)
3. Add domain in Vercel → Update DNS in GoDaddy → Wait 5-30 min
4. Verify at https://www.lifesvibe.net ✅

