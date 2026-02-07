import { useTonConnectUI } from '@tonconnect/ui-react';
import { useState } from 'react';
import styles from '../App.module.css';

const RECEIVER_ADDRESS = "UQCJ0se-AJ78OGP4N7DAj_Am1PcX7wYmeXsSwIDAsC0Tl5P_";
const DONATION_AMOUNT_TON = "0.1"; // Minimal donation
const DONATION_AMOUNT_NANOTONS = "100000000"; // 0.1 * 10^9

export function DonationButton({ apiBase }) {
    const [tonConnectUI] = useTonConnectUI();
    const [status, setStatus] = useState('idle'); // idle, processing, success, error
    const [message, setMessage] = useState('');

    const handleDonation = async () => {
        setStatus('processing');
        setMessage('Please approve the transaction in your wallet...');

        try {
            const transaction = {
                validUntil: Math.floor(Date.now() / 1000) + 360, // 6 minutes
                messages: [
                    {
                        address: RECEIVER_ADDRESS,
                        amount: DONATION_AMOUNT_NANOTONS, // 0.1 TON
                    }
                ]
            };

            const result = await tonConnectUI.sendTransaction(transaction);

            console.log('Transaction success:', result);
            setMessage('Payment successful! Feeding the cat... 😺');

            // Trigger the motor on success
            await fetch(`${apiBase}/feed`, { method: 'POST' });

            setStatus('success');
            setTimeout(() => setStatus('idle'), 3000); // Hide after 3s

        } catch (e) {
            console.error('Transaction failed or canceled:', e);
            setStatus('error');
            setMessage('Donation failed or canceled ❌');
            setTimeout(() => setStatus('idle'), 3000);
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
