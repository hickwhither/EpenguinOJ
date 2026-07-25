import React, { useMemo, useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { get_request, post_request } from '../Request';

/* --- HELPERS --- */
function useDebounce(value, delay = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

const formatDate = (value) => (value ? new Date(value).toLocaleString() : '-');

const calculateDuration = (startTime, endTime) => {
  if (!startTime || !endTime) return '-';
  const diffMs = new Date(endTime) - new Date(startTime);
  if (diffMs <= 0) return '0m';
  const totalMinutes = Math.floor(diffMs / (1000 * 60));
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return hours > 0 ? `${hours}h ${minutes > 0 ? `${minutes}m` : ''}` : `${minutes}m`;
};

// Tính toán trạng thái và nhãn nút đăng ký
const getRegistrationStatus = (contest, now) => {
  if (contest.is_registered) {
    return { label: 'Registered', canRegister: false, isRegistered: true };
  }
  const regStart = contest.registration_start ? new Date(contest.registration_start) : null;
  const regEnd = contest.registration_end ? new Date(contest.registration_end) : null;

  if (regStart && now < regStart) return { label: 'Registration Upcoming', canRegister: false };
  if (regEnd && now > regEnd) return { label: 'Registration Ended', canRegister: false };
  return { label: 'Register', canRegister: true };
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

/* --- REUSABLE CONTEST CARD COMPONENT --- */
const ContestCard = ({ contest, type, onRegister, onViewDetails }) => {
  const now = new Date();
  const tagMap = {
    ongoing: { label: 'Live', class: 'is-danger' },
    upcoming: { label: 'Upcoming', class: 'is-warning' },
    ended: { label: 'Ended', class: 'is-dark' },
  };

  const regStatus = type !== 'ended' ? getRegistrationStatus(contest, now) : null;

  return (
    <div className="column is-12-mobile is-6-tablet is-4-desktop">
      <div className="box is-flex is-flex-direction-column h-100">
        <div className="content">
          <span className={`tag ${tagMap[type].class}`}>{tagMap[type].label}</span>
          <h2 className="title is-5 mt-2 mb-0">{contest.name || `Contest #${contest.id}`}</h2>
        </div>

        <div className="content is-small my-2">
          <div><strong>Reg Start:</strong> {formatDate(contest.registration_start)}</div>
          <div><strong>Reg End:</strong> {formatDate(contest.registration_end)}</div>
          <div><strong>Start:</strong> {formatDate(contest.start_time)}</div>
          <div><strong>End:</strong> {formatDate(contest.end_time)}</div>
          <div><strong>Duration:</strong> {calculateDuration(contest.start_time, contest.end_time)}</div>
        </div>

        <div className="buttons mt-auto pt-3">
          <button className="button is-link is-fullwidth" onClick={() => onViewDetails(contest.id)}>
            View details
          </button>

          {type !== 'ended' && (
            <button
              className={`button is-fullwidth ${regStatus?.isRegistered ? 'is-success is-outlined' : 'is-success'}`}
              onClick={() => onRegister(contest.id)}
              disabled={!regStatus?.canRegister}
            >
              {regStatus?.label}
            </button>
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

  // Actions
  const handleRegister = async (contestId) => {
    try {
      await post_request(`/contest/${contestId}/register`);
      refetchOngoing();
      refetchUpcoming();
    } catch (error) {
      console.error('Failed to register:', error);
    }
  };

  const handleViewDetails = (id) => navigate(`/c/${id}`);

  const pagesToShow = useMemo(() => {
    return Array.from({ length: Math.max(1, totalPages) }, (_, i) => i + 1);
  }, [totalPages]);

  return (
    <div className="container">
      <h1 className="title">Contests</h1>

      {/* 1. ONGOING CONTESTS */}
      <section className="mb-6">
        <h2 className="title is-4 has-text-danger">Ongoing Contests</h2>
        {loadingOngoing ? (
          <div className="box has-text-centered">Loading...</div>
        ) : ongoingList.length === 0 ? (
          <div className="notification is-light">No ongoing contests at the moment.</div>
        ) : (
          <div className="columns is-multiline">
            {ongoingList.map((c) => (
              <ContestCard key={c.id} contest={c} type="ongoing" onRegister={handleRegister} onViewDetails={handleViewDetails} />
            ))}
          </div>
        )}
      </section>

      {/* 2. UPCOMING CONTESTS */}
      <section className="mb-6">
        <h2 className="title is-4 has-text-warning-dark">Upcoming Contests</h2>
        {loadingUpcoming ? (
          <div className="box has-text-centered">Loading...</div>
        ) : upcomingList.length === 0 ? (
          <div className="notification is-light">No upcoming contests scheduled.</div>
        ) : (
          <div className="columns is-multiline">
            {upcomingList.map((c) => (
              <ContestCard key={c.id} contest={c} type="upcoming" onRegister={handleRegister} onViewDetails={handleViewDetails} />
            ))}
          </div>
        )}
      </section>

      {/* 3. ENDED CONTESTS (Với Search & Pagination) */}
      <section className="mb-6">
        <h2 className="title is-4 has-text-grey">Past Contests</h2>

        {/* Controls Header: Search + Pagination chỉ phục vụ Ended Contests */}
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
          <div className="notification is-light">No ended contests found.</div>
        ) : (
          <div className="columns is-multiline">
            {endedList.map((c) => (
              <ContestCard key={c.id} contest={c} type="ended" onViewDetails={handleViewDetails} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}