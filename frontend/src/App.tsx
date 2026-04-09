import { useState } from "react";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_URL as string;

interface ShortenResponse {
  short_id: string;
  short_url: string;
}

interface StatsResponse {
  short_id: string;
  original_url: string;
  clicks: number;
}

export default function App() {
  const [url, setUrl] = useState("");
  const [result, setResult] = useState<ShortenResponse | null>(null);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const handleShorten = async () => {
    setError("");
    setResult(null);
    setStats(null);

    if (!url.trim()) {
      setError("Please enter a URL.");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/shorten`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ original_url: url.trim() }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.message || "Failed to shorten URL.");
      }

      const data: ShortenResponse = await res.json();
      setResult(data);
      fetchStats(data.short_id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async (short_id: string) => {
    try {
      const res = await fetch(`${API_BASE}/stats/${short_id}`);
      if (res.ok) {
        const data: StatsResponse = await res.json();
        setStats(data);
      }
    } catch {
      // Stats are best-effort
    }
  };

  const handleCopy = () => {
    if (result?.short_url) {
      navigator.clipboard.writeText(result.short_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="container">
      <h1>✂️ URL Shortener</h1>
      <p className="subtitle">Paste a long URL and get a short one.</p>

      <div className="input-row">
        <input
          type="url"
          placeholder="https://example.com/very/long/url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleShorten()}
        />
        <button onClick={handleShorten} disabled={loading}>
          {loading ? "Shortening…" : "Shorten"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className="result-card">
          <p className="label">Your short link</p>
          <div className="short-url-row">
            <a href={result.short_url} target="_blank" rel="noreferrer">
              {result.short_url}
            </a>
            <button className="copy-btn" onClick={handleCopy}>
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
          {stats !== null && (
            <p className="stats">
              👆 {stats.clicks} click{stats.clicks !== 1 ? "s" : ""}
              <button
                className="copy-btn"
                onClick={() => fetchStats(result!.short_id)}
                style={{ marginLeft: "0.75rem" }}
              >
                Refresh
              </button>
            </p>
          )}
        </div>
      )}
    </div>
  );
}