import React from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import MenuButton from '../../components/UI/MenuButton';
import BeautyForm from '../../components/UI/BeautyForm';
import api from 'utils/apiMiddleware'
import 'assets/styles/Pages.css';
import 'assets/styles/BeautyForm.css'

function FieldGroup({ label, children }) {
    return (
        <div className="create-game-form__field-group">
            <label className="create-game-form__label">{label}</label>
            {children}
        </div>
    );
}

function AuthGuest() {
    const navigate = useNavigate();
    const [playerName, setPlayerName] = useState('');
    const [error, setError] = useState('');

    const handleBackwards = () => {
        navigate('/auth');
    }

    const handleSubmit = async () => {
        // Очищаем предыдущие ошибки
        setError('');

        // Проверяем имя
        if (!playerName || playerName.trim() === '') {
            setError('Пожалуйста, введите имя');
            return;
        }

        // Проверяем длину имени
        const trimmedName = playerName.trim();
        if (trimmedName.length < 2 || trimmedName.length > 20) {
            setError('Имя должно содержать от 2 до 20 символов');
            return;
        }

        try {
            const authData = await api.post(`/auth_guest?player_name=${encodeURIComponent(trimmedName)}`);
            console.log('Ответ от сервера:', authData);

            if (authData.playerId) {
                // Сохраняем данные авторизации
                sessionStorage.setItem('playerId', authData.playerId);
                sessionStorage.setItem('playerName', trimmedName);

                navigate('/');
            } else {
                setError('Неверный ответ от сервера');
            }
        }
        catch (error) {
            console.error('Ошибка при создании игрока:', error);
            setError(error.response?.data?.detail || 'Не удалось создать игрока. Попробуйте снова.');
        }
    }

    return (
        <div className='page-container' >
            <h1 className="form-title">Вход</h1>
            <BeautyForm>
                <div className="beauty-form__fields">
                    <FieldGroup label="Ваше имя:">
                        <input
                            className="beauty-form__input"
                            type="text"
                            placeholder="Введите ваше имя"
                            value={playerName}
                            onChange={(e) => setPlayerName(e.target.value)}
                            onKeyPress={(e) => {
                                if (e.key === 'Enter') {
                                    handleSubmit();
                                }
                            }}
                        />
                    </FieldGroup>
                    {error && (
                        <div className="beauty-form__error">
                            {error}
                        </div>
                    )}
                </div>
                <div className="beauty-form__buttons">
                    <MenuButton type="button" onClick={handleBackwards} text="Назад" />
                    <MenuButton type="submit" onClick={handleSubmit} text="Создать" />
                </div>
            </BeautyForm>
        </div>
    );
}

export default AuthGuest;

