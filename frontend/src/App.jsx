
import styles from './App.module.css';
import { StreamBackground } from './components/StreamBackground/StreamBackground';
import { useState, useEffect } from 'react';
import { TonConnectUIProvider, TonConnectButton } from '@tonconnect/ui-react';

// Manifest URL
const MANIFEST_URL = 'https://raw.githubusercontent.com/ton-community/tutorials/main/03-client/test/public/tonconnect-manifest.json';

function App() {
  const [debugMode, setDebugMode] = useState(true);

  return (
    <TonConnectUIProvider manifestUrl={MANIFEST_URL}>
      <div className={styles.app}>
        {/* 1. Video Stream Layer */}
        <StreamBackground
          // Proxy stream via HP Server
          streamUrl="http://192.168.1.150:1984/stream.html?src=cat_cam&mode=mse"
          posterUrl=""
        />

        {/* 2. Top Bar (Overlay) */}
        <div className={styles.topBar}>
          {/* Light Control Buttons (Simple ON/OFF) */}
          {debugMode && (
            <button
              className={`${styles.badge} ${styles.lightBadge}`}
              onClick={() => fetch('http://192.168.1.151:8000/light/on', { method: 'POST' }).catch(console.error)}
            >
              🔦 ON
            </button>
          )}

          {debugMode && (
            <button
              className={`${styles.badge} ${styles.lightBadge}`}
              onClick={() => fetch('http://192.168.1.151:8000/light/off', { method: 'POST' }).catch(console.error)}
              style={{ marginLeft: '10px', background: '#333', color: 'white' }}
            >
              OFF
            </button>
          )}

          {/* Motor Control Buttons */}
          {debugMode && (
            <button
              className={`${styles.badge} ${styles.lightBadge}`}
              onClick={() => fetch('http://192.168.1.151:8000/motor/on', { method: 'POST' }).catch(console.error)}
              style={{ marginLeft: '20px', background: '#e67e22' }}
            >
              ⚙️ ON
            </button>
          )}

          {debugMode && (
            <button
              className={`${styles.badge} ${styles.lightBadge}`}
              onClick={() => fetch('http://192.168.1.151:8000/motor/off', { method: 'POST' }).catch(console.error)}
              style={{ marginLeft: '10px', background: '#333', color: 'white' }}
            >
              OFF
            </button>
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
          <DebugOverlay />
        </div>
      </div>
    </TonConnectUIProvider>
  );
}

function DebugOverlay() {
  const [status, setStatus] = useState({ online: false, voltage: null, camera: false, error: null });

  const fetchStatus = () => {
    fetch('http://192.168.1.151:8000/status')
      .then(res => res.json())
      .then(data => setStatus({
        online: true,
        voltage: data.voltage,
        camera: data.camera_online,
        error: null
      }))
      .catch(err => setStatus(prev => ({ ...prev, online: false, error: 'Connection lost' })));
  };

  // Poll status every 5 minutes
  useEffect(() => {
    fetchStatus(); // Run immediately

    const interval = setInterval(fetchStatus, 300000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className={styles.debugOverlay}>
      <p>
        Status: {status.online ? '🟢 Connected' : '🔴 Offline'}
      </p>
      {status.online && (
        <p>Camera: {status.camera ? '🟢 Ready' : '🔴 Error'}</p>
      )}
      {status.voltage !== null && (
        <p style={{ color: status.voltage < 3.5 ? '#ff4d4d' : 'white' }}>
          Battery: {status.voltage.toFixed(2)}V {status.voltage < 3.5 && '⚠️'}
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
