import { useTonConnectUI } from '@tonconnect/ui-react';
import { useState } from 'react';
import styles from '../App.module.css';

// Raw (network-agnostic) form of the receiver UQCJ0se…AsC0Tl5P_.
// The user-friendly UQ form carries a MAINNET flag; a testnet wallet chokes on it
// ([TON_CONNECT_SDK_ERROR] NullPointerException). Raw "0:<hex>" works on both networks.
const RECEIVER_ADDRESS = "0:89d2c7be009efc3863f837b0c08ff026d4f717ef0626797b12c080c0b02d1397";
const DONATION_AMOUNT_TON = "0.1"; // Minimal donation
const DONATION_AMOUNT_NANOTONS = "100000000"; // 0.1 * 10^9

// Poll settings for on-chain verification (indexer lag tolerance)
const VERIFY_ATTEMPTS = 10;
const VERIFY_INTERVAL_MS = 3000;

// Build a TON text-comment payload (BOC, base64) carrying the unique nonce.
// op=0 (4 zero bytes) + UTF-8 string = standard text comment that the indexer
// surfaces as in_msg.message. We serialize a single ordinary cell (no refs) by
// hand to avoid pulling a TON SDK + Buffer polyfill into the browser bundle.
// Assumes the payload fits one cell (< 120 bytes), which a 32-char nonce does.
function buildCommentPayload(text) {
    const enc = new TextEncoder().encode(text);
    const data = new Uint8Array(4 + enc.length); // first 4 bytes (op=0) stay zero
    data.set(enc, 4);
    const bits = data.length * 8;
    const cell = new Uint8Array(2 + data.length);
    cell[0] = 0x00; // d1: ordinary cell, 0 refs, level 0
    cell[1] = Math.floor(bits / 8) + Math.ceil(bits / 8); // d2: data length descriptor
    cell.set(data, 2);

    const boc = new Uint8Array(11 + cell.length);
    boc.set([0xb5, 0xee, 0x9c, 0x72], 0); // BOC magic
    boc[4] = 0x01; // flags=0, ref-size=1 byte
    boc[5] = 0x01; // offset-size=1 byte
    boc[6] = 0x01; // cells count = 1
    boc[7] = 0x01; // roots count = 1
    boc[8] = 0x00; // absent = 0
    boc[9] = cell.length & 0xff; // total cells size
    boc[10] = 0x00; // root cell index = 0
    boc.set(cell, 11);

    let bin = '';
    for (const b of boc) bin += String.fromCharCode(b);
    return btoa(bin);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export function DonationButton({ verifyBase, isTestnet }) {
    const [tonConnectUI] = useTonConnectUI();
    const [status, setStatus] = useState('idle'); // idle, processing, success, error
    const [message, setMessage] = useState('');

    const handleDonation = async () => {
        const targetAddress = RECEIVER_ADDRESS;
        // Unique nonce ties THIS payment to THIS feed request (anti-replay on the backend).
        const nonce = crypto.randomUUID().replace(/-/g, '');
        setStatus('processing');
        setMessage(`Please approve the transaction in your wallet... (${isTestnet ? 'TESTNET' : 'MAINNET'})`);

        try {
            const transaction = {
                validUntil: Math.floor(Date.now() / 1000) + 360, // 6 minutes
                messages: [
                    {
                        address: targetAddress,
                        amount: DONATION_AMOUNT_NANOTONS, // 0.1 TON
                        payload: buildCommentPayload(nonce), // nonce as text comment
                    }
                ]
            };

            await tonConnectUI.sendTransaction(transaction);

            // Payment is signed — now verify it on-chain before the motor runs.
            // The Pi /feed is NOT called directly anymore; only the verifier may trigger it.
            setMessage('Verifying payment on-chain... 🔍');

            let fed = false;
            for (let attempt = 0; attempt < VERIFY_ATTEMPTS; attempt++) {
                let data;
                try {
                    const res = await fetch(`${verifyBase}/verify`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ nonce }),
                    });
                    data = await res.json();
                } catch {
                    data = { status: 'pending' };
                }

                if (data.status === 'fed') {
                    fed = true;
                    break;
                }
                if (data.status === 'already_used') {
                    throw new Error('Payment already used');
                }
                if (data.status === 'feed_failed') {
                    throw new Error('Payment OK, but feeder hardware did not respond');
                }
                if (data.status === 'error') {
                    throw new Error('Verification rejected the request');
                }
                // pending → indexer lag, wait and retry
                await sleep(VERIFY_INTERVAL_MS);
            }

            if (!fed) {
                throw new Error('Payment not confirmed in time. If you paid, the cat will not be fed twice — please retry.');
            }

            setMessage('Payment verified! Feeding the cat... 😺');
            setStatus('success');
            setTimeout(() => setStatus('idle'), 3000); // Hide after 3s

        } catch (e) {
            console.error('Transaction failed, canceled, or unverified:', e);
            setStatus('error');
            setMessage(e?.message || 'Donation failed or canceled ❌');
            setTimeout(() => setStatus('idle'), 4000);
        }
    };

    return (
        <>
            <button
                className={`${styles.badge} ${styles.lightBadge}`}
                style={{
                    background: 'linear-gradient(45deg, #0088cc, #00aaff)',
                    color: 'white',
                    fontWeight: 'bold',
                    border: '1px solid rgba(255,255,255,0.2)',
                    marginTop: '10px',
                    width: '100%'
                }}
                onClick={handleDonation}
                disabled={status === 'processing'}
            >
                {status === 'processing' ? 'Processing...' : `🍬 Feed Cat (${DONATION_AMOUNT_TON} TON)`}
            </button>

            {/* Modal Overlay */}
            {status !== 'idle' && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    background: 'rgba(0,0,0,0.7)',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    zIndex: 10000,
                    backdropFilter: 'blur(5px)'
                }}>
                    <div style={{
                        background: '#222',
                        padding: '20px',
                        borderRadius: '16px',
                        maxWidth: '80%',
                        textAlign: 'center',
                        color: 'white',
                        boxShadow: '0 10px 25px rgba(0,0,0,0.5)',
                        border: '1px solid rgba(255,255,255,0.1)'
                    }}>
                        <div style={{ fontSize: '40px', marginBottom: '10px' }}>
                            {status === 'processing' && '⏳'}
                            {status === 'success' && '✅'}
                            {status === 'error' && '❌'}
                        </div>
                        <h3 style={{ margin: '0 0 10px 0' }}>
                            {status === 'processing' && 'Processing'}
                            {status === 'success' && 'Success!'}
                            {status === 'error' && 'Error'}
                        </h3>
                        <p style={{ margin: 0, fontSize: '14px', opacity: 0.9 }}>{message}</p>
                    </div>
                </div>
            )}
        </>
    );
}
