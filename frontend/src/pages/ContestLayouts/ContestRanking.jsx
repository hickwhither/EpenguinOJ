import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, useOutletContext, Link } from 'react-router-dom';
import { get_request } from '../../Request';
import { HandleDisplay } from '../../components/HandleDisplay';

const RANK_STYLE = {
  1: { color: '#c9a227', fontWeight: 'bold' },
  2: { color: '#9aa0a6', fontWeight: 'bold' },
  3: { color: '#b08d57', fontWeight: 'bold' },
};

export default function ContestRanking() {
  const { contest_id } = useParams();
  const { contest } = useOutletContext();

  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const startTime = contest?.start_time;
  const endTime = contest?.end_time;
  const nowSeconds = now.getTime() / 1000;
  const isRunning = !!(startTime && endTime && nowSeconds >= startTime && nowSeconds <= endTime);

  const { data, isLoading, error } = useQuery({
    queryKey: ['contest-ranking', contest_id],
    queryFn: () => get_request(`/contest/${contest_id}/ranking`).then((res) => res.data),
    enabled: !!contest_id,
    staleTime: 1000 * 5,
    refetchInterval: isRunning ? 10000 : false,
  });

  const problems = data?.problems || [];
  const ranking = data?.ranking || [];

  if (isLoading) {
    return (
      <div className="box has-text-centered">
        <span className="icon is-large"><i className="fas fa-spinner fa-pulse"></i></span>
        <p className="has-text-grey mt-2">Loading ranking...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="notification is-danger is-light">
        {error.response?.data?.detail || error.message || 'Cannot load ranking'}
      </div>
    );
  }

  return (
    <div className="box p-0" style={{ overflowX: 'auto' }}>
      {ranking.length === 0 ? (
        <div className="has-text-centered has-text-grey py-6">No participants yet.</div>
      ) : (
        <table className="table is-fullwidth is-hoverable is-narrow">
          <thead>
            <tr>
              <th style={{ width: '70px' }}>Rank</th>
              <th>User</th>
              {problems.map((p) => (
                <th key={p.id} className="has-text-centered" style={{ minWidth: '70px' }}>
                  <Link to={`/c/${contest_id}/p/${p.id}`} className="has-text-grey">
                    {p.display_order + 1}
                  </Link>
                </th>
              ))}
              <th className="has-text-right">Total</th>
              <th className="has-text-right">Penalty</th>
            </tr>
          </thead>
          <tbody>
            {ranking.map((entry) => (
              <tr key={entry.user.username}>
                <td>
                  <span style={RANK_STYLE[entry.rank] || undefined}>
                    {entry.rank}
                  </span>
                </td>
                <td>
                  <span className="has-text-weight-semibold">
                    <HandleDisplay user={entry.user} />
                  </span>
                  {entry.user.nickname && (
                    <span className="is-size-7 has-text-grey ml-1">({entry.user.nickname})</span>
                  )}
                </td>
                {problems.map((p) => {
                  const res = entry.problem_results?.[String(p.id)];
                  const score = res?.score ?? 0;
                  const max_score = res?.max_score ?? 0;
                  const accepted = res?.accepted;
                  return (
                    <td key={p.id} className="has-text-centered">
                      {max_score > 0 ? (
                        <span className={`tag is-small ${accepted ? 'is-success' : 'is-light'}`}>
                          {score}
                        </span>
                      ) : (
                        <span className="has-text-grey-lighter">-</span>
                      )}
                    </td>
                  );
                })}
                <td className="has-text-right has-text-weight-bold">{entry.total_score}</td>
                <td className="has-text-right">{Math.round(entry.penalty)} min</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
