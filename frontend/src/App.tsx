import { useEffect, useState, type CSSProperties } from "react";

type Metrics = {
  day: number;
  population: number;
  employment_rate: number;
  average_satisfaction: number;
  government_balance: number;
  household_savings: number;
  firm_balance: number;
  transactions: number;
};

type District = {
  id: number;
  name: string;
  population: number;
  employment_rate: number;
  satisfaction: number;
  daily_rent: number;
};

type World = {
  day: number;
  seed: number;
  tax_rate: number;
  metrics: Metrics;
  history: Metrics[];
  districts: District[];
  total_money: number;
};

type AgentResponse = {
  agent_type: string;
  proposal: { target_tax_rate: number; rationale: string };
  world: World;
};

async function request<T>(path: string, body?: object): Promise<T> {
  const response = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const details = await response.json();
      message = details.detail ?? message;
    } catch {
      // Keep the HTTP fallback if the response is not JSON.
    }
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return response.json() as Promise<T>;
}

function amount(value: number) {
  return `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value)} cr`;
}

function MetricCard({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <article className="metric-card">
      <span className="metric-label">{label}</span>
      <strong className="metric-number">{value}</strong>
      <span className="metric-hint">{hint}</span>
    </article>
  );
}

function TrendChart({ points }: { points: Metrics[] }) {
  const [series, setSeries] = useState<"average_satisfaction" | "employment_rate">(
    "average_satisfaction",
  );
  const selected = points.length ? points : [{ day: 0, average_satisfaction: 0, employment_rate: 0 }];
  const coords = selected
    .map((point, index) => {
      const x = 20 + (selected.length <= 1 ? 0 : index / (selected.length - 1)) * 560;
      const y = 198 - (point[series] / 100) * 175;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  return (
    <section className="panel trend-panel">
      <div className="panel-header">
        <div>
          <span className="eyebrow">SIMULATION HISTORY</span>
          <h2>City trends</h2>
        </div>
        <select value={series} onChange={(e) => setSeries(e.target.value as typeof series)}>
          <option value="average_satisfaction">Satisfaction</option>
          <option value="employment_rate">Employment rate</option>
        </select>
      </div>
      <div className="chart-wrapper">
        <svg viewBox="0 0 600 225" role="img" aria-label={`Time series for ${series}`}>
          {[0, 25, 50, 75, 100].map((percent) => {
            const y = 198 - percent * 1.75;
            return (
              <g key={percent}>
                <line x1="20" x2="580" y1={y} y2={y} stroke="#213744" strokeDasharray="3 7" />
                <text x="0" y={y + 4} className="chart-tick">{percent}</text>
              </g>
            );
          })}
          <polyline fill="none" stroke="#53e3c6" strokeWidth="3.5" points={coords} />
          {selected.length === 1 && <circle cx="20" cy="198" r="4" fill="#53e3c6" />}
          <text x="20" y="221" className="chart-tick">DAY {selected[0].day}</text>
          <text x="580" y="221" className="chart-tick" textAnchor="end">
            DAY {selected[selected.length - 1].day}
          </text>
        </svg>
      </div>
    </section>
  );
}

function App() {
  const [world, setWorld] = useState<World | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [taxRate, setTaxRate] = useState(12);
  const [selectedDistrict, setSelectedDistrict] = useState(0);
  const [seed, setSeed] = useState(42);
  const [mayorMessage, setMayorMessage] = useState("");

  useEffect(() => {
    request<World>("/api/world")
      .then((data) => {
        setWorld(data);
        setTaxRate(data.tax_rate * 100);
        setSeed(data.seed);
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  async function action<T>(path: string, payload: object, transform?: (data: T) => World) {
    setBusy(true);
    setError("");
    try {
      const data = await request<T>(path, payload);
      const next = transform ? transform(data) : (data as World);
      setWorld(next);
      setTaxRate(next.tax_rate * 100);
      return data;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      return null;
    } finally {
      setBusy(false);
    }
  }

  const district = world?.districts.find((item) => item.id === selectedDistrict);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-icon">◎</span><div>EARTH<span>ONLINE</span></div></div>
        <span className="sidebar-label">WORLD CONTROL</span>
        <div className="nav-link current">▦ <span>City overview</span></div>
        <div className="nav-link disabled">◈ <span>Agent explorer</span><small>soon</small></div>
        <div className="nav-link disabled">▥ <span>Scenario lab</span><small>soon</small></div>
        <div className="sidebar-bottom">
          <div className="system-status"><i /> SIMULATION ENGINE</div>
          <strong>Version 0.1.0</strong>
          <p>Synthetic economy · no real-world calibration</p>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumbs">EARTH ONLINE <span>/</span> CITY ONE <span>/</span> OVERVIEW</div>
          <div className="top-right"><span className="live-dot" /> LOCAL SANDBOX <span className="day-pill">DAY {world?.day ?? "—"}</span></div>
        </header>

        <section className="intro">
          <div>
            <span className="eyebrow">SIMULATION LAB / CITY ONE</span>
            <h1>A living city, one day at a time.</h1>
            <p>Explore how households, businesses and policy decisions shape a synthetic society.</p>
          </div>
          <div className="step-actions">
            <button disabled={busy || !world} className="button secondary" onClick={() => void action<World>("/api/step", { days: 1 })}>+ 1 day</button>
            <button disabled={busy || !world} className="button primary" onClick={() => void action<World>("/api/step", { days: 30 })}>▶ Run 30 days</button>
          </div>
        </section>

        {error && <div className="error">{error}. Ensure the backend is running at localhost:8000.</div>}
        {!world ? (
          <div className="loading">Connecting to the city simulation…</div>
        ) : (
          <>
            <div className="metrics-grid">
              <MetricCard label="POPULATION" value={world.metrics.population.toLocaleString()} hint="Simulated households" />
              <MetricCard label="EMPLOYMENT" value={`${world.metrics.employment_rate}%`} hint="Households with jobs" />
              <MetricCard label="SATISFACTION" value={`${world.metrics.average_satisfaction}/100`} hint="Mean social well-being" />
              <MetricCard label="CITY TREASURY" value={amount(world.metrics.government_balance)} hint="Government funds" />
            </div>

            <div className="workspace-grid">
              <section className="panel map-panel">
                <div className="panel-header">
                  <div><span className="eyebrow">URBAN MODEL</span><h2>District map</h2></div>
                  <span className="tag">10 DISTRICTS</span>
                </div>
                <p className="muted">Select a district to inspect its simulated residents.</p>
                <div className="district-grid">
                  {world.districts.map((d) => (
                    <button
                      key={d.id}
                      className={`district ${selectedDistrict === d.id ? "selected" : ""}`}
                      style={{ "--district-tone": `${Math.round((d.satisfaction / 100) * 65 + 18)}%` } as CSSProperties}
                      onClick={() => setSelectedDistrict(d.id)}
                    >
                      <span>0{d.id}</span><b>{d.name}</b><small>{d.satisfaction} mood</small>
                    </button>
                  ))}
                </div>
                <div className="map-legend"><span>LOW SATISFACTION</span><div /><span>HIGH SATISFACTION</span></div>
              </section>

              <section className="panel inspect-panel">
                <div className="panel-header"><div><span className="eyebrow">DISTRICT INSPECTOR</span><h2>{district?.name}</h2></div><span className="tag">#{selectedDistrict}</span></div>
                <div className="inspector-art">◉</div>
                <div className="inspector-row"><span>Residents</span><b>{district?.population}</b></div>
                <div className="inspector-row"><span>Employment rate</span><b>{district?.employment_rate}%</b></div>
                <div className="inspector-row"><span>Social satisfaction</span><b>{district?.satisfaction}/100</b></div>
                <div className="inspector-row"><span>Daily housing rent</span><b>{district?.daily_rent} cr</b></div>
                <p className="inspector-note">District boundaries are schematic. Real geography and migration are future features.</p>
              </section>
            </div>

            <div className="workspace-grid lower-grid">
              <TrendChart points={world.history} />
              <section className="panel policy-panel">
                <div className="panel-header"><div><span className="eyebrow">EXPERIMENT CONTROL</span><h2>Fiscal policy</h2></div></div>
                <div className="policy-value">{taxRate.toFixed(0)}<small>% income tax</small></div>
                <input aria-label="Income tax percentage" type="range" min="0" max="50" step="1" value={taxRate} onChange={(e) => setTaxRate(Number(e.target.value))} />
                <div className="range-label"><span>0%</span><span>50%</span></div>
                <button disabled={busy} className="button secondary full" onClick={() => void action<World>("/api/policy", { tax_rate: taxRate / 100 })}>Apply tax change</button>
                <button disabled={busy} className="button text full" onClick={() => void action<AgentResponse>("/api/agent/mayor/decide", {}, (data) => {
                  setMayorMessage(data.proposal.rationale);
                  return data.world;
                })}>Ask mayor agent (demo) ↗</button>
                {mayorMessage && <p className="mayor-message">{mayorMessage}</p>}
              </section>
            </div>

            <footer className="bottom-bar">
              <span>TOTAL MONEY SUPPLY: {amount(world.total_money)} <i>· conserved by double-entry transfers</i></span>
              <div className="reset-control"><label htmlFor="seed">SEED</label><input id="seed" type="number" min="0" value={seed} onChange={(e) => setSeed(Number(e.target.value))} /><button disabled={busy} onClick={() => void action<World>("/api/reset", { seed, population: world.metrics.population })}>↻ Reset city</button></div>
            </footer>
          </>
        )}
      </main>
    </div>
  );
}

export default App;

