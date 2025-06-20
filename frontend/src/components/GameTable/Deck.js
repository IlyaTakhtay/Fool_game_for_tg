import React from "react";
import CardStack from "./CardStack"; // ваш компонент выше
import "assets/styles/game/Card.css";
import "assets/styles/game/Deck.css";
import spadesIcon from "assets/images/suits/spades.svg";
import heartsIcon from "assets/images/suits/hearts.svg";
import diamondsIcon from "assets/images/suits/diamonds.svg";
import clubsIcon from "assets/images/suits/clubs.svg";

// Карта соответствия типов мастей и их иконок
const SUIT_ICONS = {
  spades: spadesIcon,
  hearts: heartsIcon,
  diamonds: diamondsIcon,
  clubs: clubsIcon,
  'S': spadesIcon,
  'H': heartsIcon,
  'D': diamondsIcon,
  'C': clubsIcon,
  's': spadesIcon,
  'h': heartsIcon,
  'd': diamondsIcon,
  'c': clubsIcon,
  '': null
};


export default function DeckWithTrump({
  count,
  backImage,
  trumpCardImage,
  trumpSuit,
}) {
  console.log('DeckWithTrump received props:', {
    count,
    trumpSuit,
    trumpCardImage: typeof trumpCardImage === 'string' ? trumpCardImage.substring(0, 100) + '...' : 'backImage',
    hasBackImage: !!backImage,
  });

  const trumpSuitIcon = SUIT_ICONS[trumpSuit];

  console.log('Trump suit icon:', {
    trumpSuit,
    hasIcon: !!trumpSuitIcon,
    availableIcons: Object.keys(SUIT_ICONS)
  });

  return (
    <div className="deck">
      <CardStack
        count={count}
        backImage={backImage}
        dense
        maxVisible={36}
        overdraftShow={false}
        rotateTooltip
      />

      {trumpSuit && trumpSuitIcon && (
        <div className="deck__trump-container">
          <img
            src={trumpSuitIcon}
            alt="trump suit"
            className="deck__trump-suit"
          />
          <img
            src={trumpCardImage}
            alt="trump card"
            className="deck__trump-card"
          />
        </div>
      )}
    </div>
  );
}
