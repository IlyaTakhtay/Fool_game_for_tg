import React from 'react';
import { useNavigate } from 'react-router-dom';
import MenuButton from '../components/UI/MenuButton';
import 'assets/styles/Pages.css';

function ComingSoon() {
  const navigate = useNavigate();

  const handleBackwards = () => {
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate('/');
    }
  };

  return (
    <div className="page-container">
      <h1 className="form-title">В разработке!</h1>
      <MenuButton onClick={handleBackwards} text="Назад" />
    </div>
  );
}

export default ComingSoon;
