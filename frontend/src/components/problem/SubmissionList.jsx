import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { get_request } from '../../Request';

const getStatusTagClass = (percentage, status) => {
  if (percentage === 100 || status === 'AC') return 'is-success';
  if (percentage > 0) return 'is-warning';
  return 'is-danger';
};

const fetchSubmissions = async ({ is_best, problem_id, contest_id, username, page }) => {
  const params = new URLSearchParams({ is_best, problem_id, contest_id, username, page });
  const res = await get_request(`/submissions?${params.toString()}`);
  const responseData = res?.data || res;
  return {
    items: responseData?.items || (Array.isArray(responseData) ? responseData : []),
    pages: responseData?.pages || 1,
    size: responseData?.size || 50,
    total: responseData?.total || 0,
  };
};

export default function SubmissionList({ isOpen, onClose, title, is_best=false, problem_id, contest_id, username }) {
  const [page, setPage] = useState(1);

  useEffect(() => {
    if (isOpen) {
      setPage(1);
    }
  }, [isOpen, title, is_best, problem_id, contest_id]);

  const { data, isLoading } = useQuery({
    queryKey: ['submissions', { is_best, problem_id, contest_id, username, page }],
    queryFn: () => fetchSubmissions({ is_best, problem_id, contest_id, username, page }),
    staleTime: 1000 * 10,
    enabled: isOpen && !!problem_id,
    placeholderData: (prev) => prev,
  });

  const list = data?.items || [];
  const totalPages = data?.pages || 1;
  const pageSize = data?.size || 50;

  return (
    <div className={`modal ${isOpen ? "is-active" : ""}`}>
      <div className="modal-background" onClick={onClose}></div>
      <div className="modal-content" style={{ width: '85%', maxWidth: '1000px' }}>
        <div className="box">
          <div className="is-flex is-justify-content-space-between is-align-items-center mb-4">
            <h2 className="title is-4 mb-0">{title}</h2>
            {data?.total > 0 && (
              <span className="tag is-info is-light">Tổng cộng: {data.total} bài nộp</span>
            )}
          </div>

          {isLoading ? (
            <div className="has-text-centered py-5">Loading dữ liệu...</div>
          ) : list.length === 0 ? (
            <div className="has-text-centered has-text-grey py-5">Chưa có bài nộp nào.</div>
          ) : (
            <>
              <div className="table-container">
                <table className="table is-fullwidth is-striped is-hoverable">
                  {list.map((sub, index) => (
                    <tr key={sub.id}>
                      {is_best && (
                        <td>
                          <strong>{(page - 1) * pageSize + index + 1}</strong>
                        </td>
                      )}
                      <td>#{sub.id}</td>
                      <td>{sub.user?.username || sub.username || 'N/A'}</td>
                      <td><span className="tag is-white">{sub.language}</span></td>
                      <td>
                        <span className={`tag is-bold ${getStatusTagClass(sub.percentage, sub.status)}`}>
                          {sub.percentage ?? 0}% {sub.status ? `(${sub.status})` : ''}
                        </span>
                      </td>
                      <td>{sub.time_used ?? 0} ms</td>
                      <td>{sub.memory_used ? (sub.memory_used / 1024).toFixed(2) : 0} MB</td>
                    </tr>
                  ))}
                </table>
              </div>

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <nav className="pagination is-centered is-small mt-4" role="navigation" aria-label="pagination">
                  <button 
                    className="pagination-previous"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page <= 1}
                  >
                    Previous
                  </button>
                  <button 
                    className="pagination-next"
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                  >
                    Next
                  </button>

                  <ul className="pagination-list">
                    {Array.from({ length: totalPages }, (_, i) => i + 1)
                      .filter(p => p === 1 || p === totalPages || Math.abs(p - page) <= 1)
                      .map((p, i, arr) => {
                        const prev = arr[i - 1];
                        return (
                          <React.Fragment key={p}>
                            {prev && p - prev > 1 && (
                              <li><span className="pagination-ellipsis">&hellip;</span></li>
                            )}
                            <li>
                              <button
                                className={`pagination-link ${page === p ? 'is-current' : ''}`}
                                onClick={() => setPage(p)}
                              >
                                {p}
                              </button>
                            </li>
                          </React.Fragment>
                        );
                      })}
                  </ul>
                </nav>
              )}
            </>
          )}
        </div>
      </div>
      <button className="modal-close is-large" aria-label="close" onClick={onClose}></button>
    </div>
  );
}