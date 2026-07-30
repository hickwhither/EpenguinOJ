import React, { useMemo, useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { get_request } from '../Request';
import { formatDateWithLink } from '../dateUtils';
import RegisterContestButton from '../components/contest/ContestRegister';

/* --- HELPERS --- */
function useDebounce(value, delay = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

const formatDate = (value) => {
  if (!value) return '-';
  return formatDateWithLink(value).text;
};

const calculateDuration = (startTime, endTime) => {
  if (!startTime || !endTime) return '-';
  const diffMs = new Date(endTime) - new Date(startTime);
  if (diffMs <= 0) return '0m';
  const totalMinutes = Math.floor(diffMs / (1000 * 60));
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return hours > 0 ? `${hours}h ${minutes > 0 ? `${minutes}m` : ''}` : `${minutes}m`;
};

/* --- API CALLS --- */
const fetchOngoing = async () => (await get_request('/contest/ongoing'))?.data || [];
const fetchUpcoming = async () => (await get_request('/contest/upcoming'))?.data || [];
const fetchEnded = async ({ page, search }) => {
  const params = new URLSearchParams({ page });
  if (search) params.append('search', search);
  const res = await get_request(`/contest/ended?${params.toString()}`);
  return res?.data || { items: [], total: 0, page: 1, pages: 1 };
};

/* --- CONTEST CARD COMPONENT --- */
const ContestCard = ({ contest, type, onViewDetails, onRegisterSuccess }) => {
  return (
    <div className="column is-12-mobile is-6-tablet is-4-desktop is-3-widescreen">
      <div className="box is-flex is-flex-direction-column h-100">
        <h2 className="title is-5 my-auto">{contest.name || `Contest #${contest.id}`}</h2>

        <div className="content is-3 my-2">
          <div><strong>Reg Start:</strong> <a href={formatDateWithLink(contest.registration_start).link} target="_blank" rel="noopener noreferrer">{formatDate(contest.registration_start)}</a></div>
          <div><strong>Reg End:</strong> <a href={formatDateWithLink(contest.registration_end).link} target="_blank" rel="noopener noreferrer">{formatDate(contest.registration_end)}</a></div>
          <div><strong>Start:</strong> <a href={formatDateWithLink(contest.start_time).link} target="_blank" rel="noopener noreferrer">{formatDate(contest.start_time)}</a></div>
          <div><strong>End:</strong> <a href={formatDateWithLink(contest.end_time).link} target="_blank" rel="noopener noreferrer">{formatDate(contest.end_time)}</a></div>
          <div><strong>Duration:</strong> {calculateDuration(contest.start_time, contest.end_time)}</div>
        </div>

        <div className="buttons mt-auto pt-3">
          <button className="button is-link is-fullwidth" onClick={() => onViewDetails(contest.id)}>
            View details
          </button>

          {type !== 'ended' && (
            <RegisterContestButton contest={contest} onSuccess={onRegisterSuccess} />
          )}
        </div>
      </div>
    </div>
  );
};

/* --- MAIN COMPONENT --- */
export default function ContestList() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 500);

  // Queries
  const { data: ongoingList = [], isLoading: loadingOngoing, refetch: refetchOngoing } = useQuery({
    queryKey: ['contests', 'ongoing'],
    queryFn: fetchOngoing,
    staleTime: 1000 * 60,
  });

  const { data: upcomingList = [], isLoading: loadingUpcoming, refetch: refetchUpcoming } = useQuery({
    queryKey: ['contests', 'upcoming'],
    queryFn: fetchUpcoming,
    staleTime: 1000 * 60,
  });

  const { data: endedData, isLoading: loadingEnded } = useQuery({
    queryKey: ['contests', 'ended', { page, search: debouncedSearch }],
    queryFn: () => fetchEnded({ page, search: debouncedSearch }),
    staleTime: 1000 * 60,
    placeholderData: (prev) => prev,
  });

  const endedList = endedData?.items || [];
  const totalPages = endedData?.pages || 1;

  // Callback làm mới danh sách sau khi đăng ký thành công
  const handleRegisterSuccess = () => {
    refetchOngoing();
    refetchUpcoming();
  };

  const handleViewDetails = (id) => navigate(`/c/${id}`);

  const pagesToShow = useMemo(() => {
    return Array.from({ length: Math.max(1, totalPages) }, (_, i) => i + 1);
  }, [totalPages]);

  return (
    <div className="container">
      <h1 className="title">Contests</h1>

      {/* ONGOING CONTESTS */}
      <section className="mb-6">
        <h2 className="title is-4 has-text-danger">Ongoing Contests</h2>
        {loadingOngoing ? (
          <div className="box has-text-centered">Loading...</div>
        ) : ongoingList.length === 0 ? (
          <div className="notification">No ongoing contests at the moment.</div>
        ) : (
          <div className="columns is-multiline">
            {ongoingList.map((c) => (
              <ContestCard
                key={c.id} 
                contest={c}
                type="ongoing"
                onViewDetails={handleViewDetails}
                onRegisterSuccess={handleRegisterSuccess}
              />
            ))}
          </div>
        )}
      </section>

      {/* UPCOMING CONTESTS */}
      <section className="mb-6">
        <h2 className="title is-4 has-text-warning">Upcoming Contests</h2>
        {loadingUpcoming ? (
          <div className="box has-text-centered">Loading...</div>
        ) : upcomingList.length === 0 ? (
          <div className="notification">No upcoming contests scheduled.</div>
        ) : (
          <div className="columns is-multiline">
            {upcomingList.map((c) => (
              <ContestCard
                key={c.id}
                contest={c}
                type="upcoming"
                onViewDetails={handleViewDetails}
                onRegisterSuccess={handleRegisterSuccess}
              />
            ))}
          </div>
        )}
      </section>

      {/* ENDED CONTESTS */}
      <section className="mb-6">
        <h2 className="title is-4 has-text-grey">Past Contests</h2>

        {/* Search / Pagination */}
        <div className="level mb-4">
          <div className="level-left">
            <div className="level-item">
              <input
                className="input"
                type="text"
                placeholder="Search name..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
              />
            </div>
          </div>

          <div className="level-right">
            <nav className="level-item pagination is-centered" role="navigation">
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

        {loadingEnded ? (
          <div className="box has-text-centered">Loading ended contests...</div>
        ) : endedList.length === 0 ? (
          <div className="notification">No ended contests found.</div>
        ) : (
          <div className="columns is-multiline">
            {endedList.map((c) => (
              <ContestCard
                key={c.id}
                contest={c}
                type="ended"
                onViewDetails={handleViewDetails}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}