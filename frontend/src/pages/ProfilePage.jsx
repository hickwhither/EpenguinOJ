import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { get_request } from '../Request';
import { HandleDisplay } from '../components/HandleDisplay';
import { useAuth } from '../context/AuthContext';
import { formatDate } from '../dateUtils';

const defaultAvatar = "https://bulma.io/assets/images/placeholders/128x128.png";

export default function ProfilePage() {
  const { username } = useParams();
  const { current_user } = useAuth();
  const isOwn = current_user?.username === username;

  const { data: user, isLoading, error } = useQuery({
    queryKey: ['profile', username],
    queryFn: async () => {
      const res = await get_request(`/auth/profile/${username}`);
      if (res.status !== 200) throw new Error(res.data?.detail || 'User not found');
      return res.data;
    },
  });

  const { data: submissions } = useQuery({
    queryKey: ['profile-submissions', username],
    queryFn: async () => {
      const res = await get_request(`/submissions?username=${username}&page=1`);
      return res?.data?.items || (Array.isArray(res?.data) ? res.data : []);
    },
    staleTime: 1000 * 30,
  });

  if (isLoading) return <div className="box has-text-centered py-6">Loading profile...</div>;
  if (error) return <div className="notification is-danger">{error.message}</div>;

  return (
    <div className="container">
      <div className="columns">
        <div className="column is-4">
          <div className="box has-text-centered">
            <figure className="image is-128x128 mx-auto mb-3">
              <img className="is-rounded" src={user?.avatar_url || defaultAvatar} alt={user?.username} />
            </figure>
            <h1 className="title is-4">
              <HandleDisplay user={user} />
            </h1>
            {user?.nickname && <p className="subtitle is-6 has-text-grey">{user.nickname}</p>}
            {user?.bio && <p className="has-text-grey mt-2">{user.bio}</p>}
            <hr />
            <div className="is-flex is-justify-content-space-around">
              <div><strong>Rating</strong><p>{user?.rating ?? '-'}</p></div>
              <div><strong>ELO</strong><p>{user?.elo ?? '-'}</p></div>
              <div><strong>Rank</strong><p>{user?.rank ?? '-'}</p></div>
            </div>
            {isOwn && (
              <Link to="/profile/settings" className="button is-link is-outlined is-fullwidth mt-4">
                Edit Profile
              </Link>
            )}
          </div>
        </div>
        <div className="column is-8">
          <div className="box">
            <h2 className="title is-5">Submissions</h2>
            {!submissions || submissions.length === 0 ? (
              <p className="has-text-grey">No submissions yet.</p>
            ) : (
              <div>
                {submissions.slice(0, 20).map((sub) => (
                  <div key={sub.id} className="is-flex is-align-items-center py-2" style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <span className={`tag ${sub.status === 'D' ? (sub.score > 0 ? 'is-success' : 'is-light') : 'is-info'} mr-2`}>
                      {sub.score ?? '---'}/{sub.max_score ?? '---'}
                    </span>
                    <Link to={`/p/${sub.problem?.id}`} className="has-text-link mr-2">
                      {sub.problem?.name || `Problem #${sub.problem?.id}`}
                    </Link>
                    <span className="has-text-grey is-size-7">{formatDate(sub.date_created)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
