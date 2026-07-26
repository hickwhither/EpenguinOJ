import React from 'react';
import { useOutletContext } from 'react-router-dom';

export default function ContestRanking() {
  const { contest } = useOutletContext();

  return (
    <>
    <p className="has-text-grey">Bảng xếp hạng cho kỳ thi {contest.name} sẽ hiển thị tại đây.</p>
    {/* Thêm logic/bảng xếp hạng ở đây */}
    </>
  );
}