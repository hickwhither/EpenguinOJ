import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { get_request, post_request } from '../Request';
import { toast } from 'react-toastify';

const fetchContest = async (contest_id) => {
  const res = await get_request(`/contest/${contest_id}`);
  if (res.status !== 200) throw new Error(res.data?.detail || 'Cannot load contest');
  return res.data;
};

const formatDate = (value) => (value ? new Date(value).toLocaleString() : '-');

export default function ContestDisplay() {
  const { contest_id } = useParams();
  const [password, setPassword] = useState('');
  const [registering, setRegistering] = useState(false);

  const { data: contest, isLoading, error, refetch } = useQuery({
    queryKey: ['contest', contest_id],
    queryFn: () => fetchContest(contest_id),
    staleTime: 1000 * 60 * 5,
  });

  const register = async (e) => {
    e.preventDefault();
    setRegistering(true);
    const res = await post_request(`/contest/${contest_id}/register`, { password });
    setRegistering(false);

    if (res.status === 200) {
      toast.success('Đăng ký contest thành công!');
      refetch(); // Tải lại data để cập nhật is_registered và problems
    } else {
      toast.error(res.data?.detail || 'Không thể đăng ký contest');
    }
  };

  if (isLoading) return <div className="box">Loading contest…</div>;
  if (error) return <div className="box has-text-danger">{error.message}</div>;

  return (
    <div className="columns">
      {/* Cột thông tin Contest */}
      <div className="column is-one-quarter">
        <div className="box">
          <h2 className="title is-5">{contest.name}</h2>
          <p><strong>ID / Code:</strong> {contest.id}</p>
          <hr />
          
          <p className="heading text-uppercase has-text-weight-bold">Thời gian cuộc thi</p>
          <p><strong>Start:</strong> {formatDate(contest.start_time)}</p>
          <p><strong>End:</strong> {formatDate(contest.end_time)}</p>
          
          {contest.registration_start && contest.registration_end ?
          <p className="heading text-uppercase has-text-weight-bold mt-3">Registration time</p> : '' }
          {contest.registration_start ? <p><strong>Registration open:</strong> {formatDate(contest.registration_start)}</p> : ''}
          {contest.registration_end ? <p><strong>Registration close:</strong> {formatDate(contest.registration_end)}</p> : ''}
          
          <hr />

          {/* Kiểm tra trạng thái is_registered */}
          {contest.is_registered ? (
            <div className="notification is-success is-light has-text-centered py-2">
              <strong>✓ Đã đăng ký</strong>
            </div>
          ) : (
            <form onSubmit={register}>
              <label className="label">Mật khẩu contest</label>
              <input
                className="input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Bỏ trống nếu không có"
                disabled={registering}
              />
              <button
                type="submit"
                className={`button is-primary is-fullwidth mt-3 ${registering ? 'is-loading' : ''}`}
                disabled={registering}
              >
                Đăng ký ngay
              </button>
            </form>
          )}
        </div>
      </div>

      {/* Cột Nội dung & Bài tập */}
      <div className="column">
        <h1 className="title">{contest.name}</h1>
        <div className="content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {contest.description || '*Không có mô tả*'}
          </ReactMarkdown>
        </div>

        <h2 className="title is-4 mt-5">Danh sách bài tập</h2>
        <div className="box">
          {contest.problems === null ? (
            <div className="notification is-warning is-light">
              Bạn cần đăng ký hoặc chờ đến giờ contest bắt đầu để xem danh sách bài tập.
            </div>
          ) : contest.problems && contest.problems.length > 0 ? (
            <table className="table is-hoverable is-fullwidth">
              <thead>
                <tr>
                  <th style={{ width: '80px' }}>ID</th>
                  <th>Tên bài tập</th>
                </tr>
              </thead>
              <tbody>
                {contest.problems.map((problem) => (
                  <tr key={problem.id}>
                    <td>
                      <Link to={`/c/${contest.id}/${problem.id}`}>
                        {problem.id}
                      </Link>
                    </td>
                    <td>{problem.name}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="has-text-grey">Contest hiện chưa có bài tập nào.</p>
          )}
        </div>
      </div>
    </div>
  );
}