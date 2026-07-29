import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';

export default function LoginModal() {
    const { isLoginModalActive, setIsLoginModalActive, login } = useAuth();
    const [form, setForm] = useState({ username: '', password: '' });
    const [errors, setErrors] = useState({ username: '', general: '' });
    const [isLoading, setIsLoading] = useState(false);

    const usernameRegex = /^[a-zA-Z_]+$/;
    
    const validateUsername = (value) => {
        if (!value) {
            return 'Username cannot be empty';
        }
        if (!usernameRegex.test(value)) {
            return 'Username can only include letters (A-Z, a-z) and underscore (_)';
        }
        return '';
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setForm((prev) => ({ ...prev, [name]: value }));
        if (name === 'username') {
            const errorMsg = validateUsername(value);
            setErrors((prev) => ({ ...prev, username: errorMsg }));
        }
    };

    const handleClose = () => {
        setForm({ username: '', password: '' });
        setErrors({ username: '', general: '' });
        setIsLoginModalActive(false);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        const usernameError = validateUsername(form.username);
        if (usernameError) {
            setErrors((prev) => ({ ...prev, username: usernameError }));
            return;
        }

        setIsLoading(true);
        setErrors((prev) => ({ ...prev, general: '' }));

        try {
            const success = await login(form);
            if (success) {
                handleClose();
            } else {
                setErrors((prev) => ({ ...prev, general: 'Username or password incorrect' }));
            }
        } catch (err) {
            setErrors((prev) => ({ ...prev, general: `An error occurred. Please try again ${err}` }));
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={`modal ${isLoginModalActive ? "is-active" : ""}`}>
            <div className="modal-background" onClick={handleClose}></div>
            <div className="modal-card">
                <header className="modal-card-head">
                    <p className="modal-card-title">Sign in</p>
                    <button 
                        type="button" 
                        className="delete" 
                        aria-label="close" 
                        onClick={handleClose}
                    ></button>
                </header>

                <form onSubmit={handleSubmit}>
                    <section className="modal-card-body">
                        {/* Field Username */}
                        <div className="field">
                            <label className="label">Username</label>
                            <div className="control has-icons-left has-icons-right">
                                <input
                                    className={`input ${errors.username ? 'is-danger' : ''}`}
                                    type="text"
                                    name="username"
                                    value={form.username}
                                    onChange={handleChange}
                                    placeholder="Username"
                                    required
                                />
                                <span className="icon is-small is-left">
                                    <i className="fa-solid fa-user"></i>
                                </span>
                                {errors.username && (
                                    <span className="icon is-small is-right has-text-danger">
                                        <i className="fa-solid fa-exclamation-triangle"></i>
                                    </span>
                                )}
                            </div>

                            <div style={{ minHeight: '24px', marginTop: '0.25rem' }}>
                                {errors.username && (
                                    <p className="help is-danger mt-0">{errors.username}</p>
                                )}
                            </div>
                        </div>

                        {/* Field Password */}
                        <div className="field">
                            <label className="label">Password</label>
                            <div className="control has-icons-left">
                                <input
                                    className="input"
                                    type="password"
                                    name="password"
                                    value={form.password}
                                    onChange={handleChange}
                                    placeholder="Password"
                                    required
                                />
                                <span className="icon is-small is-left">
                                    <i className="fa-solid fa-lock"></i>
                                </span>
                            </div>
                            {/* Khung giữ nhịp cho đều với ô trên */}
                            <div style={{ minHeight: '12px' }}></div>
                        </div>
                        
                        <div style={{ minHeight: '48px', marginBottom: '0.75rem' }}>
                            {errors.general && (
                                <div className="notification is-danger is-light py-2 px-4 mb-0">
                                    {errors.general}
                                </div>
                            )}
                        </div>
                    </section>

                    <footer className="modal-card-foot">
                        <button 
                            type="submit" 
                            className={`button is-success ${isLoading ? 'is-loading' : ''}`}
                            disabled={!!errors.username || isLoading}
                        >
                            Sign in
                        </button>
                        <button 
                            type="button" 
                            className="button" 
                            onClick={handleClose}
                        >
                            Cancel
                        </button>
                    </footer>
                </form>
            </div>
        </div>
    );
}