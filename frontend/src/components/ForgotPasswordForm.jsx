// src/components/ForgotPasswordForm.jsx
import { useState } from 'react';
import { supabase } from '../lib/supabase';

export default function ForgotPasswordForm() {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleReset = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      // The path user lands on after clicking the email link
      redirectTo: `${window.location.origin}/update-password`,
    });

    if (error) {
      setMessage(`Error: ${error.message}`);
    } else {
      setMessage('Password reset email sent! Please check your inbox.');
    }
    setLoading(false);
  };

  return (
    <form onSubmit={handleReset} className="p-4 flex flex-col gap-3">
      <h2 className="text-xl font-bold">Reset Password</h2>
      <input
        type="email"
        placeholder="Enter your registered email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        className="p-2 border rounded"
      />
      <button 
        type="submit" 
        disabled={loading}
        className="bg-blue-600 text-white p-2 rounded"
      >
        {loading ? 'Sending...' : 'Send Reset Link'}
      </button>
      {message && <p className="text-sm mt-2">{message}</p>}
    </form>
  );
}