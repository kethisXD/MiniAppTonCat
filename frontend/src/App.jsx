
import styles from './App.module.css';
import { StreamBackground } from './components/StreamBackground/StreamBackground';
import { useState, useEffect } from 'react';
import { TonConnectUIProvider, TonConnectButton, useTonWallet } from '@tonconnect/ui-react';
import { DonationButton } from './components/DonationButton';

// Manifest URL
const MANIFEST_URL = `${window.location.origin}/tonconnect-manifest.json`;

const getApiBaseUrl = () => {
  // Allow override via query param ?api=...
  const params = new URLSearchParams(window.location.search);
  if (params.get('api')) {
    return params.get('api');
  }

  // Check if running locally (dev mode)
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://192.168.1.151:8000';
  }
  // In production/Telegram, use relative path handled by proxy
  return '/pi';
};

const API_BASE = getApiBaseUrl();

const getVerifyBaseUrl = () => {
  // Allow override via query param ?verify=...
  const params = new URLSearchParams(window.location.search);
  if (params.get('verify')) {
    return params.get('verify');
  }

  // Dev: verifier runs on the HP server (reachable on LAN).
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://192.168.1.150:5557';
  }
  // In production/Telegram, use relative path handled by Caddy (/verify -> verifier).
  return '/verify';
};

const VERIFY_BASE = getVerifyBaseUrl();

const getStreamUrl = () => {
  // Allow override via query param ?stream=...
  const params = new URLSearchParams(window.location.search);
  if (params.get('stream')) {
    return params.get('stream');
  }

  // Check if running locally (dev mode)
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://192.168.1.150:1984/stream.html?src=cat_cam&mode=mse';
  }
  // In production/Telegram, use relative path handled by proxy
  return '/stream.html?src=cat_cam&mode=mse';
};

const STREAM_URL = getStreamUrl();

// Payment network (build-time, NOT from the feeder's /status — the Pi may be offline
// or report a stale flag, which must not change which network we charge on).
// false = MAINNET, true = TESTNET.
const PAYMENT_TESTNET = false;

function AppContent() {
  const [debugMode, setDebugMode] = useState(true);
  // Reflects the feeder's reported network — for the debug overlay only.
  // The payment network is fixed by PAYMENT_TESTNET, not by this.
  const [isTestnet, setIsTestnet] = useState(PAYMENT_TESTNET);
  const wallet = useTonWallet();

  useEffect(() => {
    // Initial fetch to get network mode
    fetch(`${API_BASE}/status`)
      .then(res => res.json())
      .then(data => setIsTestnet(!!data.testnet))
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
    }
  }, []);


  return (
    <div className={styles.app}>
      {/* 1. Video Stream Layer */}
      <StreamBackground
        // Proxy stream via HP Server
        streamUrl={STREAM_URL}
        posterUrl=""
      />

      {/* 2. Top Bar (Overlay) */}
      <div className={styles.topBar}>
        {debugMode && (
          <div className={styles.controlsColumn}>
            {/* Light Control Buttons (Simple ON/OFF) */}
            <div className={styles.controlRow}>
              <button
                className={`${styles.badge} ${styles.lightBadge}`}
                onClick={() => fetch(`${API_BASE}/light/on`, { method: 'POST' }).catch(console.error)}
              >
                🔦 ON
              </button>

              <button
                className={`${styles.badge} ${styles.lightBadge}`}
                onClick={() => fetch(`${API_BASE}/light/off`, { method: 'POST' }).catch(console.error)}
                style={{ background: '#333', color: 'white' }}
              >
                OFF
              </button>
            </div>

            {/* Motor Control Buttons */}
            <div className={styles.controlRow}>
              <button
                className={`${styles.badge} ${styles.lightBadge}`}
                onClick={() => fetch(`${API_BASE}/motor/left`, { method: 'POST' }).catch(console.error)}
                style={{ background: '#e67e22' }}
              >
                ⬅️ Left
              </button>

              <button
                className={`${styles.badge} ${styles.lightBadge}`}
                onClick={() => fetch(`${API_BASE}/motor/right`, { method: 'POST' }).catch(console.error)}
                style={{ background: '#e67e22' }}
              >
                Right ➡️
              </button>
            </div>
          </div>
        )}

        <div style={{ flex: 1 }} /> {/* Spacer */}

        <button
          className={`${styles.badge} ${styles.debugBadge}`}
          onClick={() => setDebugMode(!debugMode)}
        >
          debug
        </button>
      </div>

      {/* 3. Bottom Controls */}
      <div className={styles.bottomBar}>
        {!wallet ? (
          <div className={styles.tonConnectWrapper}>
            <TonConnectButton className={styles.tonBtn} />
          </div>
        ) : (
          <div style={{ width: '80%', display: 'flex', justifyContent: 'center' }}>
            <DonationButton verifyBase={VERIFY_BASE} isTestnet={PAYMENT_TESTNET} />
          </div>
        )}
      </div>

      {/* 3. Debug Overlay - Always rendered but hidden to keep connection alive */}
      <div style={{ display: debugMode ? 'block' : 'none' }}>
        <div style={{ display: debugMode ? 'block' : 'none' }}>
          <DebugOverlay isVisible={debugMode} wallet={wallet} />
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <TonConnectUIProvider manifestUrl={MANIFEST_URL}>
      <AppContent />
    </TonConnectUIProvider>
  );
}

function DebugOverlay({ isVisible, wallet }) {
  const [status, setStatus] = useState({
    online: false,
    voltage: null,
    sensor_error: null,
    camera: false,
    error: null,
    walletConnected: false,
    walletAddress: '',
    testnet: false
  });

  const fetchStatus = () => {
    fetch(`${API_BASE}/status`)
      .then(res => res.json())
      .then(data => {
        console.log("Status Fetch:", data); // Debugging
        setStatus({
          online: true,
          voltage: data.voltage,
          sensor_error: data.sensor_error,
          camera: data.camera_online,
          error: null,
          walletConnected: !!wallet,
          walletAddress: wallet?.account?.address || '',
          testnet: !!data.testnet
        });
      })
      .catch(() => setStatus(prev => ({
        ...prev,
        online: false,
        error: 'Connection lost',
        walletConnected: !!wallet,
        walletAddress: wallet?.account?.address || ''
      })));
  };

  // Poll status every 10 seconds or when made visible
  useEffect(() => {
    if (isVisible) {
      fetchStatus();
    }

    const interval = setInterval(() => {
      if (isVisible) fetchStatus();
    }, 10000); // 10 seconds
    return () => clearInterval(interval);
  }, [isVisible, wallet]);

  return (
    <div className={styles.debugOverlay}>
      <p style={{ fontWeight: 'bold', color: '#ffd700' }}>v2.1 Check</p>
      <p>
        Status: {status.online ? '🟢 Connected' : '🔴 Offline'}
        {status.online && status.testnet && <span style={{ color: '#ff4d4d', fontWeight: 'bold', marginLeft: '5px' }}>(TESTNET)</span>}
      </p>
      {status.online && (
        <p>Camera: {status.camera ? '🟢 Ready' : '🔴 Error'}</p>
      )}
      {status.voltage !== null ? (
        <p style={{ color: status.voltage < 3.6 ? '#ff4d4d' : 'white' }}>
          Voltage: {status.voltage.toFixed(2)}V
        </p>
      ) : (
        <p style={{ color: '#ffaaaa' }}>
          Voltage: {status.sensor_error || 'N/A'}
        </p>
      )}
      {status.error && <p style={{ fontSize: '10px', color: '#ffaaaa' }}>{status.error}</p>}

      <div style={{ marginTop: '8px', borderTop: '1px solid #555', paddingTop: '4px' }}>
        <p>Wallet: {status.walletConnected ? '✅ Linked' : '❌ Null'}</p>
        <p style={{ fontSize: '9px', wordBreak: 'break-all' }}>{status.walletAddress}</p>
      </div>

      <button
        onClick={fetchStatus}
        style={{
          marginTop: '10px',
          padding: '4px 8px',
          fontSize: '12px',
          background: '#444',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer'
        }}
      >
        Refresh Status
      </button>
    </div>
  );
}

export default App;
