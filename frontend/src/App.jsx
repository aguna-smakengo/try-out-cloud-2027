import React, { useState, useRef, useEffect } from "react";
import Webcam from "react-webcam";
import { 
  User, Lock, ScanFace, CreditCard, Send, History, LayoutDashboard,
  LogOut, ShieldCheck, AlertCircle, Eye, EyeOff, Wallet, Plus,
  Loader2, CheckCircle2, X, RefreshCw, Fingerprint, TrendingUp, ArrowDownLeft
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const API_BASE_URL = import.meta.env.VITE_API_URL || "";

// ---------------------------------------------------------------------------
// Main Application Component
// ---------------------------------------------------------------------------
export default function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState("dashboard");
  const [toast, setToast] = useState(null);
  const [globalLoading, setGlobalLoading] = useState(false);
  const [sessionLoading, setSessionLoading] = useState(true); // For initial session restore

  const showToast = (message, type = "info") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  // *** SESSION RESTORE ON LOAD ***
  useEffect(() => {
    const token = localStorage.getItem("bank_token");
    if (!token) { setSessionLoading(false); return; }
    
    const parts = token.split("_");
    if (parts.length < 3) { localStorage.removeItem("bank_token"); setSessionLoading(false); return; }
    
    const username = parts[1];
    const pin = parts[2];
    
    fetch(`${API_BASE_URL}/me`, {
      method: "GET",
      headers: { "Content-Type": "application/json", "Authorization": token }
    })
    .then(r => r.json())
    .then(data => {
      if (data.status === "success") {
        setUser(data.user);
      } else {
        localStorage.removeItem("bank_token");
      }
    })
    .catch(() => localStorage.removeItem("bank_token"))
    .finally(() => setSessionLoading(false));
  }, []);

  const refreshUserData = async () => {
    if (!user) return;
    setGlobalLoading(true);
    try {
      const token = localStorage.getItem("bank_token");
      const resp = await fetch(`${API_BASE_URL}/me`, {
        method: "GET",
        headers: { "Content-Type": "application/json", "Authorization": token }
      });
      const data = await resp.json();
      if (resp.ok) {
        setUser(data.user);
        showToast("Liquidity Status Synced", "success");
      }
    } catch { showToast("Sync failed", "error"); }
    finally { setGlobalLoading(false); }
  };

  const handleLogout = () => {
    localStorage.removeItem("bank_token");
    setUser(null);
    setView("dashboard");
  };

  // Session loading spinner
  if (sessionLoading) {
    return (
      <div className="session-loading">
        <div className="loading-brand">🏦</div>
        <Loader2 className="animate-spin" size={32} color="var(--accent-blue)" />
        <p>Restoring Secure Session...</p>
      </div>
    );
  }

  return (
    <>
      <AnimatePresence>
        {toast && <Toast toast={toast} onClose={() => setToast(null)} />}
        {globalLoading && (
          <motion.div 
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="global-loader"
          >
            <Loader2 className="animate-spin" size={48} color="var(--accent-blue)" />
          </motion.div>
        )}
      </AnimatePresence>

      {!user ? (
        <LoginScreen onLogin={(userData) => setUser(userData)} showToast={showToast} />
      ) : (
        <div className="bank-app">
          <Sidebar activeView={view} setView={setView} onLogout={handleLogout} />
          <div className="content-area">
            <Header user={user} onRefresh={refreshUserData} loading={globalLoading} />
            <main className="view-container">
              <AnimatePresence mode="wait">
                <motion.div
                  key={view}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -12 }}
                  transition={{ duration: 0.25, ease: "easeOut" }}
                >
                  {view === "dashboard" && <Dashboard user={user} setView={setView} showToast={showToast} onRefresh={refreshUserData} />}
                  {view === "transfer" && <TransferView user={user} showToast={showToast} onComplete={refreshUserData} />}
                  {view === "recognition" && <SecurityView user={user} showToast={showToast} onRefresh={refreshUserData} />}
                  {view === "history" && <HistoryView />}
                </motion.div>
              </AnimatePresence>
            </main>
          </div>
        </div>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// Sidebar
// ---------------------------------------------------------------------------
function Sidebar({ activeView, setView, onLogout }) {
  const items = [
    { id: "dashboard", label: "Dashboard", icon: <LayoutDashboard size={20} /> },
    { id: "transfer",  label: "Transfer",  icon: <Send size={20} /> },
    { id: "recognition", label: "Face ID", icon: <ScanFace size={20} /> },
    { id: "history",   label: "History",   icon: <History size={20} /> },
  ];
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="logo-icon">🏦</span>
        <div>
          <div className="brand-name">Recognition</div>
          <div className="brand-tag">Vault Elite</div>
        </div>
      </div>
      <nav className="sidebar-nav">
        {items.map(item => (
          <motion.button
            key={item.id}
            whileHover={{ x: 4 }}
            whileTap={{ scale: 0.96 }}
            className={`nav-item ${activeView === item.id ? "active" : ""}`}
            onClick={() => setView(item.id)}
          >
            <div className="icon-box">{item.icon}</div>
            <span>{item.label}</span>
          </motion.button>
        ))}
      </nav>
      <div className="sidebar-footer">
        <button className="nav-item" onClick={onLogout}>
          <div className="icon-box"><LogOut size={20} /></div>
          <span>Terminate Session</span>
        </button>
      </div>
    </aside>
  );
}

// ---------------------------------------------------------------------------
// Header
// ---------------------------------------------------------------------------
function Header({ user, onRefresh, loading }) {
  return (
    <header className="app-header">
      <div className="header-left">
        <h1>Overview</h1>
        <p>Security Level: <span className="text-success">Maximum</span></p>
      </div>
      <div className="header-right">
        <motion.button whileHover={{ rotate: 180 }} transition={{ duration: 0.4 }}
          className="refresh-btn" onClick={onRefresh} disabled={loading}
        >
          <RefreshCw size={18} className={loading ? "animate-spin" : ""} />
        </motion.button>
        <div className="user-profile-chip">
          <div className="profile-text">
            <span className="name">{user.username}</span>
            <span className="tier">Premium Member</span>
          </div>
          <div className="avatar-ring">
            <img src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user.username}`} alt="avatar" />
          </div>
        </div>
      </div>
    </header>
  );
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------
function Dashboard({ user, setView, showToast, onRefresh }) {
  const [showBalance, setShowBalance] = useState(true);
  const [depositOpen, setDepositOpen] = useState(false);

  return (
    <div className="dashboard-layout">
      {/* Digital Card */}
      <motion.div
        whileHover={{ y: -6, rotateX: 3 }}
        transition={{ type: "spring", stiffness: 250, damping: 20 }}
        className="premium-card"
      >
        <div className="card-top-row">
          <div className="card-chip" />
          <div className="card-vendor">ELITE BANK</div>
        </div>
        <div className="card-balance-section">
          <div className="balance-label">Total Liquidity</div>
          <div className="balance-value">
            {showBalance
              ? `$${user.balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}`
              : "••••••••"}
            <button className="visibility-toggle" onClick={() => setShowBalance(!showBalance)}>
              {showBalance ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>
        <div className="card-bottom-row">
          <div className="card-number">{user.card_number}</div>
          <div className="card-holder">{user.username.toUpperCase()}</div>
        </div>
      </motion.div>

      {/* Status Pills */}
      <div className="status-pills">
        <div className="pill">
          <TrendingUp size={16} />
          <span>Status: <strong className="text-success">Active</strong></span>
        </div>
        <div className="pill">
          <Fingerprint size={16} />
          <span>Biometrics: <strong className={user.face_image_key ? "text-success" : "text-warning"}>
            {user.face_image_key ? "Verified" : "Pending"}
          </strong></span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="quick-action-bar">
        <motion.button whileHover={{ y: -6 }} className="action-btn primary" onClick={() => setView("transfer")}>
          <div className="btn-circle"><Send size={22} /></div>
          <span>Send Money</span>
        </motion.button>
        <motion.button whileHover={{ y: -6 }} className="action-btn secondary" onClick={() => setDepositOpen(true)}>
          <div className="btn-circle"><Plus size={22} /></div>
          <span>Deposit</span>
        </motion.button>
        <motion.button whileHover={{ y: -6 }} className="action-btn secondary" onClick={() => setView("recognition")}>
          <div className="btn-circle"><ScanFace size={22} /></div>
          <span>Face ID</span>
        </motion.button>
      </div>

      <AnimatePresence>
        {depositOpen && (
          <DepositModal user={user} onClose={() => setDepositOpen(false)} showToast={showToast} onComplete={onRefresh} />
        )}
      </AnimatePresence>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Deposit Modal
// ---------------------------------------------------------------------------
function DepositModal({ onClose, showToast, onComplete }) {
  const [amount, setAmount] = useState("");
  const [loading, setLoading] = useState(false);

  const handleDeposit = async () => {
    const parsed = parseFloat(amount);
    if (!parsed || parsed <= 0) { showToast("Enter a valid amount", "error"); return; }
    setLoading(true);
    try {
      const token = localStorage.getItem("bank_token");
      const resp = await fetch(`${API_BASE_URL}/deposit`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": token },
        body: JSON.stringify({ amount: parsed })
      });
      const data = await resp.json();
      if (resp.ok) {
        showToast(`Successfully deposited $${parsed.toLocaleString()}`, "success");
        onComplete();
        onClose();
      } else {
        showToast(data.message || "Deposit rejected", "error");
      }
    } catch { showToast("Network error", "error"); }
    finally { setLoading(false); }
  };

  return (
    <Modal onClose={onClose}>
      <div className="modal-icon-header">
        <div className="modal-icon-circle"><Plus size={28} /></div>
        <h3>Liquidity Injection</h3>
        <p>Transfer funds from Central Bank reserves.</p>
      </div>
      <div className="input-field-modal">
        <label>Amount (USD)</label>
        <input
          type="text"
          inputMode="decimal"
          value={amount ? parseInt(amount.toString().split(".")[0] || 0).toLocaleString() + (amount.toString().includes(".") ? "." + amount.toString().split(".")[1] : "") : ""}
          onChange={e => setAmount(e.target.value.replace(/[^0-9.]/g, ""))}
          placeholder="0.00"
          autoFocus
        />
      </div>
      <button className="btn-confirm" onClick={handleDeposit} disabled={!amount || loading}>
        {loading ? <Loader2 size={18} className="animate-spin" /> : "Authorize Deposit"}
      </button>
    </Modal>
  );
}

// ---------------------------------------------------------------------------
// Transfer View
// ---------------------------------------------------------------------------
function TransferView({ user, showToast, onComplete }) {
  const [toCard, setToCard] = useState("");
  const [amount, setAmount] = useState("");
  const [step, setStep] = useState("form");
  const [pin, setPin] = useState("");
  const [loading, setLoading] = useState(false);
  const webcamRef = useRef(null);

  // Auto-format card number: insert space every 4 digits
  const handleCardInput = (e) => {
    const raw = e.target.value.replace(/\s/g, "").replace(/\D/g, "").slice(0, 16);
    const formatted = raw.match(/.{1,4}/g)?.join(" ") || raw;
    setToCard(formatted);
  };

  // Auto-format amount: show with thousand separators, store raw
  const handleAmountInput = (e) => {
    const raw = e.target.value.replace(/[^0-9.]/g, "");
    setAmount(raw);
  };

  const formatDisplay = (val) => {
    if (!val) return "";
    const [int, dec] = val.toString().split(".");
    return parseInt(int || 0).toLocaleString() + (dec !== undefined ? "." + dec : "");
  };

  const doTransfer = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("bank_token");
      const resp = await fetch(`${API_BASE_URL}/transfer`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": token },
        body: JSON.stringify({ to_card: toCard, amount: parseFloat(amount) })
      });
      const data = await resp.json();
      if (resp.ok) {
        showToast("Transfer task dispatched to Vault Engine", "success");
        setStep("form"); setAmount(""); setToCard("");
        // Delay refresh
        setTimeout(onComplete, 2000);
      } else {
        showToast(data.message || "Transfer rejected", "error");
        setStep("form");
      }
    } catch { showToast("Network error", "error"); setStep("form"); }
    finally { setLoading(false); }
  };

  const handleFaceAuth = async () => {
    if (!webcamRef.current) return;
    setLoading(true);
    const img = webcamRef.current.getScreenshot();
    try {
      const token = localStorage.getItem("bank_token");
      const resp = await fetch(`${API_BASE_URL}/verify-face`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": token },
        body: JSON.stringify({ image_data: img })
      });
      const data = await resp.json();
      if (resp.ok && data.verified) {
        await doTransfer();
      } else {
        showToast("Biometric mismatch. Identity denied.", "error");
        setLoading(false);
        setStep("form");
      }
    } catch { showToast("Biometric engine error", "error"); setLoading(false); setStep("form"); }
  };

  return (
    <div className="transfer-page">
      <div className="card glass-card">
        <div className="card-head">
          <Send size={24} color="var(--accent-blue)" />
          <h2>Send Liquidity</h2>
        </div>
        <div className="transfer-form">
          {/* Quick-fill shortcut */}
          <div className="quick-banks">
            <span className="quick-label">Quick Transfer To:</span>
            <button className="bank-shortcut" onClick={() => setToCard("1111 2222 3333 4444")}>
              🏛️ Master Admin
            </button>
            <button className="bank-shortcut" onClick={() => setToCard("0000 0000 0000 0000")}>
              🏦 Central Bank
            </button>
          </div>

          <div className="field">
            <label>Recipient Card (Bank ID)</label>
            <div className="input-box">
              <CreditCard size={18} />
              <input
                type="text"
                value={toCard}
                onChange={handleCardInput}
                placeholder="0000 0000 0000 0000"
                maxLength={19}
              />
            </div>
          </div>
          <div className="field">
            <label>Amount (USD)</label>
            <div className="input-box">
              <Wallet size={18} />
              <input
                type="text"
                inputMode="decimal"
                value={formatDisplay(amount)}
                onChange={handleAmountInput}
                placeholder="0.00"
              />
            </div>
          </div>
          <button className="submit-btn" disabled={!toCard || !amount} onClick={() => setStep("auth-choice")}>
            Authenticate Transaction
          </button>
        </div>
      </div>

      <AnimatePresence>
        {step === "auth-choice" && (
          <Modal onClose={() => setStep("form")}>
            <h3>Identity Verification</h3>
            <p style={{ color: "var(--text-secondary)", margin: "0.5rem 0 2rem" }}>Choose your authorization method.</p>
            <div className="auth-grid">
              <motion.button whileHover={{ scale: 1.04 }} className="auth-opt-btn" onClick={() => setStep("face")}>
                <ScanFace size={32} color="var(--accent-blue)" />
                <span>Face Biometric</span>
              </motion.button>
              <motion.button whileHover={{ scale: 1.04 }} className="auth-opt-btn" onClick={() => setStep("pin")}>
                <ShieldCheck size={32} color="var(--accent-purple)" />
                <span>Security PIN</span>
              </motion.button>
            </div>
          </Modal>
        )}
        {step === "face" && (
          <Modal onClose={() => setStep("auth-choice")}>
            <h3>Biometric Scan</h3>
            <p style={{ color: "var(--text-secondary)", margin: "0.5rem 0 1.5rem" }}>Look directly at the camera.</p>
            <div className="scanner-frame">
              <Webcam audio={false} ref={webcamRef} screenshotFormat="image/jpeg" screenshotQuality={0.6}
                videoConstraints={{ width: 320, height: 320, facingMode: "user" }}
                style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              <div className="scan-overlay" />
            </div>
            <button className="btn-confirm" onClick={handleFaceAuth} disabled={loading}>
              {loading ? <Loader2 size={18} className="animate-spin" /> : "Verify & Authorize"}
            </button>
          </Modal>
        )}
        {step === "pin" && (
          <Modal onClose={() => setStep("auth-choice")}>
            <h3>PIN Authorization</h3>
            <p style={{ color: "var(--text-secondary)", margin: "0.5rem 0 1.5rem" }}>Enter your 6-digit security PIN.</p>
            <input type="password" maxLength={6} value={pin} onChange={e => setPin(e.target.value)}
              placeholder="••••••" className="pin-input-big" autoFocus />
            <button className="btn-confirm mt-2" onClick={doTransfer} disabled={loading || !pin}>
              {loading ? <Loader2 size={18} className="animate-spin" /> : "Authorize Transfer"}
            </button>
          </Modal>
        )}
      </AnimatePresence>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Security View (Face ID Registration)
// ---------------------------------------------------------------------------
function SecurityView({ user, showToast, onRefresh }) {
  const [loading, setLoading] = useState(false);
  const webcamRef = useRef(null);

  const handleRegister = async () => {
    if (!webcamRef.current) return;
    setLoading(true);
    const img = webcamRef.current.getScreenshot();
    try {
      const token = localStorage.getItem("bank_token");
      const resp = await fetch(`${API_BASE_URL}/register-face`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": token },
        body: JSON.stringify({ image_data: img })
      });
      const data = await resp.json();
      if (resp.ok) {
        showToast("Transaction queued for processing", "success");
        onClose();
        // Delay refresh slightly to allow SQS -> Processing to complete
        setTimeout(onRefresh, 2000);
      }
      else showToast(data.message || "Capture failed", "error");
    } catch { showToast("Network error", "error"); }
    finally { setLoading(false); }
  };

  return (
    <div className="security-view">
      <div className="card glass-card">
        <div className="card-head">
          <ShieldCheck size={28} color="var(--accent-blue)" />
          <h2>Biometric Protocol</h2>
        </div>
        <p className="security-desc">Map your facial signature to the Vault Elite security layer for password-free authorization.</p>
        <div className="webcam-wrap">
          <div className="scanner-frame large">
            <Webcam audio={false} ref={webcamRef} screenshotFormat="image/jpeg" screenshotQuality={0.6}
              videoConstraints={{ width: 320, height: 320, facingMode: "user" }}
              style={{ width: "100%", height: "100%", objectFit: "cover" }} />
            <div className="scan-overlay" />
          </div>
        </div>
        <button className="btn-confirm" onClick={handleRegister} disabled={loading}>
          {loading ? <><Loader2 size={18} className="animate-spin" /> Recording...</> : "Register Biometric Signature"}
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// History View
// ---------------------------------------------------------------------------
function HistoryView() {
  return (
    <div className="history-view">
      <div className="card glass-card">
        <div className="card-head"><History size={24} color="var(--accent-blue)" /><h2>Activity Log</h2></div>
        <div className="empty-state">
          <History size={56} opacity={0.08} />
          <p>Your transaction ledger is current.</p>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Reusable Modal
// ---------------------------------------------------------------------------
function Modal({ children, onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <motion.div
        initial={{ scale: 0.88, opacity: 0, y: 24 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.88, opacity: 0, y: 24 }}
        transition={{ type: "spring", damping: 22, stiffness: 300 }}
        className="modal-container"
        onClick={e => e.stopPropagation()}
      >
        <button className="modal-close-x" onClick={onClose}><X size={20} /></button>
        {children}
      </motion.div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Toast
// ---------------------------------------------------------------------------
function Toast({ toast, onClose }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 60 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 60 }}
      className={`toast-premium ${toast.type}`}
    >
      <div className="toast-icon">
        {toast.type === "success" ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
      </div>
      <span className="toast-msg">{toast.message}</span>
      <button onClick={onClose} className="toast-close"><X size={16} /></button>
    </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Login Screen
// ---------------------------------------------------------------------------
function LoginScreen({ onLogin, showToast }) {
  const [username, setUsername] = useState("");
  const [pin, setPin] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleAuth = async (e) => {
    e.preventDefault();
    if (!username.trim() || !pin.trim()) { showToast("Fill in all fields", "error"); return; }
    setLoading(true);
    try {
      const endpoint = isRegistering ? "/register" : "/login";
      const resp = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username.trim(), pin })
      });
      const data = await resp.json();
      if (resp.ok) {
        localStorage.setItem("bank_token", data.token);
        onLogin(data.user);
        showToast(isRegistering ? "Identity established. Welcome." : "Access granted.", "success");
      } else {
        showToast(data.message || "Authentication denied", "error");
      }
    } catch { showToast("Connection protocol failed", "error"); }
    finally { setLoading(false); }
  };

  return (
    <div className="login-page">
      <motion.div initial={{ opacity: 0, scale: 0.92 }} animate={{ opacity: 1, scale: 1 }} className="auth-box">
        <div className="auth-header">
          <div className="logo">🏦</div>
          <h2>Recognition <span>Vault</span></h2>
          <p>Intelligence-Driven Security Platform</p>
        </div>
        <form onSubmit={handleAuth}>
          <div className="input-group-modern">
            <User size={18} color="var(--text-secondary)" />
            <input
              type="text" placeholder="Access Identifier"
              value={username} onChange={e => setUsername(e.target.value)} required
            />
          </div>
          <div className="input-group-modern">
            <Lock size={18} color="var(--text-secondary)" />
            <input
              type="password" placeholder="Security PIN (6 digits)"
              value={pin} onChange={e => setPin(e.target.value)} maxLength={6} required
            />
          </div>
          <motion.button whileHover={{ y: -2 }} whileTap={{ scale: 0.97 }} type="submit" className="auth-btn-main" disabled={loading}>
            {loading ? <Loader2 size={20} className="animate-spin" /> : isRegistering ? "Register Identity" : "Establish Link"}
          </motion.button>
        </form>
        <p className="auth-switch" onClick={() => setIsRegistering(!isRegistering)}>
          {isRegistering ? "Already have access? Sign In" : "New Operator? Create Profile"}
        </p>
      </motion.div>
    </div>
  );
}
