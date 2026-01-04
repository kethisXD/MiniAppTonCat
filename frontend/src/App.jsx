
import styles from './App.module.css';
import { StreamBackground } from './components/StreamBackground/StreamBackground';
import { useState, useEffect } from 'react';
import { TonConnectUIProvider, TonConnectButton } from '@tonconnect/ui-react';

// Manifest URL
// Manifest URL
const MANIFEST_URL = `${window.location.origin}/tonconnect-manifest.json`;

const getApiBaseUrl = () => {
  // Check if running locally (dev mode)
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://192.168.1.151:8000';
  }
  // In production/Telegram, use relative path handled by proxy
  return '/pi';
};

const API_BASE = getApiBaseUrl();

const getStreamUrl = () => {
  // Check if running locally (dev mode)
  if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    return 'http://192.168.1.150:1984/stream.html?src=cat_cam&mode=mse';
  }
  // In production/Telegram, use relative path handled by proxy
  return '/stream.html?src=cat_cam&mode=mse';
};

const STREAM_URL = getStreamUrl();

function App() {
  const [debugMode, setDebugMode] = useState(true);

  useEffect(() => {
    if (window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
    }
  }, []);


  return (
    <TonConnectUIProvider manifestUrl={MANIFEST_URL}>
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
                  onClick={() => fetch(`${API_BASE}/motor/on`, { method: 'POST' }).catch(console.error)}
                  style={{ background: '#e67e22' }}
                >
                  ⚙️ ON
                </button>

                <button
                  className={`${styles.badge} ${styles.lightBadge}`}
                  onClick={() => fetch(`${API_BASE}/motor/off`, { method: 'POST' }).catch(console.error)}
                  style={{ background: '#333', color: 'white' }}
                >
                  OFF
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
          <div className={styles.tonConnectWrapper}>
            <TonConnectButton className={styles.tonBtn} />
          </div>
        </div>

        {/* 3. Debug Overlay - Always rendered but hidden to keep connection alive */}
        <div style={{ display: debugMode ? 'block' : 'none' }}>
          <div style={{ display: debugMode ? 'block' : 'none' }}>
            <DebugOverlay isVisible={debugMode} />
          </div>
        </div>
      </div>
    </TonConnectUIProvider>
  );
}

function DebugOverlay({ isVisible }) {
  const [status, setStatus] = useState({ online: false, voltage: null, sensor_error: null, camera: false, error: null });

  const fetchStatus = () => {
    fetch(`${API_BASE}/status`)
      .then(res => res.json())
      .then(data => setStatus({
        online: true,
        voltage: data.voltage,
        sensor_error: data.sensor_error,
        camera: data.camera_online,
        error: null
      }))
      .catch(() => setStatus(prev => ({ ...prev, online: false, error: 'Connection lost' })));
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
  }, [isVisible]);

  return (
    <div className={styles.debugOverlay}>
      <p>
        Status: {status.online ? '🟢 Connected' : '🔴 Offline'}
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
