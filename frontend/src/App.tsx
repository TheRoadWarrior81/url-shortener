import { useState, useRef, type KeyboardEvent } from "react";

const API_URL = import.meta.env.VITE_API_URL as string;

interface ShortenResult {
  short_url: string;
  short_id: string;
}

interface StatsResult {
  short_id: string;
  original_url: string;
  clicks: number;
}

export default function App() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<ShortenResult | null>(null);
  const [shortenError, setShortenError] = useState("");
  const [shortening, setShortening] = useState(false);
  const [copied, setCopied] = useState(false);

  const [statsId, setStatsId] = useState("");
  const [stats, setStats] = useState<StatsResult | null>(null);
  const [statsError, setStatsError] = useState("");
  const [loadingStats, setLoadingStats] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);

  async function handleShorten() {
    const trimmed = url.trim();
    if (!trimmed) return;
    setShortening(true);
    setShortenError("");
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/shorten`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ original_url: trimmed }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setShortenError(data?.message || "Failed to shorten URL. Please try again.");
      } else {
        const data: ShortenResult = await res.json();
        setResult(data);
      }
    } catch {
      setShortenError("Network error. Please check your connection.");
    } finally {
      setShortening(false);
    }
  }

  async function handleStats() {
    const trimmed = statsId.trim();
    if (!trimmed) return;
    setLoadingStats(true);
    setStatsError("");
    setStats(null);
    try {
      const res = await fetch(`${API_URL}/stats/${trimmed}`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setStatsError(data?.message || "Short ID not found.");
      } else {
        const data: StatsResult = await res.json();
        setStats(data);
      }

      const data: StatsResult = await res.json();
      setStats(data);
    } catch {
      setStatsError("Network error. Please check your connection.");
    } finally {
      setLoadingStats(false);
    }
  }

  function handleCopy() {
    if (!result) return;
    navigator.clipboard.writeText(result.short_url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  function handleKeyDown(e: KeyboardEvent, action: () => void) {
    if (e.key === "Enter") action();
  }

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;700;800;900&family=Inter:wght@400;500;600&display=swap');

        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

        body {
          font-family: 'Inter', sans-serif;
          background: #f7f9fb;
          color: #191c1e;
          -webkit-font-smoothing: antialiased;
        }

        .app { min-height: 100vh; display: flex; flex-direction: column; }

        /* Header */
        .header {
          position: sticky; top: 0; z-index: 50;
          background: #f7f9fb;
          border-bottom: 1px solid #e0e3e5;
          padding: 0 32px;
          height: 64px;
          display: flex; align-items: center; justify-content: space-between;
        }
        .header-left { display: flex; align-items: center; gap: 32px; }
        .logo {
          font-family: 'Manrope', sans-serif;
          font-size: 20px; font-weight: 900;
          letter-spacing: -0.04em; color: #0f172a;
          text-decoration: none;
        }
        .header-right { display: flex; align-items: center; gap: 12px; }
        .btn-primary {
          background: linear-gradient(135deg, #1c3ead 0%, #3a58c6 100%);
          color: white; border: none;
          padding: 8px 22px; border-radius: 100px;
          font-family: 'Manrope', sans-serif;
          font-weight: 700; font-size: 13px;
          cursor: pointer; letter-spacing: 0.01em;
          transition: opacity 0.15s, transform 0.1s;
        }
        .btn-primary:hover { opacity: 0.92; }
        .btn-primary:active { transform: scale(0.97); }
        .btn-primary:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }

        /* Hero */
        .hero {
          max-width: 900px; margin: 0 auto;
          padding: 64px 32px 48px;
          width: 100%;
        }
        .hero-eyebrow {
          font-size: 11px; font-weight: 700;
          letter-spacing: 0.12em; text-transform: uppercase;
          color: #1c3ead; margin-bottom: 16px;
          display: flex; align-items: center; gap: 8px;
        }
        .hero-eyebrow::before {
          content: '';
          display: inline-block; width: 20px; height: 2px;
          background: #1c3ead; border-radius: 2px;
        }
        .hero-title {
          font-family: 'Manrope', sans-serif;
          font-size: clamp(36px, 5vw, 52px);
          font-weight: 900; line-height: 1.08;
          letter-spacing: -0.03em;
          color: #0f172a; margin-bottom: 16px;
        }
        .hero-title span { color: #1c3ead; }
        .hero-sub {
          color: #434654; font-size: 17px;
          line-height: 1.6; max-width: 480px;
          margin-bottom: 40px;
        }

        /* Shortener card */
        .shortener-card {
          background: white;
          border-radius: 16px;
          box-shadow: 0 2px 24px rgba(25,28,30,0.07), 0 0 0 1px rgba(25,28,30,0.04);
          overflow: hidden;
        }
        .input-row {
          display: flex; gap: 12px; align-items: center;
          padding: 20px 20px;
        }
        .url-input-wrap { position: relative; flex: 1; }
        .url-input-icon {
          position: absolute; left: 14px; top: 50%;
          transform: translateY(-50%);
          color: #737686; font-size: 17px; pointer-events: none;
        }
        .url-input {
          width: 100%; padding: 14px 16px 14px 44px;
          background: #f2f4f6; border: 2px solid transparent;
          border-radius: 10px; font-size: 15px;
          color: #191c1e; outline: none;
          font-family: 'Inter', sans-serif;
          transition: border-color 0.15s, background 0.15s;
        }
        .url-input::placeholder { color: #9ea3b0; }
        .url-input:focus { border-color: #1c3ead; background: white; }

        .error-msg {
          color: #ba1a1a; font-size: 13px;
          padding: 0 20px 16px; font-weight: 500;
        }

        /* Result */
        .result-row {
          display: grid; grid-template-columns: 1fr auto;
          gap: 12px; padding: 0 20px 20px; align-items: center;
        }
        .result-link-card {
          background: #f7f9fb;
          border-left: 3px solid #1c3ead;
          border-radius: 10px; padding: 14px 18px;
          display: flex; align-items: center; justify-content: space-between;
          gap: 12px; min-width: 0;
        }
        .result-label {
          font-size: 10px; font-weight: 700;
          letter-spacing: 0.1em; text-transform: uppercase;
          color: #1c3ead; margin-bottom: 4px;
        }
        .result-url {
          font-family: 'Manrope', sans-serif;
          font-size: 17px; font-weight: 700;
          color: #191c1e; white-space: nowrap;
          overflow: hidden; text-overflow: ellipsis;
        }
        .copy-btn {
          background: #dde1ff; color: #001453;
          border: none; padding: 9px 18px;
          border-radius: 100px; font-weight: 700;
          font-size: 13px; cursor: pointer;
          white-space: nowrap;
          transition: background 0.15s, transform 0.1s;
          flex-shrink: 0;
        }
        .copy-btn:hover { background: #b8c4ff; }
        .copy-btn:active { transform: scale(0.96); }
        .copy-btn.copied { background: #c8f0d8; color: #00401a; }

        /* Stats section */
        .stats-section {
          background: #f0f2f5;
          border-top: 1px solid #e0e3e5;
          padding: 56px 32px;
          flex: 1;
        }
        .stats-inner { max-width: 900px; margin: 0 auto; }
        .stats-header {
          display: flex; align-items: flex-end;
          justify-content: space-between; gap: 20px;
          margin-bottom: 28px; flex-wrap: wrap;
        }
        .stats-title {
          font-family: 'Manrope', sans-serif;
          font-size: 28px; font-weight: 900;
          letter-spacing: -0.02em; color: #0f172a;
          margin-bottom: 4px;
        }
        .stats-sub { color: #434654; font-size: 14px; }
        .stats-search-wrap { position: relative; }
        .stats-input {
          padding: 11px 44px 11px 18px;
          border-radius: 100px; border: 1px solid #c3c5d7;
          background: white; font-size: 14px;
          color: #191c1e; outline: none; width: 240px;
          font-family: 'Inter', sans-serif;
          transition: border-color 0.15s;
        }
        .stats-input:focus { border-color: #1c3ead; }
        .stats-input::placeholder { color: #9ea3b0; }
        .stats-search-btn {
          position: absolute; right: 8px; top: 50%;
          transform: translateY(-50%);
          background: none; border: none;
          color: #1c3ead; cursor: pointer;
          padding: 4px; display: flex; align-items: center;
          font-size: 15px;
          transition: color 0.15s;
        }
        .stats-search-btn:hover { color: #3a58c6; }

        /* Stats result card */
        .stats-card {
          background: white;
          border-radius: 16px;
          box-shadow: 0 2px 24px rgba(25,28,30,0.07), 0 0 0 1px rgba(25,28,30,0.04);
          padding: 28px 32px;
          display: grid;
          grid-template-columns: auto 1fr;
          gap: 28px;
          align-items: center;
        }
        .stats-clicks-block {
          text-align: center;
          background: linear-gradient(135deg, #1c3ead 0%, #3a58c6 100%);
          border-radius: 12px; padding: 24px 32px;
          color: white; min-width: 140px;
        }
        .stats-clicks-label {
          font-size: 11px; font-weight: 700;
          letter-spacing: 0.1em; text-transform: uppercase;
          opacity: 0.7; margin-bottom: 8px;
        }
        .stats-clicks-num {
          font-family: 'Manrope', sans-serif;
          font-size: 48px; font-weight: 900;
          line-height: 1; letter-spacing: -0.03em;
        }
        .stats-clicks-sub { font-size: 12px; opacity: 0.6; margin-top: 6px; }
        .stats-details { min-width: 0; }
        .stats-detail-label {
          font-size: 11px; font-weight: 700;
          letter-spacing: 0.1em; text-transform: uppercase;
          color: #737686; margin-bottom: 6px;
        }
        .stats-detail-id {
          font-family: 'Manrope', sans-serif;
          font-size: 22px; font-weight: 800;
          color: #1c3ead; margin-bottom: 16px;
          letter-spacing: -0.02em;
        }
        .stats-detail-url-label {
          font-size: 11px; font-weight: 700;
          letter-spacing: 0.1em; text-transform: uppercase;
          color: #737686; margin-bottom: 6px;
        }
        .stats-detail-url {
          font-size: 14px; color: #434654;
          word-break: break-all; line-height: 1.5;
        }

        .stats-error { color: #ba1a1a; font-size: 14px; font-weight: 500; }
        .stats-empty {
          color: #737686; font-size: 14px;
          text-align: center; padding: 40px 0;
        }

        /* Footer */
        .footer {
          background: #eceef0;
          border-top: 1px solid #e0e3e5;
          padding: 28px 32px;
          display: flex; justify-content: space-between;
          align-items: center; gap: 16px; flex-wrap: wrap;
        }
        .footer-logo {
          font-family: 'Manrope', sans-serif;
          font-weight: 900; font-size: 15px;
          color: #0f172a; letter-spacing: -0.03em;
        }
        .footer-copy { font-size: 12px; color: #737686; margin-top: 2px; }
        .footer-nav { display: flex; gap: 20px; }
        .footer-nav a {
          color: #737686; font-size: 13px;
          text-decoration: none;
          transition: color 0.15s;
        }
        .footer-nav a:hover { color: #191c1e; }

        @media (max-width: 600px) {
          .header { padding: 0 16px; }
          .hero { padding: 40px 16px 32px; }
          .input-row { flex-direction: column; }
          .btn-primary { width: 100%; padding: 14px; font-size: 15px; }
          .result-row { grid-template-columns: 1fr; }
          .stats-section { padding: 40px 16px; }
          .stats-header { flex-direction: column; align-items: flex-start; }
          .stats-input { width: 100%; }
          .stats-search-wrap { width: 100%; }
          .stats-card { grid-template-columns: 1fr; }
          .stats-clicks-block { text-align: left; }
          .footer { padding: 24px 16px; }
        }
      `}</style>

      <div className="app">
        {/* Header */}
        <header className="header">
          <div className="header-left">
            <span className="logo">PrecisionLink</span>
          </div>
          <div className="header-right">
            <a
              href="https://github.com/TheRoadWarrior81/url-shortener"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                color: "#434654", fontSize: "13px", fontWeight: 600,
                textDecoration: "none", display: "flex", alignItems: "center", gap: "6px"
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/>
              </svg>
              View source
            </a>
            <button className="btn-primary" onClick={() => inputRef.current?.focus()}>
              Shorten a URL
            </button>
          </div>
        </header>

        {/* Hero + Shortener */}
        <section style={{ background: "#f7f9fb", flex: "0 0 auto" }}>
          <div className="hero">
            <div className="hero-eyebrow">AWS Serverless · Lambda · DynamoDB</div>
            <h1 className="hero-title">
              The architect&apos;s tool for{" "}
              <span>precise</span> navigation.
            </h1>
            <p className="hero-sub">
              Transform cluttered URLs into clean, high-performance short links — deployed on AWS with real-time click tracking.
            </p>

            <div className="shortener-card">
              <div className="input-row">
                <div className="url-input-wrap">
                  <span className="url-input-icon">🔗</span>
                  <input
                    ref={inputRef}
                    className="url-input"
                    type="url"
                    placeholder="Paste your long URL here..."
                    value={url}
                    onChange={(e) => { setUrl(e.target.value); setShortenError(""); }}
                    onKeyDown={(e) => handleKeyDown(e, handleShorten)}
                    aria-label="Long URL to shorten"
                  />
                </div>
                <button
                  className="btn-primary"
                  onClick={handleShorten}
                  disabled={shortening || !url.trim()}
                  style={{ padding: "14px 32px", fontSize: "15px" }}
                >
                  {shortening ? "Shortening…" : "Shorten"}
                </button>
              </div>

              {shortenError && (
                <div className="error-msg" role="alert">{shortenError}</div>
              )}

              {result && (
                <div className="result-row">
                  <div className="result-link-card">
                    <div style={{ minWidth: 0 }}>
                      <div className="result-label">Resulting link</div>
                      <div className="result-url">{result.short_url}</div>
                    </div>
                    <button
                      className={`copy-btn${copied ? " copied" : ""}`}
                      onClick={handleCopy}
                    >
                      {copied ? "✓ Copied" : "Copy"}
                    </button>
                  </div>
                  <button
                    className="btn-primary"
                    style={{ padding: "12px 20px", fontSize: "13px", flexShrink: 0 }}
                    onClick={() => {
                      setStatsId(result.short_id);
                      setTimeout(() => {
                        document.getElementById("stats-section")?.scrollIntoView({ behavior: "smooth" });
                      }, 100);
                    }}
                  >
                    View stats →
                  </button>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Stats */}
        <section className="stats-section" id="stats-section">
          <div className="stats-inner">
            <div className="stats-header">
              <div>
                <h2 className="stats-title">Quick stats</h2>
                <p className="stats-sub">Verify your link performance in seconds.</p>
              </div>
              <div className="stats-search-wrap">
                <input
                  className="stats-input"
                  type="text"
                  placeholder="Enter short ID…"
                  value={statsId}
                  onChange={(e) => { setStatsId(e.target.value); setStatsError(""); }}
                  onKeyDown={(e) => handleKeyDown(e, handleStats)}
                  aria-label="Short ID to look up stats"
                />
                <button
                  className="stats-search-btn"
                  onClick={handleStats}
                  disabled={loadingStats || !statsId.trim()}
                  aria-label="Fetch stats"
                >
                  {loadingStats ? "…" : "→"}
                </button>
              </div>
            </div>

            {statsError && (
              <p className="stats-error" role="alert">{statsError}</p>
            )}

            {stats && (
              <div className="stats-card">
                <div className="stats-clicks-block">
                  <div className="stats-clicks-label">Total clicks</div>
                  <div className="stats-clicks-num">{stats.clicks.toLocaleString()}</div>
                  <div className="stats-clicks-sub">all time</div>
                </div>
                <div className="stats-details">
                  <div className="stats-detail-label">Short ID</div>
                  <div className="stats-detail-id">{stats.short_id}</div>
                  <div className="stats-detail-url-label">Original URL</div>
                  <div className="stats-detail-url">{stats.original_url}</div>
                </div>
              </div>
            )}

            {!stats && !statsError && !loadingStats && (
              <p className="stats-empty">
                Enter a short ID above to view click analytics.
              </p>
            )}
          </div>
        </section>

        {/* Footer */}
        <footer className="footer">
          <div>
            <div className="footer-logo">PrecisionLink</div>
            <div className="footer-copy">Built with AWS Lambda · DynamoDB · API Gateway · CloudFront</div>
          </div>
          <nav className="footer-nav">
            <a
              href="https://github.com/TheRoadWarrior81/url-shortener"
              target="_blank"
              rel="noopener noreferrer"
            >
              GitHub
            </a>
            <a href={`${API_URL}/docs`} target="_blank" rel="noopener noreferrer">
              API
            </a>
          </nav>
        </footer>
      </div>
    </>
  );
}
