import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { post_request } from '../Request';
import { toast } from 'react-toastify';

export default function DiscordConfirm() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const mounted = useRef(true);

  // FIX 1: Explicitly set mounted.current to true on mount for React 18 Strict Mode
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);

  const action = searchParams.get('type') || ''; // 'create_account', 'change_password', 'quick_login'
  const secret = searchParams.get('secret') || '';

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const [isCheckingToken, setIsCheckingToken] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [formErrors, setFormErrors] = useState({
    username: '',
    email: '',
    password: '',
  });

  // Wrapped in useCallback so we can safely call it inside useEffect
  const handleQuickLogin = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await post_request('/confirm/quick-login', { secret });
      if (!mounted.current) return;

      if (res && res.status >= 200 && res.status < 300) {
        toast.success("Login successful!");
        navigate('/', { replace: true });
      } else {
        toast.error(res?.data?.detail || "Quick login failed.");
        navigate('/', { replace: true });
      }
    } catch {
      if (!mounted.current) return;
      toast.error("A network error occurred during quick login.");
      navigate('/', { replace: true });
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, [secret, navigate]);

  useEffect(() => {
    if (!action || !secret) {
      toast.error("Confirmation link is missing required parameters.");
      navigate('/', { replace: true });
      return;
    }

    const validateTokenAndProceed = async () => {
      setIsCheckingToken(true);
      try {
        const checkRes = await post_request('/confirm/check', { secret });
        if (!mounted.current) return;

        if (!checkRes || checkRes.status < 200 || checkRes.status >= 300) {
          const errorMsg = checkRes?.data?.detail || "Invalid or expired token.";
          toast.error(errorMsg);
          navigate('/', { replace: true });
          return;
        }

        setIsCheckingToken(false);

        if (action === 'quick_login') {
          handleQuickLogin();
        }
      } catch {
        // FIX 2: Catch network errors so the screen doesn't get stuck
        if (!mounted.current) return;
        toast.error("Failed to verify confirmation link. Please try again.");
        navigate('/', { replace: true });
      }
    };

    validateTokenAndProceed();
    // FIX 3: Added missing dependencies
  }, [action, secret, navigate, handleQuickLogin]); 

  const validateForm = () => {
    let isValid = true;
    const errors = { username: '', email: '', password: '' };
    
    if (action === 'create_account') {
      const usernameRegex = /^[a-zA-Z_]+$/;
      if (!username.trim()) {
        errors.username = 'Username is required.';
        isValid = false;
      } else if (!usernameRegex.test(username)) {
        errors.username = 'Username can only contain letters (A-Z, a-z) and underscores (_).';
        isValid = false;
      }

      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!email.trim()) {
        errors.email = 'Email is required.';
        isValid = false;
      } else if (!emailRegex.test(email)) {
        errors.email = 'Please enter a valid email address.';
        isValid = false;
      }
    }

    if (action === 'create_account' || action === 'change_password') {
      if (!password) {
        errors.password = 'Password is required.';
        isValid = false;
      } else if (password.length < 6) {
        errors.password = 'Password must be at least 6 characters.';
        isValid = false;
      }
    }

    setFormErrors(errors);
    return isValid;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) return;

    setLoading(true);

    let endpoint;
    let payload;

    if (action === 'create_account') {
      endpoint = '/confirm/create-account';
      payload = { secret, username, email, password };
    } else if (action === 'change_password') {
      endpoint = '/confirm/reset-password';
      payload = { secret, password };
    } else {
      toast.error("Invalid action.");
      navigate('/', { replace: true });
      return;
    }

    try {
      const res = await post_request(endpoint, payload);
      if (!mounted.current) return;

      if (res && res.status >= 200 && res.status < 300) {
        toast.success(
          action === 'create_account'
            ? "Account created successfully!"
            : "Password updated successfully!"
        );
        navigate('/', { replace: true });
      } else {
        const errorMsg = res?.data?.detail || "Action failed.";

        if (res?.status === 401 || res?.status === 408) {
          toast.error(errorMsg);
          navigate('/', { replace: true });
        } else {
          if (errorMsg === 'confirm.exist_username') {
            setFormErrors((prev) => ({ ...prev, username: 'Username is already taken.' }));
          } else if (errorMsg === 'confirm.exist_email') {
            setFormErrors((prev) => ({ ...prev, email: 'Email address is already registered.' }));
          } else if (errorMsg === 'confirm.exist_discord_id') {
            setError('This Discord account is already linked to another user.');
          } else {
            setError(errorMsg);
          }
        }
      }
    } catch {
      if (!mounted.current) return;
      setError("A network error occurred. Please try again.");
    } finally {
      if (mounted.current) setLoading(false);
    }
  };

  if (isCheckingToken) {
    return (
      <div className="container section has-text-centered py-6">
        <span className="icon is-large has-text-info mb-2">
          <i className="fas fa-spinner fa-pulse fa-2x"></i>
        </span>
        <p className="subtitle">Verifying confirmation details...</p>
      </div>
    );
  }

  return (
    <div className="container section" style={{ maxWidth: '500px' }}>
      <div className="box">
        <h1 className="title has-text-centered is-size-4">
          {action === 'create_account' && (
            <>
              <i className="fas fa-user-plus mr-2"></i> Create Discord Account
            </>
          )}
          {action === 'change_password' && (
            <>
              <i className="fas fa-key mr-2"></i> Reset Password
            </>
          )}
          {action === 'quick_login' && (
            <>
              <i className="fas fa-bolt mr-2"></i> Quick Login
            </>
          )}
        </h1>

        {error && (
          <div className="notification is-danger is-light">
            <button className="delete" onClick={() => setError(null)}></button>
            {error}
          </div>
        )}

        {action === 'quick_login' ? (
          <div className="has-text-centered py-5">
            <span className="icon is-large has-text-primary mb-3">
              <i className="fas fa-circle-notch fa-spin fa-2x"></i>
            </span>
            <p className="subtitle">Processing login...</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} noValidate>
            {action === 'create_account' && (
              <>
                {/* Username Input */}
                <div className="field">
                  <label className="label">Username</label>
                  <div className="control has-icons-left">
                    <input
                      className={`input ${formErrors.username ? 'is-danger' : ''}`}
                      type="text"
                      placeholder="e.g. john_doe"
                      value={username}
                      onChange={(e) => {
                        setUsername(e.target.value);
                        if (formErrors.username) setFormErrors({ ...formErrors, username: '' });
                      }}
                      required
                    />
                    <span className="icon is-small is-left">
                      <i className="fas fa-user"></i>
                    </span>
                  </div>
                  {formErrors.username ? (
                    <p className="help is-danger">{formErrors.username}</p>
                  ) : (
                    <p className="help is-hint">Only letters (A-Z, a-z) and underscores (_)</p>
                  )}
                </div>

                {/* Email Input */}
                <div className="field">
                  <label className="label">Email</label>
                  <div className="control has-icons-left">
                    <input
                      className={`input ${formErrors.email ? 'is-danger' : ''}`}
                      type="email"
                      placeholder="example@gmail.com"
                      value={email}
                      onChange={(e) => {
                        setEmail(e.target.value);
                        if (formErrors.email) setFormErrors({ ...formErrors, email: '' });
                      }}
                      required
                    />
                    <span className="icon is-small is-left">
                      <i className="fas fa-envelope"></i>
                    </span>
                  </div>
                  {formErrors.email && (
                    <p className="help is-danger">{formErrors.email}</p>
                  )}
                </div>
              </>
            )}

            {/* Password Input */}
            {(action === 'create_account' || action === 'change_password') && (
              <div className="field">
                <label className="label">
                  {action === 'change_password' ? 'New Password' : 'Password'}
                </label>
                <div className="control has-icons-left">
                  <input
                    className={`input ${formErrors.password ? 'is-danger' : ''}`}
                    type="password"
                    placeholder="Enter password..."
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (formErrors.password) setFormErrors({ ...formErrors, password: '' });
                    }}
                    required
                  />
                  <span className="icon is-small is-left">
                    <i className="fas fa-lock"></i>
                  </span>
                </div>
                {formErrors.password && (
                  <p className="help is-danger">{formErrors.password}</p>
                )}
              </div>
            )}

            {/* Submit Button */}
            <div className="field mt-5">
              <button
                type="submit"
                className={`button is-primary is-fullwidth ${loading ? 'is-loading' : ''}`}
                disabled={loading}
              >
                <span className="icon">
                  <i className={action === 'create_account' ? 'fas fa-check' : 'fas fa-save'}></i>
                </span>
                <span>
                  {action === 'create_account' ? 'Register & Sign In' : 'Update Password'}
                </span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}