import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, useNavigate, useLocation, Outlet } from 'react-router-dom';
import { get_request } from '../Request';
import RegisterContestButton from '../components/contest/ContestRegister';

const fetchContest = async (contest_id) => {
  const res = await get_request(`/contest/${contest_id}`);
  if (res.status !== 200) throw new Error(res.data?.detail || 'Cannot load contest');
  return res.data;
};

export default function ContestLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { contest_id } = useParams();

  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const { data: contest, isLoading, error, refetch } = useQuery({
    queryKey: ['contest', contest_id],
    queryFn: () => fetchContest(contest_id),
    staleTime: 1000 * 60,
  });

  if (isLoading) return <div className="box">Loading contest…</div>;
  if (error) return <div className="box has-text-danger">{error.message}</div>;

  const startTime = contest?.start_time ? new Date(contest.start_time * 1000) : null;
  const endTime = contest?.end_time ? new Date(contest.end_time * 1000) : null;
  const getProgressValue = () => {
    if (!startTime || !endTime) return 0;
    const current = now.getTime();
    const start = startTime.getTime();
    const end = endTime.getTime();
    if (current < start) return 0;
    if (current > end) return 100;
    const total = end - start;
    const elapsed = current - start;
    if (total <= 0) return 100;
    return Math.min(100, Math.max(0, (elapsed / total) * 100));
  };
  const progressPercent = getProgressValue();

  const isTabActive = (path) => {
    if (path === 'ranking') return location.pathname === `/c/${contest_id}/ranking`;
    if (path === 'submissions') return location.pathname.startsWith(`/c/${contest_id}/s`)
    return location.pathname.startsWith(`/c/${contest_id}/${path}`);
  };

  return (
    <>
      <h1 className="title">{contest.name}</h1>

      {/* Progress Bar tự động nhảy theo thời gian */}
      <div className="block">
        <progress className="progress is-primary" value={progressPercent} max="100">
          {progressPercent.toFixed(1)}%
        </progress>
      </div>

      {/* Navigation Tabs */}
      <div className="tabs is-boxed">
        <ul>
          <li>
            <RegisterContestButton contest={contest} onSuccess={refetch} />
          </li>
          <li className={isTabActive('info') ? 'is-active' : ''}>
            <a onClick={() => navigate(`/c/${contest_id}`)}>
              <span className="icon is-small"><i className="fa-solid fa-circle-info" /></span>
              Info
            </a>
          </li>
          <li className={isTabActive('ranking') ? 'is-active' : ''}>
            <a onClick={() => navigate(`/c/${contest_id}/ranking`)}>
              <span className="icon is-small"><i className="fa-solid fa-ranking-star" /></span>
              Ranking
            </a>
          </li>
          <li className={isTabActive('submissions') ? 'is-active' : ''}>
            <a onClick={() => navigate(`/c/${contest_id}/s`)}>
              <span className="icon is-small"><i className="fa-solid fa-square-poll-horizontal" /></span>
              Submissions
            </a>
          </li>
        </ul>
      </div>

      {/* Nội dung chi tiết của trang con sẽ render ở đây */}
      <Outlet context={{ contest, refetch }} />
    </>
  );
}