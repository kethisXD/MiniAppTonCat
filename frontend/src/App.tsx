
import styles from './App.module.css';
import { StreamBackground } from './components/StreamBackground/StreamBackground';
import { useState } from 'react';
import { TonConnectUIProvider, TonConnectButton } from '@tonconnect/ui-react';

// Manifest URL (you need to host this file somewhere, or use a placeholder for localhost)
const MANIFEST_URL = 'https://raw.githubusercontent.com/ton-community/tutorials/main/03-client/test/public/tonconnect-manifest.json';

function App() {
    const [debugMode, setDebugMode] = useState(true);

    return (
        <TonConnectUIProvider manifestUrl={MANIFEST_URL}>
            <div className={styles.app}>
                {/* 1. Video Stream Layer */}
                <StreamBackground
                    // Placeholder video for testing (since we don't have RPi stream yet)
                    streamUrl="https://media.w3.org/2010/05/sintel/trailer_hd.mp4"
                    posterUrl="https://media.w3.org/2010/05/sintel/poster.png"
                />

                {/* 2. Top Bar (Overlay) */}
                <div className={styles.topBar}>
                    <div className={styles.deviceInfo}>
                        <span className={styles.badge}>устройство 1</span>
                        {debugMode && <span className={`${styles.badge} ${styles.debugBadge}`}>debug</span>}
                    </div>

                    {/* TON Connect Button (Top Right traditionally, or can be custom placed) */}
                    {/* We can hide default button and use custom if needed, but standard is good for start */}
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
