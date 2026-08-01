// src/pages/UpdatePasswordPage.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';

export default function UpdatePasswordPage() {
  const [newPassword, setNewPassword] = useState('');
  const [status, setStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleUpdatePassword = async (e) => {
    e.preventDefault();
    setLoading(true);

    // Call updateUser while the user is authenticated via the email reset token
    const { error } = await supabase.auth.updateUser({
      password: newPassword,
    });

    if (error) {
      setStatus(`Error: ${error.message}`);
    } else {
      setStatus('Password successfully updated! Redirecting to login...');
      setTimeout(() => navigate('/login'), 2000);
    }
    setLoading(false);
  };

  return (
    <div className="max-w-md mx-auto mt-10 p-6 border rounded shadow">
      <h2 className="text-2xl font-semibold mb-4">Set New Password</h2>
      <form onSubmit={handleUpdatePassword} className="flex flex-col gap-4">
        <input
          type="password"
          placeholder="Enter new password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          minLength={6}
          required
          className="p-2 border rounded"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-green-600 text-white py-2 rounded font-medium"
        >
          {loading ? 'Updating...' : 'Update Password'}
        </button>
      </form>
      {status && <p className="mt-4 text-sm text-gray-700">{status}</p>}
    </div>
  );
}