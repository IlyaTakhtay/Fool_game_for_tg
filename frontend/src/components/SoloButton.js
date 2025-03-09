import React from 'react';
import './SoloButton.css';

function SoloButton({ onClick, text }) {
  return (
    <button className="solo-button" onClick={onClick}>
      {text}
    </button>
  );
}

export default SoloButton;
