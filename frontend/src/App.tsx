import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "./api";
import { Dashboard } from "./components/Dashboard";
import { History } from "./components/History";
import { AddSheet } from "./components/AddSheet";
import { Insights } from "./components/Insights";
import { Wealth } from "./components/Wealth";
import { Logo } from "./components/Logo";
import { getInitData, getUser, haptic } from "./telegram";
import type { Space } from "./types";

type Tab = "home" | "history" | "insights" | "wealth";

const TABS: { id: Tab; icon: string; label: string }[] = [
  { id: "home", icon: "🏠", label: "Home" },
  { id: "history", icon: "📜", label: "History" },
  { id: "insights", icon: "📊", label: "Insights" },
  { id: "wealth", icon: "💎", label: "Wealth" },
];

export default function App() {
  const [spaces, setSpaces] = useState<Space[]>([]);
  const [meId, setMeId] = useState<number | null>(null);
  const [activeSpaceId, setActiveSpaceId] = useState<number | null>(null);
  const [tab, setTab] = useState<Tab>("home");
  const [showAdd, setShowAdd] = useState(false);
  const [showSwitch, setShowSwitch] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadMe = useCallback(() => {
    setLoading(true);
    setError(null);
    api
      .me()
      .then((me) => {
        setMeId(me.user.id);
        setSpaces(me.spaces);
        setActiveSpaceId((prev) => prev ?? me.spaces[0]?.id ?? null);
      })
      .catch((e) => {
        if (e instanceof ApiError && e.status === 401) {
          setError(
            "Couldn't verify your Telegram session. Please open this app from the FinBuddy bot.",
          );
        } else {
          setError(e instanceof Error ? e.message : "Something went wrong");
        }
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!getInitData()) {
      setError(
        "Open this dashboard from inside Telegram (via the FinBuddy bot) to sign in.",
      );
      setLoading(false);
      return;
    }
    loadMe();
  }, [loadMe]);

  const activeSpace = spaces.find((s) => s.id === activeSpaceId) ?? null;

  if (loading) return <div className="spinner" />;

  if (error) {
    return (
      <div className="app">
        <div className="center muted">{error}</div>
      </div>
    );
  }

  if (!activeSpace) {
    return <Onboarding onReady={loadMe} />;
  }

  const refresh = () => setRefreshKey((k) => k + 1);

  const user = getUser();

  return (
    <div className="app">
      <div className="header">
        <div className="brand">
          <Logo size={38} />
          <div>
            <h1 className="brand-name">FinBuddy</h1>
            <div className="sub">
              {user ? `Hi ${user.firstName} · ` : ""}
              {activeSpace.name}
            </div>
          </div>
        </div>
        <button
          className="space-switch"
          onClick={() => setShowSwitch(true)}
        >
          {activeSpace.type === "shared" ? "👥" : "🙋"} Switch
        </button>
      </div>

      <div key={`${activeSpace.id}-${refreshKey}`}>
        {tab === "home" && (
          <Dashboard
            space={activeSpace}
            meId={meId ?? 0}
            onSeeAll={() => setTab("history")}
            onAdd={() => setShowAdd(true)}
          />
        )}
        {tab === "history" && <History space={activeSpace} />}
        {tab === "insights" && <Insights space={activeSpace} />}
        {tab === "wealth" && <Wealth space={activeSpace} />}
      </div>

      {(tab === "home" || tab === "history") && (
        <button
          className="fab"
          onClick={() => {
            haptic("light");
            setShowAdd(true);
          }}
        >
          +
        </button>
      )}

      <div className="tabbar">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`tab ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            <span className="ico">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      {showAdd && (
        <AddSheet
          space={activeSpace}
          onClose={() => setShowAdd(false)}
          onAdded={refresh}
        />
      )}

      {showSwitch && (
        <SpaceSwitcher
          spaces={spaces}
          activeId={activeSpace.id}
          onPick={(id) => {
            setActiveSpaceId(id);
            setShowSwitch(false);
          }}
          onClose={() => setShowSwitch(false)}
          onChanged={loadMe}
        />
      )}
    </div>
  );
}

function Onboarding({ onReady }: { onReady: () => void }) {
  const [mode, setMode] = useState<"create" | "join">("create");
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const submit = async () => {
    setBusy(true);
    setErr(null);
    try {
      if (mode === "create") {
        await api.createSpace(name.trim() || "My Budget", "solo", "INR");
      } else {
        await api.joinSpace(code.trim().toUpperCase());
      }
      onReady();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="app">
      <div className="onboard-hero">
        <Logo size={64} />
        <h1>Welcome to FinBuddy</h1>
        <p className="muted">
          Track spending, savings &amp; investments — together or solo.
        </p>
      </div>
      <div className="chip-row">
        <button
          className={`chip ${mode === "create" ? "active" : ""}`}
          onClick={() => setMode("create")}
        >
          Create a space
        </button>
        <button
          className={`chip ${mode === "join" ? "active" : ""}`}
          onClick={() => setMode("join")}
        >
          Join with code
        </button>
      </div>
      <div className="card">
        {mode === "create" ? (
          <>
            <label className="field">Space name</label>
            <input
              placeholder="My Budget"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </>
        ) : (
          <>
            <label className="field">Invite code</label>
            <input
              placeholder="ABC123"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
          </>
        )}
        {err && <p style={{ color: "var(--red)", fontSize: 13 }}>{err}</p>}
        <button className="primary" onClick={submit} disabled={busy}>
          {busy ? "Please wait…" : "Continue"}
        </button>
      </div>
    </div>
  );
}

function SpaceSwitcher({
  spaces,
  activeId,
  onPick,
  onClose,
  onChanged,
}: {
  spaces: Space[];
  activeId: number;
  onPick: (id: number) => void;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);

  const create = async () => {
    if (!name.trim()) return;
    setBusy(true);
    try {
      await api.createSpace(name.trim(), "shared", "INR");
      onChanged();
      onClose();
    } finally {
      setBusy(false);
    }
  };

  const join = async () => {
    if (!code.trim()) return;
    setBusy(true);
    try {
      await api.joinSpace(code.trim().toUpperCase());
      onChanged();
      onClose();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="sheet-backdrop" onClick={onClose}>
      <div className="sheet" onClick={(e) => e.stopPropagation()}>
        <h2>Your spaces</h2>
        {spaces.map((s) => (
          <div
            className="txn"
            key={s.id}
            onClick={() => onPick(s.id)}
            style={{ cursor: "pointer" }}
          >
            <div className="icon">{s.type === "shared" ? "👥" : "🙋"}</div>
            <div className="meta">
              <div className="t">{s.name}</div>
              <div className="s">
                {s.members.length} member{s.members.length > 1 ? "s" : ""} ·
                code {s.invite_code}
              </div>
            </div>
            {s.id === activeId && <span className="badge">active</span>}
          </div>
        ))}

        {creating ? (
          <div style={{ marginTop: 14 }}>
            <label className="field">New shared space name</label>
            <input
              placeholder="Home with Partner"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <button className="primary" onClick={create} disabled={busy}>
              Create
            </button>
            <div style={{ height: 12 }} />
            <label className="field">…or join with an invite code</label>
            <input
              placeholder="ABC123"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
            <button className="ghost" onClick={join} disabled={busy}>
              Join space
            </button>
          </div>
        ) : (
          <button
            className="ghost"
            style={{ marginTop: 14, width: "100%" }}
            onClick={() => setCreating(true)}
          >
            + New / join a space
          </button>
        )}
      </div>
    </div>
  );
}
