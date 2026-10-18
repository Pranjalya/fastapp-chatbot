import React, { useState } from 'react';
import { X, Sliders, Key } from 'lucide-react';
import type { ModelProvider } from '../../types/chat';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  providers: ModelProvider[];
  currentProvider: string;
  currentModel: string;
  nTurns: number;
  apiKey: string;
  temperature: number;
  onSave: (settings: {
    provider: string;
    model: string;
    nTurns: number;
    apiKey: string;
    temperature: number;
  }) => void;
}

export const SettingsModal: React.FC<Props> = ({
  isOpen,
  onClose,
  providers,
  currentProvider,
  currentModel,
  nTurns,
  apiKey,
  temperature,
  onSave,
}) => {
  if (!isOpen) return null;

  const [provider, setProvider] = useState(currentProvider);
  const [model, setModel] = useState(currentModel);
  const [turns, setTurns] = useState(nTurns);
  const [key, setKey] = useState(apiKey);
  const [temp, setTemp] = useState(temperature);

  const selectedProviderObj = providers.find((p) => p.id === provider);

  const handleProviderChange = (newProvider: string) => {
    setProvider(newProvider);
    const pObj = providers.find((p) => p.id === newProvider);
    if (pObj) {
      setModel(pObj.default_model);
    }
  };

  const handleSave = () => {
    onSave({
      provider,
      model,
      nTurns: turns,
      apiKey: key,
      temperature: temp,
    });
    onClose();
  };

  return (
    <div className="modal-overlay" id="settings-modal-overlay">
      <div className="modal-card" id="settings-modal-card" style={{ maxWidth: '520px' }}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sliders size={20} color="var(--accent-secondary)" />
            <h3>Model & Conversation Settings</h3>
          </div>
          <button className="icon-btn" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Provider Selection */}
          <div className="form-group">
            <label className="form-label">AI Provider</label>
            <select
              className="form-select"
              value={provider}
              onChange={(e) => handleProviderChange(e.target.value)}
              id="select-provider"
            >
              {providers.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} {p.has_server_key ? '(Server Key Configured)' : '(Requires Key)'}
                </option>
              ))}
            </select>
          </div>

          {/* Model Selection */}
          <div className="form-group">
            <label className="form-label">Model Name</label>
            <select
              className="form-select"
              value={model}
              onChange={(e) => setModel(e.target.value)}
              id="select-model"
            >
              {selectedProviderObj?.models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>

          {/* API Key Override */}
          <div className="form-group">
            <label className="form-label">
              API Key (Optional Override)
            </label>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <Key size={16} style={{ position: 'absolute', left: '12px', color: 'var(--text-muted)' }} />
              <input
                type="password"
                className="form-input"
                style={{ paddingLeft: '38px', width: '100%' }}
                placeholder={selectedProviderObj?.has_server_key ? 'Using server key from .env' : 'Enter API key'}
                value={key}
                onChange={(e) => setKey(e.target.value)}
                id="input-api-key"
              />
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Leave blank to use the backend configured environment key.
            </span>
          </div>

          {/* N-Turns Retention Slider */}
          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label className="form-label">
                N-Turn Conversation Retention: <strong>{turns} turns ({turns * 2} raw messages)</strong>
              </label>
            </div>
            <input
              type="range"
              min="2"
              max="15"
              step="1"
              value={turns}
              onChange={(e) => setTurns(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--accent-primary)', cursor: 'pointer' }}
              id="input-n-turns"
            />
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Older turns beyond {turns} exchanges will be condensed into the running rolling summary.
            </span>
          </div>

          {/* Temperature Slider */}
          <div className="form-group">
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <label className="form-label">Temperature: <strong>{temp}</strong></label>
            </div>
            <input
              type="range"
              min="0.0"
              max="1.0"
              step="0.1"
              value={temp}
              onChange={(e) => setTemp(Number(e.target.value))}
              style={{ width: '100%', accentColor: 'var(--accent-secondary)', cursor: 'pointer' }}
              id="input-temperature"
            />
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
          <button className="icon-btn" onClick={onClose} style={{ padding: '10px 16px' }}>
            Cancel
          </button>
          <button className="btn-primary" onClick={handleSave} id="btn-save-settings">
            Apply Settings
          </button>
        </div>
      </div>
    </div>
  );
};
