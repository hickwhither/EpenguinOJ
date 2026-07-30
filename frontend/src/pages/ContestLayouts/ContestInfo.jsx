import { useOutletContext } from 'react-router-dom';

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import 'katex/dist/katex.min.css';
import { formatDateWithLink } from '../../dateUtils';

function preprocessMath(text) {
  if (!text) return '';
  return text.replace(/(?<!~)~(?!~)(.*?)(?<!~)~(?!~)/g, '$$$1$$');
}

export default function ContestInfo() {
  const { contest } = useOutletContext();
  const rawDescription = contest?.description || 'No description';
  const processedDescription = preprocessMath(rawDescription);

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