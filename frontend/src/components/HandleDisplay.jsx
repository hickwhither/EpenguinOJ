import React from 'react';

export const HandleDisplay = ({ user }) => {
  const getRankTagClass = (rank) => {
    // if (!rank) return '';
    switch (rank.toLowerCase()) {
      case 'admin':
        return 'has-text-danger has-text-dark';    // Đỏ đậm quyền lực
      case 'mod':
      case 'moderator':
        return 'has-text-danger has-text-light';   // Đỏ nhạt
      case 'vip':
        return 'has-text-warning';           // Vàng VIP
      case 'pro':
      case 'diamond':
        return 'has-text-link has-text-light';     // Xanh sành điệu
      case 'gold':
        return 'has-text-success has-text-light';  // Xanh lá
    }
    return ''
  };

  return (
    <span className={getRankTagClass(user.rank)}>
      {user?.username || "Unknown"}
    </span>
  );
};
