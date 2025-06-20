import React from 'react';
import './ConnectionStatus.css';

const ConnectionStatus = ({ status, isUsingMocks }) => {
    if (process.env.NODE_ENV !== 'development') {
        return null;
    }

    return (
        <div className="connection-status">
            {status} {isUsingMocks && '(Mocks)'}
        </div>
    );
};

export default ConnectionStatus; 
