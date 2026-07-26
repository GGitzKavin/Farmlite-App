import React from 'react';
import { Navigate, useParams } from 'react-router-dom';

const EditLivestock: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  return id ? (
    <Navigate to={`/livestock/${id}?edit=true`} replace />
  ) : (
    <Navigate to="/livestock" replace />
  );
};

export default EditLivestock;
