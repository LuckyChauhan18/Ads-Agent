# Configuration Guide

## Environment Variables

This project uses environment variables for configuration management. All client-side environment variables in Vite must be prefixed with `VITE_`.

### Setup

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Update values in `.env`:**
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_APP_NAME=SPECTRA
   VITE_APP_VERSION=1.0.0
   VITE_ENABLE_ANALYTICS=true
   VITE_ENABLE_DEBUG=false
   ```

3. **Never commit `.env`** - It's already in `.gitignore`

### Available Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | `http://localhost:8000` |
| `VITE_APP_NAME` | Application name | `SPECTRA` |
| `VITE_APP_VERSION` | Application version | `1.0.0` |
| `VITE_ENABLE_ANALYTICS` | Enable analytics tracking | `true` |
| `VITE_ENABLE_DEBUG` | Enable debug logging | `false` |

### Usage in Code

Import the config object:

```javascript
import config from '@/config/config';

// Access configuration
console.log(config.apiBaseUrl);
console.log(config.appName);
console.log(config.enableDebug);
```

### Axios Configuration

The Axios instance is pre-configured with:
- Base URL from environment variables
- 30-second timeout
- Automatic JWT token injection
- Auto-logout on 401 responses
- FormData header handling

All API calls automatically use this configuration.

### Production Setup

For production deployment, set environment variables in your hosting platform:

**Vercel/Netlify:**
- Add variables in the dashboard (Environment Variables section)

**Docker:**
```dockerfile
ENV VITE_API_BASE_URL=https://api.yourdomain.com
```

**GitHub Pages:**
- Use GitHub Actions secrets and build with them

### Different Environments

Create environment-specific files:

- `.env` - Default (gitignored)
- `.env.local` - Local overrides (gitignored)
- `.env.development` - Development
- `.env.production` - Production
- `.env.staging` - Staging

Vite automatically loads the correct file based on the mode.

### Restart Required

⚠️ **Important:** After changing `.env` values, restart the Vite dev server:

```bash
# Stop the server (Ctrl+C)
# Then restart
npm run dev
```

### Security Notes

- ✅ All secrets should be in `.env` (gitignored)
- ✅ Use `.env.example` for documentation
- ❌ Never hardcode API keys or credentials
- ❌ Never commit `.env` to version control
