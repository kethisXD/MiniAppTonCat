
import styles from './StreamBackground.module.css';

interface StreamBackgroundProps {
    streamUrl?: string;
    posterUrl?: string; // Image to show before stream loads
}

export const StreamBackground = ({ streamUrl, posterUrl }: StreamBackgroundProps) => {
    return (
        <div className={styles.container}>
            {streamUrl ? (
                <video
                    className={styles.video}
                    autoPlay
                    muted
                    playsInline
                    loop // For testing mostly
                    poster={posterUrl}
                >
                    <source src={streamUrl} />
                    Your browser does not support the video tag.
                </video>
            ) : (
                <div className={styles.placeholder}>
                    {/* Fallback if no stream is active */}
                    <div className={styles.noise}></div>
                </div>
            )}
            <div className={styles.overlay} />
        </div>
    );
};
