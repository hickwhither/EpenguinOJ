import { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { post_request, get_request } from '../Request';
import { AuthContext } from './AuthContext'; // Import context từ file trên

export const AuthProvider = ({ children }) => {
  const [current_user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isLoginModalActive, setIsLoginModalActive] = useState(false);

  useEffect(() => {
    const fetchProfile = async () => {
      const res = await get_request('/auth/profile');
      if (res.status === 200) setUser(res.data);
      setLoading(false);
    };
    fetchProfile();
  }, []);

  const login = async (form) => {
    const res = await post_request('/auth/signin', form);
    if (res.status !== 200) {
      toast.error(res.data?.detail || 'Đăng nhập thất bại');
      return false;
    }
    toast.success('Đăng nhập thành công!');
    setUser(res.data);
    setIsLoginModalActive(false);
    return true;
  };

  const logout = async () => {
    await post_request('/auth/signout');
    setUser(null);
    toast.info('Đã đăng xuất');
  };

  const loginRequired = (callback) => {
    if (current_user) callback();
    else setIsLoginModalActive(true);
  };

  return (
    <AuthContext.Provider
      value={{
        current_user,
        loading,
        isLoginModalActive,
        setIsLoginModalActive,
        login,
        logout,
        loginRequired,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};