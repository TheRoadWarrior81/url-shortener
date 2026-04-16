import { useRef, useState, type KeyboardEvent } from "react";
import "./App.css";

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
        return;
      }

      const data: ShortenResult = await res.json();
      setResult(data);
      setCopied(false);
    } catch {
      setShortenError("Network error. Please check your connection.");
    } finally {
      setShortening(false);
    }
  }

  async function fetchStats(shortId: string) {
    const trimmed = shortId.trim();
    if (!trimmed) return;

    setLoadingStats(true);
    setStatsError("");
    setStats(null);

    try {
      const res = await fetch(`${API_URL}/stats/${trimmed}`);

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setStatsError(data?.message || "Short ID not found.");
        return;
      }

      const data: StatsResult = await res.json();
      setStats(data);
    } catch {
      setStatsError("Network error. Please check your connection.");
    } finally {
      setLoadingStats(false);
    }
  }

  function handleStats() {
    void fetchStats(statsId);
  }

  function handleCopy() {
    if (!result) return;

    void navigator.clipboard.writeText(result.short_url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  function handleKeyDown(event: KeyboardEvent, action: () => void) {
    if (event.key === "Enter") action();
  }

  function jumpToStats(id: string) {
    setStatsId(id);
    void fetchStats(id);
    document.getElementById("stats-section")?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <span className="logo">PrecisionLink</span>
        </div>
        <div className="header-right">
          <a
            href="https://github.com/TheRoadWarrior81/url-shortener"
            target="_blank"
            rel="noopener noreferrer"
            className="source-link"
          >
            View source
          </a>
          <button className="btn-primary" onClick={() => inputRef.current?.focus()}>
            Shorten a URL
          </button>
        </div>
      </header>

      <section className="hero-shell">
        <div className="hero">
          <div className="hero-eyebrow">AWS Serverless · Lambda · DynamoDB</div>
          <h1 className="hero-title">
            The architect&apos;s tool for <span>precise</span> navigation.
          </h1>
          <p className="hero-sub">
            Transform cluttered URLs into clean, high-performance short links — deployed on AWS with
            real-time click tracking.
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
                  onChange={(event) => {
                    setUrl(event.target.value);
                    setShortenError("");
                  }}
                  onKeyDown={(event) => handleKeyDown(event, handleShorten)}
                  aria-label="Long URL to shorten"
                />
              </div>

              <button className="btn-primary btn-lg" onClick={handleShorten} disabled={shortening || !url.trim()}>
                {shortening ? "Shortening…" : "Shorten"}
              </button>
            </div>

            {shortenError && (
              <div className="error-msg" role="alert">
                {shortenError}
              </div>
            )}

            {result && (
              <div className="result-row">
                <div className="result-link-card">
                  <div className="result-text">
                    <div className="result-label">Resulting link</div>
                    <a href={result.short_url} target="_blank" rel="noopener noreferrer" className="result-url">
                      {result.short_url}
                    </a>
                  </div>

                  <button className={`copy-btn${copied ? " copied" : ""}`} onClick={handleCopy}>
                    {copied ? "✓ Copied" : "Copy"}
                  </button>
                </div>

                <button className="btn-primary btn-sm" onClick={() => jumpToStats(result.short_id)}>
                  View stats →
                </button>
              </div>
            )}
          </div>
        </div>
      </section>

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
                onChange={(event) => {
                  setStatsId(event.target.value);
                  setStatsError("");
                }}
                onKeyDown={(event) => handleKeyDown(event, handleStats)}
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
            <p className="stats-error" role="alert">
              {statsError}
            </p>
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
            <p className="stats-empty">Enter a short ID above to view click analytics.</p>
          )}
        </div>
      </section>

      <footer className="footer">
        <div>
          <div className="footer-logo">PrecisionLink</div>
          <div className="footer-copy">Built with AWS Lambda · DynamoDB · API Gateway · CloudFront</div>
        </div>
        <nav className="footer-nav">
          <a href="https://github.com/TheRoadWarrior81/url-shortener" target="_blank" rel="noopener noreferrer">
            GitHub
          </a>
          <a href={API_URL} target="_blank" rel="noopener noreferrer">
            API Base
          </a>
        </nav>
      </footer>
    </div>
  );
}
