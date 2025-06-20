import React from "react";
import "assets/styles/LoadingAnimation.css";

const LoadingAnimation = () => {
  return (
    <div className="loading-container">
      <div className="spinner">
      </div>
      <p className="loading-text">Загрузка...</p>
    </div>
  );
};

export default LoadingAnimation;
