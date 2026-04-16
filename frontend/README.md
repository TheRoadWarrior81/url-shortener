# Frontend (PrecisionLink)

This is the React + TypeScript (Vite) frontend for the URL shortener.

## Environment

Create `.env.development` and/or `.env.production` with:

```bash
VITE_API_URL=https://<your-api-gateway-domain>
```

## Scripts

```bash
npm install
npm run dev      # local dev server
npm run lint     # eslint checks
npm run build    # type-check + production build
npm run preview  # serve production build locally
```

## App behavior

- Shorten URL flow: `POST /shorten`
- Stats lookup flow: `GET /stats/{short_id}`
- Copy short URL to clipboard
- Jump from shorten result into stats section
