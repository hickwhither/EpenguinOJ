import React, { useMemo, useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { get_request } from '../Request';
import { useNavigate, useParams } from 'react-router-dom';

/**
 * Custom hook to debounce a value by a specified delay in milliseconds.
 * Prevents making API requests on every single keystroke.
 */
function useDebounce(value, delay = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Fetches paginated and filtered problems from the API endpoint.
 */
const fetchProblems = async ({ page, search, contest_id }) => {
  const params = new URLSearchParams({ page, search, contest_id });
  
  const res = await get_request(`/problems?${params.toString()}`);
  return res?.data || { items: [], pages: 1, total: 0, page: 1, size: 10 };
};

export default function ProblemList() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const {contest_id} = useParams();

  // Debounce search input by 500ms (0.5s)
  const debouncedSearch = useDebounce(search, 500);

  // React Query state management with debounced search value
  const { data, isLoading, isPlaceholderData } = useQuery({
    queryKey: ['problems', { page, search: debouncedSearch, contest_id }],
    queryFn: () => fetchProblems({ page, search: debouncedSearch, contest_id }),
    staleTime: 1000 * 60,
    placeholderData: (prev) => prev,
  });
  
  // Extract items list and total page count from API response
  const problems = data?.items || [];
  const totalPages = data?.pages || 1;

  // Handle search input change and reset to first page
  const onSearchChange = (e) => {
    setSearch(e.target.value);
    setPage(1);
  };

  // Compute pagination range with dynamic ellipsis
  const pagesToShow = useMemo(() => {
    const startCount = 2, endCount = 2, middleCount = 6;
    if (totalPages <= startCount + middleCount + endCount) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    const pagesSet = new Set();
    for (let i = 1; i <= Math.min(startCount, totalPages); i++) pagesSet.add(i);

    const half = Math.floor(middleCount / 2);
    let start = page - half;
    let end = start + middleCount - 1;

    if (start <= startCount) {
      start = startCount + 1;
      end = start + middleCount - 1;
    }
    if (end >= totalPages - endCount + 1) {
      end = totalPages - endCount;
      start = end - middleCount + 1;
    }
    
    for (let i = start; i <= end; i++) pagesSet.add(i);
    for (let i = Math.max(totalPages - endCount + 1, startCount + 1); i <= totalPages; i++) pagesSet.add(i);

    return Array.from(pagesSet).sort((a, b) => a - b);
  }, [totalPages, page]);

  return (
    <>
      <div className="level">
        {/* Search Field */}
        <div className='level-left'>
          <div className="level-item">
            <input className="input" type="text" placeholder="Search name..." value={search} onChange={onSearchChange} />
          </div>
        </div>

        {/* Pagination Controls */}
        <div className='level-right'>
          <nav className="level-item pagination is-centered" role="navigation" aria-label="pagination">
            <button className="pagination-previous" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>
              Previous
            </button>
            <button className="pagination-next" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>
              Next
            </button>
            <ul className="pagination-list">
              {pagesToShow.map((p) => (
                <li key={p}>
                  <button className={`pagination-link ${page === p ? 'is-current' : ''}`} onClick={() => setPage(p)}>
                    {p}
                  </button>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </div>

      {/* Problems Data Table */}
      <table className="table is-hoverable is-fullwidth" width="100%">
        <thead>
          <tr>
            <th width="10%">ID</th>
            <th>Name</th>
            <th width="30%">Authors</th>
          </tr>
        </thead>
        
        <tbody> 
          {isLoading ? (
            <tr><td colSpan={3} style={{ textAlign: 'center' }}>Loading problems…</td></tr>
          ) : problems.length === 0 ? (
            <tr><td colSpan={3} style={{ textAlign: 'center' }}>No problems found</td></tr>
          ) : (
            problems.map((problem) => (
              <tr key={problem.id} style={{ cursor: 'pointer' }}
                onClick={() => navigate(contest_id ? `/c/${contest_id}/p/${problem.id}` : `/p/${problem.id}`)}>
                <td>{problem.id}</td>
                <td>{problem.name}</td>
                <td>
                  {Array.isArray(problem.authors) 
                    ? problem.authors.map(a => (typeof a === 'string' ? a : a.username || a.name)).join(', ')
                    : (problem.authors || '')}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </>
  );
}