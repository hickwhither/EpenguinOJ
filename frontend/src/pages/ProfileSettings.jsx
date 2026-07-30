import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { useAuth } from '../context/AuthContext';
import { get_request, post_request } from '../Request';

const defaultAvatar = "https://bulma.io/assets/images/placeholders/128x128.png";

export default function ProfileSettings() {
  const { current_user, loading: authLoading, refreshProfile } = useAuth();
  const navigate = useNavigate();
  const [nickname, setNickname] = useState('');
  const [bio, setBio] = useState('');
  const [avatarUrl, setAvatarUrl] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (authLoading) return;
    if (!current_user) {
      navigate('/');
      return;
    }
    const fetchProfile = async () => {
      const res = await get_request('/auth/profile');
      if (res.status === 200) {
        setNickname(res.data?.nickname || '');
        setBio(res.data?.bio || '');
        setAvatarUrl(res.data?.avatar_url || '');
      }
    };
    fetchProfile();
  }, [current_user, authLoading, navigate]);

  const handleSave = async () => {
    setSaving(true);
    const res = await post_request('/auth/profile', { nickname, bio, avatar_url: avatarUrl }, { method: 'PATCH' });
    setSaving(false);
    if (res.status !== 200) {
      toast.error(res.data?.detail || 'Failed to update profile');
      return;
    }
    toast.success('Profile updated!');
    await refreshProfile();
  };

  if (authLoading) return <div className="box has-text-centered py-6">Loading...</div>;

  return (
    <div className="container">
      <div className="columns is-centered">
        <div className="column is-6">
          <div className="box">
            <h1 className="title is-4">Profile Settings</h1>
            <div className="field">
              <label className="label">Username</label>
              <input className="input" type="text" value={current_user?.username || ''} disabled />
            </div>
            <div className="field">
              <label className="label">Nickname</label>
              <input className="input" type="text" value={nickname} onChange={(e) => setNickname(e.target.value)} placeholder="Display name" />
            </div>
            <div className="field">
              <label className="label">Bio</label>
              <textarea className="textarea" value={bio} onChange={(e) => setBio(e.target.value)} placeholder="Tell us about yourself" rows={4} />
            </div>
            <div className="field">
              <label className="label">Avatar URL</label>
              <div className="is-flex is-align-items-center">
                <figure className="image is-48x48 mr-3">
                  <img className="is-rounded" src={avatarUrl || defaultAvatar} alt="" />
                </figure>
                <input className="input" type="text" value={avatarUrl} onChange={(e) => setAvatarUrl(e.target.value)} placeholder="https://..." />
              </div>
            </div>
            <div className="field is-grouped mt-5">
              <div className="control">
                <button className={`button is-link ${saving ? 'is-loading' : ''}`} onClick={handleSave} disabled={saving}>
                  Save Changes
                </button>
              </div>
              <div className="control">
                <button className="button is-light" onClick={() => navigate(`/profile/${current_user?.username}`)}>Cancel</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
