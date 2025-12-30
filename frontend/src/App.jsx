
import styles from './App.module.css';
import { StreamBackground } from './components/StreamBackground/StreamBackground';
import { useState } from 'react';
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
          // Real go2rtc stream from raspberry pi
          streamUrl="http://192.168.1.150:1984/stream.html?src=cat_cam&mode=mse"
          posterUrl=""
        />

        {/* 2. Top Bar (Overlay) */}
        <div className={styles.topBar}>
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

        {/* 3. Debug Overlay (Optional) */}
        {debugMode && (
          <div className={styles.debugOverlay}>
            <p>Status: Connected</p>
            <p>Feeder: Ready</p>
            <p>Temp: 42°C</p>
          </div>
        )}
      </div>
    </TonConnectUIProvider>
  );
}

export default App;
