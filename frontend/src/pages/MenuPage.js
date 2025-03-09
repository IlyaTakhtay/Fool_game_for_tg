import React from 'react';
import { useNavigate } from 'react-router-dom';
import SoloButton from '../components/SoloButton';
import './Pages.css';
import BeautyForm from '../components/BeautyForm';

function MainMenu() {
  const navigate = useNavigate();

  const handleFindGame = () => {
    navigate('/games'); // Переход на страницу со списком игр
  };

  const handleCreateGame = () => {
    console.log('Создать игру');
    navigate('/create-game'); // Переход на страницу со списком игр
    // navigate('/coming-soon'); // Переход на страницу со списком игр
    // Дополнительная логика для создания игры
  };

  const handleSettings = () => {
    console.log('Настройки');
    navigate('/coming-soon'); // Переход на страницу со списком игр
    // Дополнительная логика для перехода к настройкам
  };

  const handleProfile = () => {
    navigate('/coming-soon'); // Переход на страницу со списком игр
    // Дополнительная логика для перехода к настройкам
  };

  return (
    <div className="page-container">
      <BeautyForm>
      {/* <h1 className="title">Игра "Дурак"</h1> */}
      <SoloButton onClick={handleFindGame} text="Найти игру" />
      <SoloButton onClick={handleCreateGame} text="Создать игру" />
      <SoloButton onClick={handleSettings} text="Настройки" />
      <SoloButton onClick={handleProfile} text="Профиль" />
      </BeautyForm>
    </div>
  );
}

export default MainMenu;
