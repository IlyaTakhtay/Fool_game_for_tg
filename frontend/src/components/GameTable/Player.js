import React from 'react';
import Card from './Card';
import CardStack from 'components/GameTable/CardStack';
import backImage from "assets/images/imperial_back.png"; // путь к рубашке
import 'assets/styles/game/Player.css';

function Player({ player, className, isAttacker, isDefender }) {
  const statusClass = player.status === 'ready' ? 'border-green' : 'border-red';

  const infoClassName = [
    'player__info',
    isAttacker ? 'player__info--attacker' : '',
    isDefender ? 'player__info--defender' : ''
  ].filter(Boolean).join(' ');

  // Функция для обрезки имени до 16 символов
  const truncateName = (name) => {
    return name.length > 16 ? name.substring(0, 16) + '...' : name;
  };

  return (
    <div className={className}>
      <div className={infoClassName}>
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
