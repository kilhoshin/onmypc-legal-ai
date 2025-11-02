/**
 * EULA Dialog Component
 */
import React from 'react';

const EULADialog = ({ eulaText, onAccept, onDecline }) => {
  return (
    <div style={styles.overlay}>
      <div style={styles.dialog}>
        <h2 style={styles.title}>End User License Agreement</h2>

        <div style={styles.content}>
          <pre style={styles.text}>{eulaText}</pre>
        </div>

        <div style={styles.warning}>
          <strong>⚠️ Important:</strong> By accepting, you acknowledge that:
          <ul style={styles.warningList}>
            <li>AI results are not legal advice</li>
            <li>You must independently verify all information</li>
            <li>All responsibility lies with you</li>
          </ul>
        </div>

        <div style={styles.buttons}>
          <button style={styles.declineButton} onClick={onDecline}>
            Decline
          </button>
          <button style={styles.acceptButton} onClick={onAccept}>
            I Accept
          </button>
        </div>
      </div>
    </div>
  );
};

const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  dialog: {
    backgroundColor: '#fff',
    borderRadius: '8px',
    maxWidth: '800px',
    width: '90%',
    maxHeight: '90vh',
    display: 'flex',
    flexDirection: 'column',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
  },
  title: {
    margin: 0,
    padding: '20px',
    borderBottom: '2px solid #e0e0e0',
    fontSize: '24px',
    color: '#333',
  },
  content: {
    flex: 1,
    overflow: 'auto',
    padding: '20px',
    backgroundColor: '#f5f5f5',
  },
  text: {
    whiteSpace: 'pre-wrap',
    fontSize: '14px',
    lineHeight: '1.6',
    fontFamily: 'monospace',
    margin: 0,
  },
  warning: {
    padding: '20px',
    backgroundColor: '#fff3cd',
    borderTop: '2px solid #ffc107',
    borderBottom: '2px solid #e0e0e0',
    fontSize: '14px',
    color: '#856404',
  },
  warningList: {
    marginTop: '10px',
    paddingLeft: '20px',
  },
  buttons: {
    display: 'flex',
    gap: '10px',
    padding: '20px',
    justifyContent: 'flex-end',
  },
  declineButton: {
    padding: '10px 30px',
    fontSize: '16px',
    border: '2px solid #dc3545',
    backgroundColor: '#fff',
    color: '#dc3545',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: 'bold',
  },
  acceptButton: {
    padding: '10px 30px',
    fontSize: '16px',
    border: 'none',
    backgroundColor: '#28a745',
    color: '#fff',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: 'bold',
  },
};

export default EULADialog;
