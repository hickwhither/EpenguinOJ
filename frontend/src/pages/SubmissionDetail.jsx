import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { get_request } from '../Request';
import { formatDateWithLink } from '../dateUtils';
import { useAuth } from '../context/AuthContext';

const STATUS_LABEL = {
  QW: 'Queued', C: 'Compiling', P: 'Processing',
};

const VERDICT_LABEL = {
  AC: 'Accepted', PAC: 'Partially Accepted',
  WA: 'Wrong Answer', TLE: 'Time Limit Exceeded', MLE: 'Memory Limit Exceeded',
  OLE: 'Output Limit Exceeded', IR: 'Invalid Return', RTE: 'Runtime Error',
  CE: 'Compile Error', IE: 'Internal Error', SC: 'Short-circuited', AB: 'Aborted',
};

const VERDICT_COLOR = {
  AC: 'is-success',
  PAC: 'is-warning',
  WA: 'is-danger', TLE: 'is-warning', MLE: 'is-danger', OLE: 'is-warning',
  IR: 'is-danger', RTE: 'is-danger', CE: 'is-danger', IE: 'is-danger',
  SC: 'is-grey', AB: 'is-grey',
};

const fmtTime = (s) => (s !== null && s !== undefined ? `${s.toFixed(3)}s` : '---');
const fmtMem = (kb) => (kb ? `${(kb / 1024).toFixed(3)} MB` : '---');

const statusColor = (status) => {
  if (status === 'AC') return 'is-success';
  if (status === 'QW' || status === 'C' || status === 'P') return 'is-info';
  if (VERDICT_COLOR[status]) return VERDICT_COLOR[status];
  return 'is-light';
};

export default function SubmissionDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('result');
  const { current_user } = useAuth();

  const { data, isLoading, error } = useQuery({
    queryKey: ['submission', id],
    queryFn: () => get_request(`/submission/${id}`).then((res) => res.data),
    enabled: !!id,
    staleTime: 1000 * 60,
    refetchInterval: 5000,
  });

  const sub = data;
  const status = sub?.status;
  const isOwner = !!sub && sub.user?.id === current_user?.id;

  if (!id) return null;

  const date = sub?.date_created ? formatDateWithLink(sub.date_created) : null;

  return (
    <div className="section p-4">
      <div className="container">
        <div className="mb-3">
          <button type="button" className="button is-small is-ghost has-text-link" onClick={() => navigate(-1)}>
            <span className="icon is-small"><i className="fa-solid fa-arrow-left" /></span>
            <span>Back</span>
          </button>
        </div>

        <div className="box">
          {isLoading && !data && (
            <div className="has-text-centered py-6">
              <span className="icon is-large"><i className="fas fa-spinner fa-pulse"></i></span>
              <p className="has-text-grey mt-2">Loading submission...</p>
            </div>
          )}

          {error && (
            <div className="notification is-danger is-light">
              {error.response?.status === 403
                ? 'You can only view your own submissions.'
                : error.response?.data?.detail || error.message || 'Cannot load submission'}
            </div>
          )}

          {sub && (
            <>
              <h2 className="title is-4 mb-3">Submission #{sub.id}</h2>

              <div className="tabs is-boxed mb-4">
                <ul>
                  <li className={activeTab === 'result' ? 'is-active' : ''}>
                    <a onClick={() => setActiveTab('result')}>
                      <span className="icon is-small"><i className="fa-solid fa-list-check" /></span>
                      <span>Result</span>
                    </a>
                  </li>
                  <li className={activeTab === 'source' ? 'is-active' : ''}>
                    <a onClick={() => setActiveTab('source')}>
                      <span className="icon is-small"><i className="fa-solid fa-code" /></span>
                      <span>Source</span>
                    </a>
                  </li>
                </ul>
              </div>

              {activeTab === 'result' ? (
                <>
                  <div className="level is-mobile mb-3">
                    <div className="level-left">
                      <div>
                        <p className="title is-5 mb-1">
                          {sub.problem?.name ? `${sub.problem.name} (${sub.problem.id})` : `Problem #${sub.problem?.id || sub.id}`}
                        </p>
                        <p className="is-size-7 has-text-grey">
                          {sub.user?.username || 'Anonymous'}
                          {sub.contest_registration?.contest?.name && (
                            <span className="tag is-warning is-light is-small ml-2">
                              [{sub.contest_registration.contest.name}]
                            </span>
                          )}
                          {date && <span> &bull; <a href={date.link} target="_blank" rel="noopener noreferrer">{date.text}</a></span>}
                        </p>
                      </div>
                    </div>
                    <div className="level-right">
                      <span className={`tag is-medium ${statusColor(status)}`}>
                        {STATUS_LABEL[status] || VERDICT_LABEL[status] || status || '---'}
                      </span>
                    </div>
                  </div>

                  <div className="columns is-multiline is-size-7 mb-3">
                    <div className="column is-2"><strong>Status:</strong> {STATUS_LABEL[status] || VERDICT_LABEL[status] || status}</div>
                    <div className="column is-2"><strong>Time:</strong> {fmtTime(sub.time)}</div>
                    <div className="column is-2"><strong>Memory:</strong> {fmtMem(sub.memory)}</div>
                    <div className="column is-2"><strong>Language:</strong> {sub.language || 'C++'}</div>
                    {sub.judger_name && <div className="column is-2"><strong>Judge:</strong> {sub.judger_name}</div>}
                  </div>

                  {sub.error && (
                    <div className="notification is-warning is-light">{sub.error}</div>
                  )}

                  {sub.results?.length > 0 ? (
                    <table className="table is-fullwidth is-narrow is-hoverable is-size-7">
                      <thead>
                        <tr><th>Group</th><th>Status</th><th>Time</th><th>Memory</th><th>Feedback</th></tr>
                      </thead>
                      <tbody>
                        {sub.results.map((g, gi) => (
                          <tr key={gi}>
                            <td>{g.group || '—'}</td>
                            <td>
                              <span className={`tag ${VERDICT_COLOR[g.status] || 'is-light'} is-small`}>
                                {VERDICT_LABEL[g.status] || g.status || '—'}
                              </span>
                            </td>
                            <td>{fmtTime(g.time)}</td>
                            <td>{fmtMem(g.memory)}</td>
                            <td className="has-text-grey">{g.feedback || ''}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : status === 'C' || status === 'P' || status === 'QW' ? (
                    <div className="has-text-centered py-6">
                      <span className="icon is-large"><i className="fas fa-spinner fa-pulse"></i></span>
                      <p className="has-text-grey mt-2">Judging...</p>
                    </div>
                  ) : (
                    <div className="has-text-centered has-text-grey py-6">No results.</div>
                  )}
                </>
              ) : (
                <>
                  <div className="is-flex is-align-items-center mb-2">
                    <span className="tag is-info is-light mr-2">{sub.language || 'C++'}</span>
                    <span className="is-size-7 has-text-grey">Source code</span>
                  </div>
                  <pre style={{ maxHeight: '60vh', overflow: 'auto', fontSize: '0.85rem' }}>
                    {isOwner
                      ? sub.source || 'No source code available.'
                      : 'Source code is only visible to the submission owner.'}
                  </pre>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
