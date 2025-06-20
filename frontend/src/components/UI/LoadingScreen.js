import React from 'react';
import LoadingAnimation from './LoadingAnimation';
import './LoadingScreen.css';

const LoadingScreen = ({ status }) => {
    return (
        <div className="loading-screen">
            <LoadingAnimation />
            <p>{status === 'Connecting' ? 'Подключение к игре...' : 'Переподключение...'}</p>
            <p>Статус: {status}</p>
        </div>
    );
};

export default LoadingScreen; 
