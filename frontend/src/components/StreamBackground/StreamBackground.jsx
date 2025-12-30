
import styles from './StreamBackground.module.css';

export const StreamBackground = ({ streamUrl, posterUrl }) => {
    return (
        <div className={styles.container}>
            {streamUrl ? (
                <iframe
                    src={streamUrl}
                    className={styles.video}
                    allow="autoplay; encrypted-media; fullscreen; picture-in-picture"
                    frameBorder="0"
                    scrolling="no"
                />
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
