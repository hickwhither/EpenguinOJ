import React, { useState } from 'react';
import { toast } from 'react-toastify';
import { post_request } from '../../Request'; // Kiểm tra lại đường dẫn file Request.js

export default function RegisterContestButton({ contest, onSuccess }) {
  const [isOpen, setIsOpen] = useState(false);
  const [password, setPassword] = useState('');
  const [registering, setRegistering] = useState(false);

  const now = Math.floor(Date.now() / 1000);
  const regStart = contest?.registration_start;
  const regEnd = contest?.registration_end;

  if (contest?.is_registered) {
    return (
      <button className="button is-success is-outlined is-fullwidth" disabled>
        <span className="icon is-small me-1">
          <i className="fa-solid fa-check" />
        </span>
        <span>Registered</span>
      </button>
    );
  }

  if (regStart && now < regStart) {
    return (
      <button className="button is-static is-fullwidth" disabled>
        Registration Upcoming
      </button>
    );
  }

  if (regEnd && now > regEnd) {
    return (
      <button className="button is-static is-fullwidth" disabled>
        Registration Ended
      </button>
    );
  }

  const handleRegister = async (e) => {
    e.preventDefault();
    setRegistering(true);

    try {
      const res = await post_request(`/contest/${contest.id}/register`, { password });

      if (res?.status === 200 || res?.data?.success) {
        toast.success('Contest registration successful!');
        setIsOpen(false);
        setPassword('');
        if (onSuccess) onSuccess();
      } else {
        toast.error(res?.data?.detail || res?.data?.message || 'Cannot register this contest');
      }
    } catch (error) {
      toast.error('An error occurred during registration!');
      console.error(error);
    } finally {
      setRegistering(false);
    }
  };

  return (
    <>
      <button
        type="button"
        className="button is-primary is-fullwidth"
        onClick={() => setIsOpen(true)}
      >
        Register now
      </button>

      {/* Bulma Modal Popup */}
      <div className={`modal ${isOpen ? 'is-active' : ''}`}>
        <div className="modal-background" onClick={() => !registering && setIsOpen(false)} />

        <div className="modal-card">
          <header className="modal-card-head">
            <p className="modal-card-title">Register {contest.name || `Contest #${contest.id}`}</p>
            <button
              type="button"
              className="delete"
              aria-label="close"
              onClick={() => setIsOpen(false)}
              disabled={registering}
            />
          </header>

          <form onSubmit={handleRegister}>
            <section className="modal-card-body">
              <div className="field">
                <label className="label">Password contest</label>
                <div className="control">
                  <input
                    className="input"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Leave blank if none"
                    disabled={registering}
                    autoFocus
                  />
                </div>
              </div>
            </section>

            <footer className="modal-card-foot is-justify-content-flex-end">
              <button
                type="button"
                className="button"
                onClick={() => setIsOpen(false)}
                disabled={registering}
              >
                Cancel
              </button>
              <button type="submit" className={`button is-primary ${registering ? 'is-loading' : ''}`} disabled={registering}>
                Confirm registration
              </button>
            </footer>
          </form>
        </div>
      </div>
    </>
  );
}