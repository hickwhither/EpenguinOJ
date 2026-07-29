import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'react-router-dom';
import { get_request } from '../Request';

import { useAuth } from '../context/AuthContext';
import { HandleDisplay } from '../components/HandleDisplay';
import SubmitModal from '../components/problem/SubmitModal';
import SubmissionList from './SubmissionList';

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import 'katex/dist/katex.min.css';

const fetchProblem = async (problem_id, contest_id) => {
  const params = new URLSearchParams();
  if (problem_id) params.append('problem_id', problem_id);
  if (contest_id) params.append('contest_id', contest_id);

  // GET /problem?problem_id=...&contest_id=...
  const res = await get_request(`/problem?${params.toString()}`);
  return res.data;
};

export default function ProblemDisplay() {
  const { problem_id, contest_id } = useParams();
  const { current_user, loginRequired } = useAuth();
  
  // Modals State
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [submissionList, setSubmissionList] = useState({isOpen:false});
  const openSubmissionList = (mode) => {
    if(mode=='status') return setSubmissionList(({isOpen: true, title:'Submissions'}) );
    if(mode=='my-submissions') return setSubmissionList(({isOpen: true, title:'My Submissions', username:current_user.username }) );
    if(mode=='leaderboard') return setSubmissionList(({isOpen: true, title: 'Leaderboard', is_best:true }) );
  }
  const closeSubmissionList = () => setSubmissionList(prev => ({ ...prev, isOpen: false }));

  const { data: p = {}, isLoading, error } = useQuery({
    queryKey: ['problem', problem_id, contest_id],
    queryFn: () => fetchProblem(problem_id, contest_id),
    enabled: !!problem_id,
    staleTime: 1000 * 60,
  });

  // Loading & Error states
  if (isLoading) {
    return (
      <div className="box has-text-centered">
        <p className="has-text-grey">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="notification is-danger is-light">
        {error.response?.data?.detail || error.message || "Cannot load problem"}
      </div>
    );
  }

  if(!p){
    return <div className='box'>no problem</div>
  }

  return (
    <div className="columns">
      {/* Left column: Function buttons and problem infos */}
      <div className="column is-one-fifth">
        <div className="buttons is-centered">
          <button 
            onClick={() => loginRequired(() => setIsSubmitModalOpen(true))} 
            className="button is-primary is-fullwidth"
          >
            Submit
          </button>
          <button 
            onClick={() => openSubmissionList('status')} 
            className="button is-info" 
            title='All submissions'
          >
            <i className="fa-solid fa-signal"/>
          </button>
          <button 
            onClick={() => openSubmissionList('my-submissions')} 
            className="button is-info" 
            title='My submissions'
          >
            <i className="fa-solid fa-user-circle"/>
          </button>
          <button 
            onClick={() => openSubmissionList('leaderboard')} 
            className="button is-link" 
            title='Leaderboard'
          >
            <i className="fa-solid fa-crown"/>
          </button>
        </div>
        
        <div className="box">
          <p><strong>Time limit:</strong> {p.time_limit ? `${p.time_limit} ms` : 'N/A'}</p>
          <p><strong>Memory limit:</strong> {p.memory_limit ? `${(p.memory_limit / 1024).toFixed(1)} MB` : 'N/A'}</p>
          <p><strong>Input:</strong> {p.input || 'stdin'}</p>
          <p><strong>Output:</strong> {p.output || 'stdout'}</p>
          
          {p.authors && p.authors.length > 0 && (
            <div>
              <strong>{p.authors.length > 1 ? 'Authors' : 'Author'}: </strong>
              {p.authors.map((a, index) => (
                <React.Fragment key={a.id || index}>
                  {HandleDisplay(a)}
                  {index < p.authors.length - 1 && ', '}
                </React.Fragment>
              ))}
            </div>
          )}
        </div>
      </div>
      
      {/* Right column: Problem title and statement */}
      <div className="column">
        <h1 className="title">
          {p.name || ``}{' '}
          <span className="has-text-grey-light">({p.id || problem_id})</span>
        </h1>
        <hr />
        
        {/* Render Markdown + LaTeX */}
        <div className="content">
          <ReactMarkdown
            remarkPlugins={[remarkGfm, remarkMath]}
            rehypePlugins={[rehypeKatex]}
          >
            {p.statement || 'No statement'}
          </ReactMarkdown>
        </div>
      </div>

      {/* Modals */}
      <SubmitModal 
        isOpen={isSubmitModalOpen}
        onClose={() => setIsSubmitModalOpen(false)}
        problem_id={p.id || problem_id}
        problem_name={p.name}
        contest_id={contest_id}
      />
      
      <SubmissionList 
        isOpen={submissionList.isOpen}
        onClose={closeSubmissionList}
        title={submissionList.title}
        problem_id={p.id || problem_id}
        contest_id={contest_id}
        username={current_user?.username || ""}
      />
    </div>
  );
}