import React from 'react';
import { Navigate } from 'react-router-dom';

const AuthRequiredRoute = ({ children }) => {
    // Проверяем наличие playerId в sessionStorage
    const playerId = sessionStorage.getItem('playerId');
    
    // Если playerId отсутствует, перенаправляем на страницу авторизации
    if (!playerId) {
        return <Navigate to="/auth" />;
    }

    // Если playerId есть, рендерим защищённый контент
    return children;
};

export default AuthRequiredRoute;
