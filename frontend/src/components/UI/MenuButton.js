import React from 'react';
import 'assets/styles/MenuButton.css';

function MenuButton({ onClick, text, className = "" }) {
  return (
    <button className={`menu-button ${className}`} onClick={onClick}>
      {text}
    </button>
  );
}

export default MenuButton;
