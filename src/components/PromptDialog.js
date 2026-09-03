import React, { useEffect, useState } from 'react';
import Modal from './Modal';

/**
 * Replacement for window.prompt with real validation and inline errors.
 * `fields` is [{ name, label, required, placeholder, type, help }].
 */
const PromptDialog = ({
  open, title, description, fields = [], submitLabel = 'Save',
  onSubmit, onClose, busy = false,
}) => {
  const [values, setValues] = useState({});
  const [error, setError] = useState('');

  // Reset when the dialog opens. Keyed on the field identity/defaults so a
  // reopened dialog with different defaults picks them up, without resetting
  // on every parent render.
  const signature = JSON.stringify(fields.map((f) => [f.name, f.defaultValue || '']));
  useEffect(() => {
    if (!open) return;
    setValues(Object.fromEntries(JSON.parse(signature)));
    setError('');
  }, [open, signature]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const missing = fields.filter((f) => f.required && !String(values[f.name] || '').trim());
    if (missing.length) {
      setError(`${missing[0].label} is required.`);
      return;
    }
    setError('');
    onSubmit(values);
  };

  const field = 'w-full px-3 py-2 bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-white/30 focus:outline-none transition-colors text-sm';

  return (
    <Modal open={open} title={title} description={description} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        {fields.map((f) => (
          <div key={f.name}>
            <label htmlFor={`pd-${f.name}`} className="block text-xs uppercase tracking-wider text-white/60 mb-2">
              {f.label}{f.required && <span className="text-white/50"> (required)</span>}
            </label>
            {f.type === 'textarea' ? (
              <textarea
                id={`pd-${f.name}`} rows={3} placeholder={f.placeholder} className={field}
                value={values[f.name] || ''}
                onChange={(e) => setValues((v) => ({ ...v, [f.name]: e.target.value }))}
              />
            ) : (
              <input
                id={`pd-${f.name}`} type={f.type || 'text'} placeholder={f.placeholder} className={field}
                value={values[f.name] || ''}
                onChange={(e) => setValues((v) => ({ ...v, [f.name]: e.target.value }))}
              />
            )}
            {f.help && <p className="text-xs text-white/50 mt-1">{f.help}</p>}
          </div>
        ))}

        {error && <p role="alert" className="text-red-400 text-sm">{error}</p>}

        <div className="flex gap-3 pt-2">
          <button
            type="submit" disabled={busy}
            className="flex-1 py-2 bg-white text-black text-sm font-medium hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {busy ? 'Working…' : submitLabel}
          </button>
          <button
            type="button" onClick={onClose} disabled={busy}
            className="flex-1 py-2 border border-white/20 text-sm hover:bg-white/5 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </Modal>
  );
};

export default PromptDialog;
