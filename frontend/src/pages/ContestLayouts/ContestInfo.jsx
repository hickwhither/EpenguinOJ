import React from 'react';
import { useParams, useOutletContext } from 'react-router-dom';

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import 'katex/dist/katex.min.css';

function preprocessMath(text) {
  if (!text) return '';
  // Regex này tìm dấu ~ đơn (không phải ~~), bọc quanh nội dung, chuyển thành $...$
  return text.replace(/(?<!~)~(?!~)(.*?)(?<!~)~(?!~)/g, '$$$1$$');
}

export default function ContestInfo() {
  const { contest_id } = useParams();
  const { contest } = useOutletContext();
  const rawDescription = contest?.description || 'No description';
  const processedDescription = preprocessMath(rawDescription);

  return (
    <div className="content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[rehypeKatex]}
      >
        {processedDescription}
      </ReactMarkdown>
    </div>
  );
}