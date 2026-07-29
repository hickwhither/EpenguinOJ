import { useAuth } from '../../context/AuthContext';
const defaultAvatar = "https://bulma.io/assets/images/placeholders/128x128.png";

export default function AuthButton() {
    const { current_user, loading, logout, setIsLoginModalActive: setIsLoginModalActive } = useAuth();

    if (loading) return <></>;

    if (current_user) return (
        <div className="dropdown is-hoverable is-right">
            <div className="dropdown-trigger">
                <button className="button is-ghost" aria-haspopup="true" aria-controls="dropdown-menu">
                    <figure className="image media-left">
                        <img 
                            className="is-rounded" 
                            src={current_user?.avatar_url || defaultAvatar} 
                            alt={current_user?.username || "User"} 
                        />
                    </figure>
                </button>
            </div>
            <div className="dropdown-menu" id="dropdown-menu" role="menu">
                <div className="dropdown-content">
                    <hr className="dropdown-divider" />
                    <a href="#logout" className="dropdown-item has-text-danger" onClick={(e) => { e.preventDefault(); logout(); }}>
                        Sign out
                    </a>
                </div>
            </div>
        </div>
    );

    return (
        <button className="button is-success is-outlined" onClick={() => setIsLoginModalActive(true)}>
            <strong>Sign in</strong>
        </button>
    );
}