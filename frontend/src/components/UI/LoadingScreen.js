// LoadingScreen.js

import React from 'react';
import LoadingAnimation from './LoadingAnimation';
import './LoadingScreen.css';

const LoadingScreen = ({ status }) => {
    return (
        // Добавляем класс page-container прямо сюда!
        <div className="page-container loading-screen">
            <LoadingAnimation />
            {/* <p>{status === 'Connecting' ? 'Подключение к игре...' : 'Переподключение...'}</p> */}
            {/* <p>Статус: {status}</p> */}
        </div>
    );
};

export default LoadingScreen;
