import React, { useEffect, useRef } from 'react';

/**
 * Accessible dialog used to replace window.prompt/confirm/alert, which have
 * no validation, no styling, cannot be dismissed by keyboard predictably,
 * and are suppressed entirely by some browsers.
 */
const Modal = ({ open, title, description, onClose, children, labelledBy = 'modal-title' }) => {
  const panelRef = useRef(null);
  const previouslyFocused = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    previouslyFocused.current = document.activeElement;

    const onKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
        return;
      }
      if (e.key !== 'Tab' || !panelRef.current) return;
      // Keep focus inside the dialog while it is open.
      const focusable = panelRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', onKeyDown);
    const firstField = panelRef.current?.querySelector('input, textarea, button');
    firstField?.focus();

    return () => {
      document.removeEventListener('keydown', onKeyDown);
      previouslyFocused.current?.focus?.();
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-md border border-white/10 bg-black"
      >
        <div className="p-6 border-b border-white/10">
          <h2 id={labelledBy} className="text-lg font-medium">{title}</h2>
          {description && <p className="text-sm text-white/60 mt-1">{description}</p>}
        </div>
        <div className="p-6">{children}</div>
      </div>
    </div>
  );
};

export default Modal;
