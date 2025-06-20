import React from 'react';
import { useNavigate } from 'react-router-dom';
import MenuButton from 'components/UI/MenuButton';
import 'assets/styles/Pages.css';
import BeautyForm from 'components/UI/BeautyForm';
import { ROUTES } from 'constants/routes';

function MenuPage() {
  const navigate = useNavigate();

  // Универсальный обработчик для навигации
  const handleNavigation = (path) => () => {
    navigate(path);
  };

  return (
    <div className="page-container">
      <BeautyForm>
        <MenuButton onClick={handleNavigation(ROUTES.GAMES)} text="Найти игру" />
        <MenuButton onClick={handleNavigation(ROUTES.CREATE_GAME)} text="Создать игру" />
        <MenuButton onClick={handleNavigation(ROUTES.COMING_SOON)} text="Настройки" />
        <MenuButton onClick={handleNavigation(ROUTES.COMING_SOON)} text="Профиль" />
      </BeautyForm>
    </div>
  );
}

export default MenuPage;
