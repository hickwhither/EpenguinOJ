import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { get_request } from '../../Request';
import { formatDateWithLink } from '../../dateUtils';

const STATUS_LABEL = { QW: 'Queued', C: 'Compiling', P: 'Processing', D: 'Done' };

const VERDICT_LABEL = {
  AC: 'Accepted', OK: 'Accepted', PAC: 'Partially Accepted',
  WA: 'Wrong Answer', TLE: 'Time Limit Exceeded', MLE: 'Memory Limit Exceeded',
  OLE: 'Output Limit Exceeded', IR: 'Invalid Return', RTE: 'Runtime Error',
  CE: 'Compile Error', IE: 'Internal Error', SC: 'Short-circuited', AB: 'Aborted',
};

const VERDICT_COLOR = {
  AC: 'is-success', OK: 'is-success', PAC: 'is-warning',
  WA: 'is-danger', TLE: 'is-warning', MLE: 'is-danger', OLE: 'is-warning',
  IR: 'is-danger', RTE: 'is-danger', CE: 'is-danger', IE: 'is-danger',
  SC: 'is-grey', AB: 'is-grey',
};

const fmtTime = (ms) => (ms ? `${(ms / 1000).toFixed(2)}s` : '---');
const fmtMem = (kb) => (kb ? `${(kb / 1024).toFixed(2)} MB` : '---');

const statusColor = (score, status) => {
  if (status === 'D' && score > 0) return 'is-success';
  if (status === 'D') return 'is-light';
  if (status === 'C' || status === 'P') return 'is-info';
  return 'is-light';
};

export default function SubmissionModal({ submissionId, onClose }) {
  const [activeTab, setActiveTab] = useState('result');
  const [live, setLive] = useState(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['submission', submissionId],
    queryFn: () => get_request(`/submission/${submissionId}`).then((res) => res.data),
    enabled: !!submissionId,
    staleTime: 1000 * 60,
  });

  const status = live?.status ?? data?.status;
  const isActive = status === 'C' || status === 'P';

  useEffect(() => {
    if (!submissionId || !isActive) return;
    const evtSource = new EventSource(`/api/submission/${submissionId}/stream`);
    evtSource.onmessage = (e) => {
      const d = JSON.parse(e.data);
      setLive(d);
      if (d.status === 'D') evtSource.close();
    };
    evtSource.onerror = () => evtSource.close();
    return () => evtSource.close();
  }, [submissionId, isActive]);

  if (!submissionId) return null;

  const sub = data ? { ...data, ...live } : null;
  const date = sub?.date_created ? formatDateWithLink(sub.date_created) : null;

  return (
    <div className="modal is-active">
      <div className="modal-background" onClick={onClose}></div>
      <div className="modal-content" style={{ width: '85%', maxWidth: '1000px' }}>
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
                          {date && <span> &bull; <a href={date.link} target="_blank" rel="noopener noreferrer">{date.text}</a></span>}
                        </p>
                      </div>
                    </div>
                    <div className="level-right">
                      <span className={`tag is-medium ${statusColor(sub.score, status)}`}>
                        {sub.score} / {sub.max_score}
                      </span>
                    </div>
                  </div>

                  <div className="columns is-multiline is-size-7 mb-3">
                    <div className="column is-2"><strong>Status:</strong> {STATUS_LABEL[status] || status}</div>
                    <div className="column is-2"><strong>Time:</strong> {fmtTime(sub.time_used)}</div>
                    <div className="column is-2"><strong>Memory:</strong> {fmtMem(sub.memory_used)}</div>
                    <div className="column is-2"><strong>Language:</strong> {sub.language || 'C++'}</div>
                    {sub.judger_name && <div className="column is-2"><strong>Judge:</strong> {sub.judger_name}</div>}
                  </div>

                  {sub.error && (
                    <div className="notification is-warning is-light">{sub.error}</div>
                  )}

                  {sub.results?.length > 0 ? (
                    sub.results.map((group, gi) => (
                      <div key={gi} className="mb-4">
                        <div className="is-flex is-align-items-center is-justify-content-space-between mb-2">
                          <div className="is-flex is-align-items-center">
                            <span className="has-text-weight-semibold mr-2">Subtask {group.subtask ?? '—'}</span>
                            <span className={`tag ${VERDICT_COLOR[group.verdict] || 'is-light'} is-small`}>
                              {VERDICT_LABEL[group.verdict] || group.verdict || '—'}
                            </span>
                          </div>
                          <span className="is-size-7 has-text-grey">
                            {fmtTime(group.time_used)} &bull; {fmtMem(group.memory_used)}
                          </span>
                        </div>
                        {group.test_cases?.length > 0 ? (
                          <table className="table is-fullwidth is-narrow is-hoverable is-size-7">
                            <thead>
                              <tr><th>#</th><th>Verdict</th><th>Time</th><th>Memory</th><th>Feedback</th></tr>
                            </thead>
                            <tbody>
                              {group.test_cases.map((tc, ti) => (
                                <tr key={ti}>
                                  <td>{ti + 1}</td>
                                  <td>
                                    <span className={`tag ${VERDICT_COLOR[tc.verdict] || 'is-light'} is-small`}>
                                      {VERDICT_LABEL[tc.verdict] || tc.verdict}
                                    </span>
                                  </td>
                                  <td>{fmtTime(tc.time_used)}</td>
                                  <td>{fmtMem(tc.memory_used)}</td>
                                  <td className="has-text-grey">{tc.feedback || ''}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        ) : (
                          group.feedback && <p className="help has-text-grey">{group.feedback}</p>
                        )}
                      </div>
                    ))
                  ) : status === 'C' || status === 'P' ? (
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
                    {sub.source || 'No source code available.'}
                  </pre>
                </>
              )}
            </>
          )}
        </div>
      </div>
      <button className="modal-close is-large" aria-label="close" onClick={onClose}></button>
    </div>
  );
}
