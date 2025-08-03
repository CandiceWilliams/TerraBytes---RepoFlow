import React from 'react';
import './ChoicePage.css';

export default function ChoicePage({ onSelect }) {
  return (
    <div className="choice-page">
      <h1 className="choice-title">Which would you like to edit?</h1>
      <div className="choice-buttons">
        <button
          className="choice-button"
          onClick={() => onSelect('backend')}
        >
          Backend
        </button>
        <button
          className="choice-button"
          onClick={() => onSelect('frontend')}
        >
          Frontend
        </button>
      </div>
    </div>
  );
}