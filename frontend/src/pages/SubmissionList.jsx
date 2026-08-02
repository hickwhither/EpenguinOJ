import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { get_request } from '../Request';
import { formatDateWithLink } from '../dateUtils';

const VERDICT_LABEL = {
  AC: 'Accepted', PAC: 'Partially Accepted', WA: 'Wrong Answer',
  TLE: 'Time Limit Exceeded', MLE: 'Memory Limit Exceeded', OLE: 'Output Limit Exceeded',
  IR: 'Invalid Return', RTE: 'Runtime Error', CE: 'Compile Error', IE: 'Internal Error',
  SC: 'Short-circuited', AB: 'Aborted',
};

const STATUS_LABEL = { QW: 'Queued', C: 'Compiling', P: 'Processing', ...VERDICT_LABEL };

const getStatusBgClass = (status) => {
  if (status === 'AC') return 'has-background-success has-text-white';
  if (status === 'QW' || status === 'C' || status === 'P') return 'has-background-info has-text-white';
  if (['WA', 'MLE', 'RTE', 'CE', 'IE'].includes(status)) return 'has-background-danger has-text-white';
  if (['PAC', 'TLE', 'OLE', 'IR'].includes(status)) return 'has-background-warning has-text-dark';
  return 'has-background-grey-light has-text-dark';
};

const fetchSubmissions = async ({ is_best, problem_id, contest_id, username, page }) => {
  const params = new URLSearchParams({ is_best, page });
  if (problem_id) params.append('problem_id', problem_id);
  if (contest_id) params.append('contest_id', contest_id);
  if (username) params.append('username', username);

  const res = await get_request(`/submissions?${params.toString()}`);
  const responseData = res?.data || res;

  return {
    items: responseData?.items || (Array.isArray(responseData) ? responseData : []),
    pages: responseData?.pages || 1,
    size: responseData?.size || 50,
    total: responseData?.total || 0,
  };
};

function SubmissionRow({ sub, onView }) {
  const status = sub.status;
  return (
    <div className="is-flex is-align-items-center border-bottom py-2 px-3"
      style={{ borderBottom: '1px solid #f0f0f0', minHeight: '70px' }}>
      <div className={`has-text-centered p-2 mr-3 is-flex is-flex-direction-column is-justify-content-center ${getStatusBgClass(status)}`}
        style={{ width: '100px', minWidth: '100px', borderRadius: '6px', height: '56px' }}>
        <span className="is-size-6 has-text-weight-bold" style={{ lineHeight: '1.1' }}>
          {status || '---'}
        </span>
        <span className="is-size-7 mt-1 opacity-80" style={{ fontSize: '0.75rem' }}>
          {STATUS_LABEL[status] || 'Unknown'} | {sub.language || 'C++'}
        </span>
      </div>
      <div className="is-flex-grow-1" style={{ overflow: 'hidden' }}>
        <div className="is-flex is-align-items-center">
          <a href={`/problem/${sub.problem?.id}`} className="has-text-link has-text-weight-bold is-size-6 mr-2 truncate">
            {sub.problem?.name || `Problem #${sub.problem?.id || sub.id}`}
          </a>
        </div>
        <div className="is-size-7 has-text-grey mt-1 is-flex is-align-items-center is-flex-wrap-wrap">
          <strong className="has-text-info mr-1">
            {sub.user?.username || sub.username || 'Anonymous'}
          </strong>
          {sub.contest_registration?.contest?.name && (
            <span className="tag is-warning is-light is-small mr-2 py-0 px-1">
              [{sub.contest_registration.contest.name}]
            </span>
          )}
          <span>&bull; <a href={formatDateWithLink(sub.date_created).link} target="_blank" rel="noopener noreferrer">{formatDateWithLink(sub.date_created).text}</a></span>
        </div>
      </div>
      <div className="is-hidden-mobile mr-4 is-size-7">
        <button type="button" className="button is-small is-ghost has-text-link" onClick={() => onView(sub.id)}>view</button>
      </div>
      <div className="has-text-right" style={{ minWidth: '90px' }}>
        <div className="is-size-7 has-text-weight-semibold">
          {sub.time ? `${sub.time.toFixed(2)}s` : '---'}
        </div>
        <div className="is-size-7 has-text-grey">
          {sub.memory ? `${(sub.memory / 1024).toFixed(2)} MB` : '---'}
        </div>
      </div>
    </div>
  );
}

export default function SubmissionList({
  problem_id: propProblemId, contest_id: propContestId,
  is_best: propIsBest,
}) {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [isBest, setIsBest] = useState(propIsBest ?? false);
  const [usernameFilter, setUsernameFilter] = useState('');
  const [debouncedUsername, setDebouncedUsername] = useState('');
  const { problem_id: paramProblemId, contest_id: paramContestId } = useParams();
  const { current_user } = useAuth();

  const problem_id = propProblemId || paramProblemId;
  const contest_id = propContestId || paramContestId;
  const username = debouncedUsername || undefined;

  useEffect(() => {
    const t = setTimeout(() => setDebouncedUsername(usernameFilter.trim()), 300);
    return () => clearTimeout(t);
  }, [usernameFilter]);

  const { data, isLoading } = useQuery({
    queryKey: ['submissions', { isBest, problem_id, contest_id, username, page }],
    queryFn: () => fetchSubmissions({ is_best: isBest, problem_id, contest_id, username, page }),
    staleTime: 1000 * 10,
    refetchInterval: 5000,
    placeholderData: (prev) => prev,
  });

  const list = data?.items || [];
  const totalPages = data?.pages || 1;

  const filterKey = `${debouncedUsername}`;
  const [prevFilterKey, setPrevFilterKey] = useState(filterKey);
  if (filterKey !== prevFilterKey) {
    setPrevFilterKey(filterKey);
    setPage(1);
  }

  const handleToggleBest = (value) => {
    setIsBest(value);
    setPage(1);
  };

  return (
    <div className="section p-4">
      <div className="container">
        <div className="level mb-4 is-mobile">
          <div className="level-left">
            <div className="buttons has-addons">
              <button className={`button is-small ${!isBest ? 'is-link is-selected' : ''}`}
                onClick={() => handleToggleBest(false)}>All submissions</button>
              <button className={`button is-small ${isBest ? 'is-link is-selected' : ''}`}
                onClick={() => handleToggleBest(true)}>Best submissions</button>
            </div>
          </div>
          <div className="level-right">
            {data?.total > 0 && <span className="tag is-info is-light mr-2">Total: {data.total} submissions</span>}
            {totalPages > 1 && (
              <nav className="pagination is-small" role="navigation">
                <button className="pagination-previous button is-small"
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page <= 1}>&laquo;</button>
                <button className="pagination-next button is-small"
                  onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}>&raquo;</button>
              </nav>
            )}
          </div>
        </div>

        <div className="field has-addons mb-4">
          <div className="control has-icons-left is-expanded">
            <input
              className="input is-small"
              type="text"
              placeholder="Filter by username"
              value={usernameFilter}
              onChange={(e) => setUsernameFilter(e.target.value)}
            />
            <span className="icon is-small is-left">
              <i className="fa-solid fa-user"></i>
            </span>
          </div>
          <div className="control">
            <button className="button is-small" onClick={() => setUsernameFilter(current_user?.username || '')}>
              Only me
            </button>
          </div>
          {usernameFilter && (
            <div className="control">
              <button className="button is-small" onClick={() => setUsernameFilter('')} aria-label="Clear username filter">
                <i className="fa-solid fa-xmark"></i>
              </button>
            </div>
          )}
        </div>

        <div className="box p-0" style={{ overflow: 'hidden' }}>
          {isLoading ? (
            <div className="has-text-centered py-6">
              <span className="icon is-large"><i className="fas fa-spinner fa-pulse"></i></span>
              <p className="has-text-grey mt-2">Loading submissions...</p>
            </div>
          ) : list.length === 0 ? (
            <div className="has-text-centered has-text-grey py-6">No submissions.</div>
          ) : (
            <div className="submission-list">
              {list.map((sub) => (
                <SubmissionRow key={sub.id} sub={sub} onView={(id) => navigate(`/submission/${id}`)} />
              ))}
            </div>
          )}
        </div>

        <style>{`
          .truncate { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
          .border-bottom:last-child { border-bottom: none !important; }
          .opacity-80 { opacity: 0.85; }
        `}</style>
      </div>
    </div>
  );
}
