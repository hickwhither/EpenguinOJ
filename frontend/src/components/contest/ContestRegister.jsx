import React, { useState } from 'react';
import { toast } from 'react-toastify';
import { post_request } from '../../Request'; // Kiểm tra lại đường dẫn file Request.js

export default function RegisterContestButton({ contest, onSuccess }) {
  const [isOpen, setIsOpen] = useState(false);
  const [password, setPassword] = useState('');
  const [registering, setRegistering] = useState(false);

  const now = new Date();
  const regStart = contest?.registration_start ? new Date(contest.registration_start) : null;
  const regEnd = contest?.registration_end ? new Date(contest.registration_end) : null;

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
        toast.success('Đăng ký contest thành công!');
        setIsOpen(false);
        setPassword('');
        if (onSuccess) onSuccess();
      } else {
        toast.error(res?.data?.detail || res?.data?.message || 'Cannot register this contest');
      }
    } catch (error) {
      toast.error('Có lỗi xảy ra khi đăng ký!');
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
        Đăng ký ngay
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
                    placeholder="Bỏ trống nếu không có"
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
                Hủy
              </button>
              <button type="submit" className={`button is-primary ${registering ? 'is-loading' : ''}`} disabled={registering}>
                Confirm đăng ký
              </button>
            </footer>
          </form>
        </div>
      </div>
    </>
  );
}