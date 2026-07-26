import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../context/AuthContext';
import { get_request } from '../Request';

// Trả về màu nền cho ô status bên trái
const getStatusBgClass = (percentage, status) => {
  if (percentage === 100 || status === 'AC') return 'has-background-success has-text-white';
  if (percentage > 0) return 'has-background-warning-dark has-text-white';
  if (status === 'CE' || status === 'AB') return 'has-background-grey-dark has-text-light';
  return 'has-background-grey-light has-text-dark';
};

// Format ngày tháng cho gọn đẹp
const formatDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleString('vi-VN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
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

export default function ContestSubmissions() {
  const [page, setPage] = useState(1);
  const [isBest, setIsBest] = useState(false);
  const { problem_id, contest_id } = useParams();
  const { current_user } = useAuth();

  const username = current_user?.username;

  const { data, isLoading } = useQuery({
    queryKey: ['submissions', { isBest, problem_id, contest_id, username, page }],
    queryFn: () => fetchSubmissions({ is_best: isBest, problem_id, contest_id, username, page }),
    staleTime: 1000 * 10,
    placeholderData: (prev) => prev,
  });

  const list = data?.items || [];
  const totalPages = data?.pages || 1;

  const handleToggleBest = (value) => {
    setIsBest(value);
    setPage(1);
  };

  return (
    <div className="section p-4">
      <div className="container">
        
        {/* Thanh công cụ phía trên: Toggle isBest & Pagination */}
        <div className="level mb-4 is-mobile">
          <div className="level-left">
            <div className="buttons has-addons">
              <button
                className={`button is-small ${!isBest ? 'is-link is-selected' : ''}`}
                onClick={() => handleToggleBest(false)}
              >
                Tất cả bài nộp
              </button>
              <button
                className={`button is-small ${isBest ? 'is-link is-selected' : ''}`}
                onClick={() => handleToggleBest(true)}
              >
                Bài nộp tốt nhất
              </button>
            </div>
          </div>

          {/* Pagination gắn luôn lên header cho tiện thao tác */}
          <div className="level-right">
            {totalPages > 1 && (
              <nav className="pagination is-small" role="navigation">
                <button
                  className="pagination-previous button is-small"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                >
                  &laquo;
                </button>
                <button
                  className="pagination-next button is-small"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                >
                  &raquo;
                </button>
                <ul className="pagination-list">
                  {Array.from({ length: totalPages }, (_, i) => i + 1)
                    .filter((p) => p === 1 || p === totalPages || Math.abs(p - page) <= 1)
                    .map((p, i, arr) => {
                      const prev = arr[i - 1];
                      return (
                        <React.Fragment key={p}>
                          {prev && p - prev > 1 && (
                            <li><span className="pagination-ellipsis">&hellip;</span></li>
                          )}
                          <li>
                            <button
                              className={`pagination-link button is-small ${page === p ? 'is-link' : ''}`}
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
          </div>
        </div>

        {/* Danh sách bài nộp kiểu Row Custom */}
        <div className="box p-0" style={{ overflow: 'hidden' }}>
          {isLoading ? (
            <div className="has-text-centered py-6">
              <span className="icon is-large">
                <i className="fas fa-spinner fa-pulse"></i>
              </span>
              <p className="has-text-grey mt-2">Đang tải bài nộp...</p>
            </div>
          ) : list.length === 0 ? (
            <div className="has-text-centered has-text-grey py-6">Không có bài nộp nào.</div>
          ) : (
            <div className="submission-list">
              {list.map((sub) => (
                <div
                  key={sub.id}
                  className="is-flex is-align-items-center border-bottom py-2 px-3"
                  style={{
                    borderBottom: '1px solid #f0f0f0',
                    minHeight: '70px',
                  }}
                >
                  {/* 1. Khối Status / Điểm / Ngôn ngữ (Bên trái) */}
                  <div
                    className={`has-text-centered p-2 mr-3 is-flex is-flex-direction-column is-justify-content-center ${getStatusBgClass(
                      sub.percentage,
                      sub.status
                    )}`}
                    style={{
                      width: '100px',
                      minWidth: '100px',
                      borderRadius: '6px',
                      height: '56px',
                    }}
                  >
                    <span className="is-size-6 has-text-weight-bold" style={{ lineHeight: '1.1' }}>
                      {sub.percentage !== undefined && sub.percentage !== null ? `${sub.percentage} / 100` : '---'}
                    </span>
                    <span className="is-size-7 mt-1 opacity-80" style={{ fontSize: '0.75rem' }}>
                      {sub.status || 'N/A'} | {sub.language || 'C++'}
                    </span>
                  </div>

                  {/* 2. Thông tin Tên Bài / User / Thời gian (Bên giữa) */}
                  <div className="is-flex-grow-1" style={{ overflow: 'hidden' }}>
                    <div className="is-flex is-align-items-center">
                      <a href={`/problem/${sub.problem?.id}`} className="has-text-link has-text-weight-bold is-size-6 mr-2 truncate">
                        {sub.problem?.name || `Bài tập #${sub.problem?.id || sub.id}`}
                      </a>
                    </div>
                    <div className="is-size-7 has-text-grey mt-1 is-flex is-align-items-center is-flex-wrap-wrap">
                      <strong className="has-text-info mr-1">
                        {sub.user?.username || sub.username || 'Anonymous'}
                      </strong>
                      {sub.contest?.name && (
                        <span className="tag is-warning is-light is-small mr-2 py-0 px-1">
                          [{sub.contest.name}]
                        </span>
                      )}
                      <span>&bull; {formatDate(sub.date_created)}</span>
                    </div>
                  </div>

                  {/* 3. Link thao tác (Xem code, diff...) */}
                  <div className="is-hidden-mobile mr-4 is-size-7">
                    <span className="has-text-grey-light">
                      <a href={`/submission/${sub.id}`} className="has-text-link">view</a> &bull;{' '}
                      <a href={`/submission/${sub.id}/source`} className="has-text-link">source</a> &bull;{' '}
                      <a href={`/submission/${sub.id}/rejudge`} className="has-text-grey">rejudge</a>
                    </span>
                  </div>

                  {/* 4. Thời gian chạy & Bộ nhớ (Bên phải) */}
                  <div className="has-text-right" style={{ minWidth: '90px' }}>
                    <div className="is-size-7 has-text-weight-semibold">
                      {sub.time_used ? `${(sub.time_used / 1000).toFixed(2)}s` : '---'}
                    </div>
                    <div className="is-size-7 has-text-grey">
                      {sub.memory_used ? `${(sub.memory_used / 1024).toFixed(2)} MB` : '---'}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Thêm chút CSS trực tiếp nếu cần */}
        <style>{`
          .truncate {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
          }
          .border-bottom:last-child {
            border-bottom: none !important;
          }
          .opacity-80 {
            opacity: 0.85;
          }
        `}</style>
      </div>
    </div>
  );
}