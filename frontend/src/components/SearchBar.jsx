/**
 * Search Bar Component
 */
import React, { useState } from 'react';

const SearchBar = ({ onSearch, isSearching }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isSearching) {
      onSearch(query.trim());
    }
  };

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <div style={styles.inputContainer}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask your Legal AI..."
          style={styles.input}
          disabled={isSearching}
        />
        <button
          type="submit"
          style={{
            ...styles.button,
            ...(isSearching ? styles.buttonDisabled : {}),
          }}
          disabled={isSearching || !query.trim()}
        >
          {isSearching ? 'Searching...' : 'Search'}
        </button>
      </div>
      <p style={styles.hint}>
        Example: "Is a 2-year non-compete clause enforceable in California?"
      </p>
    </form>
  );
};

const styles = {
  form: {
    width: '100%',
    maxWidth: '900px',
    margin: '0 auto',
  },
  inputContainer: {
    display: 'flex',
    gap: '10px',
    marginBottom: '10px',
  },
  input: {
    flex: 1,
    padding: '15px 20px',
    fontSize: '16px',
    border: '2px solid #e0e0e0',
    borderRadius: '8px',
    outline: 'none',
    transition: 'border-color 0.2s',
  },
  button: {
    padding: '15px 40px',
    fontSize: '16px',
    backgroundColor: '#007bff',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 'bold',
    transition: 'background-color 0.2s',
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
    cursor: 'not-allowed',
  },
  hint: {
    fontSize: '14px',
    color: '#666',
    textAlign: 'center',
    margin: 0,
  },
};

export default SearchBar;
