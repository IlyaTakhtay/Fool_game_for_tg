import React, { useState, useEffect, useLayoutEffect, useRef } from 'react';
import { getCardSvgPath } from 'utils/cardSvgLinker';

function Card({ card, draggable, className, onCustomDrop, ...props }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isPressed, setIsPressed] = useState(false);
  const [returnAnimation, setReturnAnimation] = useState(null);

  const cardRef = useRef(null);
  const lastHoveredElement = useRef(null);
  const offset = useRef({ x: 0, y: 0 });
  const animationFrameId = useRef();

  useLayoutEffect(() => {
    if (!returnAnimation || !cardRef.current) return;

    const { startX, startY } = returnAnimation;
    const { left: endX, top: endY } = cardRef.current.getBoundingClientRect();
    
    const deltaX = startX - endX;
    const deltaY = startY - endY;

    cardRef.current.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
    cardRef.current.style.transition = 'transform 0s';

    requestAnimationFrame(() => {
      cardRef.current.style.transition = 'transform 0.35s cubic-bezier(0.2, 0.8, 0.4, 1)';
      cardRef.current.style.transform = '';
    });

    setReturnAnimation(null);
  }, [returnAnimation]);

  useEffect(() => {
    if (!isPressed) return;

    const handleMouseMove = (e) => {
      e.preventDefault();
      cancelAnimationFrame(animationFrameId.current);

      animationFrameId.current = requestAnimationFrame(() => {
        if (!cardRef.current) return;

        if (!isDragging) {
          setIsDragging(true);
        }
        
        const x = e.clientX - offset.current.x;
        const y = e.clientY - offset.current.y;
        cardRef.current.style.left = `${x}px`;
        cardRef.current.style.top = `${y}px`;
        cardRef.current.style.transform = 'rotate(5deg) scale(1.1)';

        const elementUnderCursor = document.elementFromPoint(e.clientX, e.clientY);
        const potentialDropZone = elementUnderCursor?.closest('.table-card-slot, [data-is-attack-zone="true"]');
        
        if (lastHoveredElement.current && lastHoveredElement.current !== potentialDropZone) {
          lastHoveredElement.current.classList.remove('drop-zone--active-hover');
        }

        if (potentialDropZone && lastHoveredElement.current !== potentialDropZone) {
          potentialDropZone.classList.add('drop-zone--active-hover');
          lastHoveredElement.current = potentialDropZone;
        } else if (!potentialDropZone) {
          lastHoveredElement.current = null;
        }
      });
    };

    const handleMouseUp = (e) => {
      cancelAnimationFrame(animationFrameId.current);
      if (lastHoveredElement.current) {
        lastHoveredElement.current.classList.remove('drop-zone--active-hover');
        lastHoveredElement.current = null;
      }
      
      setIsPressed(false);
      if (isDragging) {
        const dropPosition = cardRef.current.getBoundingClientRect();
        const wasSuccessful = onCustomDrop ? onCustomDrop(e, card) : false;
        
        setIsDragging(false);

        if (!wasSuccessful) {
          setReturnAnimation({ startX: dropPosition.left, startY: dropPosition.top });
        }
      }
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      cancelAnimationFrame(animationFrameId.current);
    };
  }, [isPressed, isDragging, onCustomDrop, card]);

  const handleMouseDown = (e) => {
    if (!draggable) return;
    e.preventDefault();
    setIsPressed(true);
    const rect = e.target.getBoundingClientRect();
    offset.current = { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  return (
    <img
      ref={cardRef}
      src={getCardSvgPath(card)}
      alt={`${card.rank} of ${card.suit}`}
      className={`card-svg ${isDragging ? 'dragging' : ''} ${className || ''}`}
      onMouseDown={handleMouseDown}
      draggable={false}
      style={
        isDragging
          ? {
              position: 'fixed',
              left: '0px',
              top: '0px',
              cursor: 'grabbing',
              zIndex: 1000,
              boxShadow: '0 20px 32px rgba(0,0,0,0.5)',
              transition: 'none',
              pointerEvents: 'none',
            }
          : {}
      }
      {...props}
    />
  );
}

export default React.memo(Card);
