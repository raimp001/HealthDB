import React from 'react';
import Modal from './Modal';

/** Replacement for window.confirm, with a distinct style for destructive acts. */
const ConfirmDialog = ({
  open, title, description, confirmLabel = 'Confirm',
  destructive = false, onConfirm, onClose, busy = false,
}) => (
  <Modal open={open} title={title} description={description} onClose={onClose}>
    <div className="flex gap-3">
      <button
        type="button" onClick={onConfirm} disabled={busy}
        className={`flex-1 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
          destructive
            ? 'bg-red-500/90 text-white hover:bg-red-500'
            : 'bg-white text-black hover:bg-gray-100'
        }`}
      >
        {busy ? 'Working…' : confirmLabel}
      </button>
      <button
        type="button" onClick={onClose} disabled={busy}
        className="flex-1 py-2 border border-white/20 text-sm hover:bg-white/5 transition-colors disabled:opacity-50"
      >
        Cancel
      </button>
    </div>
  </Modal>
);

export default ConfirmDialog;
