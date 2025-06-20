import React from 'react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import MenuButton from '../../components/UI/MenuButton';
import Modal from '../../components/UI/Modal';
import 'assets/styles/Pages.css';
import BeautyForm from 'components/UI/BeautyForm';

function AuthMenu() {
  const navigate = useNavigate();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleAuthTelegramm = () => {
    console.log('Telegramm')
    navigate('/coming-soon'); // Переход на страницу со списком игр
  };

  const handleAuthGuest = () => {
    console.log('Гость');
    setIsModalOpen(true); // Открываем модальное окно
    // navigate('/coming-soon'); // Переход на страницу со списком игр
    // Дополнительная логика для создания игры
  };

  const handleCloseModal = () => {
    setIsModalOpen(false); // Закрываем модальное окно
    navigate('/auth-guest'); // Переход на другую страницу после закрытия модалки
  };

  return (
    <div className="page-container">
      <h1 className="form-title">Вход</h1>
      <BeautyForm>
        <MenuButton onClick={handleAuthTelegramm} text="Войти как пользователь telegramm" />
        <MenuButton onClick={handleAuthGuest} text="Войти как гость" />
        <Modal isOpen={isModalOpen} onClose={handleCloseModal} title="Внимание">
          <p>Статистика будет сохраняться только до конца игровой сессии.</p>
        </Modal>
      </BeautyForm>
    </div>
  );
}

export default AuthMenu;
