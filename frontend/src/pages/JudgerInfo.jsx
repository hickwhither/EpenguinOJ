import { useQuery } from '@tanstack/react-query'
import { get_request } from '../Request'

function formatDate(value) {
  if (!value) return 'Chưa từng kết nối'
  return new Date(value).toLocaleString()
}

export default function JudgerInfo() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['judgers'],
    queryFn: async () => {
      const res = await get_request('/judgers')
      if (res.status >= 400) throw new Error(res.data?.detail || 'Không tải được thông tin judger')
      return res.data
    },
    refetchInterval: 5000,
  })

  const judgers = data || []

  return (
    <div className="container">
      <div className="level">
        <div className="level-left">
          <div>
            <h1 className="title">Judgers</h1>
            <p className="subtitle">Thông tin kết nối và trạng thái hiện tại của các máy chấm.</p>
          </div>
        </div>
      </div>

      {isLoading && <div className="notification is-info is-light">Đang tải danh sách judger...</div>}
      {isError && <div className="notification is-danger is-light">Không thể tải thông tin judger.</div>}

      {!isLoading && !isError && judgers.length === 0 && (
        <div className="notification is-warning is-light">Chưa có judger nào kết nối.</div>
      )}

      {!isLoading && !isError && judgers.length > 0 && (
        <div className="table-container">
          <table className="table is-fullwidth is-striped is-hoverable">
            <thead>
              <tr>
                <th>Tên</th>
                <th>Trạng thái</th>
                <th>Kết nối WS</th>
                <th>Bài đang chấm</th>
                <th>Tin nhắn</th>
                <th>Lần cuối hoạt động</th>
              </tr>
            </thead>
            <tbody>
              {judgers.map((judger) => (
                <tr key={judger.name}>
                  <td><strong>{judger.name}</strong></td>
                  <td>
                    <span className={`tag ${judger.status === 'online' ? 'is-success' : 'is-light'}`}>
                      {judger.status}
                    </span>
                  </td>
                  <td>{judger.connected ? 'Có' : 'Không'}</td>
                  <td>{judger.current_submission_id || 'Rảnh'}</td>
                  <td>{judger.message || '-'}</td>
                  <td>{formatDate(judger.last_seen)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
