import React from 'react';
import { useOutletContext } from 'react-router-dom';

export default function ContestRanking() {
  const { contest } = useOutletContext();

  return (
    <>
    <p className="has-text-grey">The ranking for contest {contest.name} will be displayed here.</p>
    {/* Thêm logic/bảng xếp hạng ở đây */}
    </>
  );
}