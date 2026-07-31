import { useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';

export default function RequireAuth({ children }) {
  const { current_user, loading, setIsLoginModalActive } = useAuth();

  useEffect(() => {
    if (!loading && !current_user) setIsLoginModalActive(true);
  }, [current_user, loading, setIsLoginModalActive]);

  if (loading) {
    return <div className="box has-text-centered">Checking login status...</div>;
  }

  if (!current_user) {
    return (
      <div className="box has-text-centered">
        <p className="title is-5">Please log in to view this content.</p>
        <button className="button is-primary" onClick={() => setIsLoginModalActive(true)}>
          Sign in
        </button>
      </div>
    );
  }

  return children;
}
