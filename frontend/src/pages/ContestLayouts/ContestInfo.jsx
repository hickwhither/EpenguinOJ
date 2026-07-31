import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import 'katex/dist/katex.min.css';
import { formatDateWithLink } from '../../dateUtils';
import RegisterContestButton from '../../components/contest/ContestRegister';
import ProblemList from '../ProblemList';

function preprocessMath(text) {
  if (!text) return '';
  return text.replace(/(?<!~)~(?!~)(.*?)(?<!~)~(?!~)/g, '$$$1$$');
}

export default function ContestInfo() {
  const { contest, refetch } = useOutletContext();
  const rawDescription = contest?.description || 'No description';
  const processedDescription = preprocessMath(rawDescription);

  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const startTime = contest?.start_time ? new Date(contest.start_time * 1000) : null;
  const endTime = contest?.end_time ? new Date(contest.end_time * 1000) : null;
  const isStarted = !startTime || now >= startTime;
  const isEnded = !endTime || now > endTime;
  const isRegistered = !!contest?.is_registered;

  return (
    <>
      <div className="box mb-4">
        <div className="columns is-size-7 has-text-grey">
          <div className="column">
            <strong>Reg Start:</strong> <a href={formatDateWithLink(contest.registration_start).link} target="_blank" rel="noopener noreferrer">{formatDateWithLink(contest.registration_start).text}</a>
          </div>
          <div className="column">
            <strong>Reg End:</strong> <a href={formatDateWithLink(contest.registration_end).link} target="_blank" rel="noopener noreferrer">{formatDateWithLink(contest.registration_end).text}</a>
          </div>
          <div className="column">
            <strong>Start:</strong> <a href={formatDateWithLink(contest.start_time).link} target="_blank" rel="noopener noreferrer">{formatDateWithLink(contest.start_time).text}</a>
          </div>
          <div className="column">
            <strong>End:</strong> <a href={formatDateWithLink(contest.end_time).link} target="_blank" rel="noopener noreferrer">{formatDateWithLink(contest.end_time).text}</a>
          </div>
        </div>
      </div>

      <div className="box">
        {!isStarted ? (
          <div className="has-text-centered has-text-grey py-6">
            <p className="is-size-6">Problems are hidden until the contest starts.</p>
          </div>
        ) : !isRegistered && !isEnded ? (
          <div className="has-text-centered py-6">
            <p className="is-size-6 mb-4">Register to view the contest problems.</p>
            <div className="is-inline-block" style={{ width: '220px' }}>
              <RegisterContestButton contest={contest} onSuccess={refetch} />
            </div>
          </div>
        ) : (
          <ProblemList contest_id={contest.id} />
        )}
      </div>

      <div className="content">
        <ReactMarkdown
          remarkPlugins={[remarkGfm, remarkMath]}
          rehypePlugins={[rehypeKatex]}
        >
          {processedDescription}
        </ReactMarkdown>
      </div>
    </>
  );
}
