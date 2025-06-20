import React from 'react';
import Card from './Card';
import CardStack from 'components/GameTable/CardStack';
import backImage from "assets/images/imperial_back.png"; // путь к рубашке
import 'assets/styles/game/Player.css';

function Player({ player, className }) {
  const statusClass = player.status === 'ready' ? 'border-green' : 'border-red';

  // Функция для обрезки имени до 16 символов
  const truncateName = (name) => {
    return name.length > 16 ? name.substring(0, 16) + '...' : name;
  };

  return (
    <div className={className}>
      <div className="player__info">
        <div className={`player__profile ${statusClass}`}>
          <img
            src={player.profileImage || backImage}
            alt={`Профиль ${player.name}`}
            className="player__profile-image"
          />
        </div>
        <p className="player__name">{truncateName(player.name)}</p>
      </div>
      <CardStack count={player.cards} backImage={backImage} />
    </div>
  );
}

export default Player;
