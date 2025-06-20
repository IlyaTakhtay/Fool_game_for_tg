import React from 'react';
import 'assets/styles/MenuButton.css';

function MenuButton({ onClick, text }) {
  return (
    <button className="menu-button" onClick={onClick}>
      {text}
    </button>
  );
}

export default MenuButton;
