// src/pages/AuthPage.jsx
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../components/ToastProvider'

export default function AuthPage() {
  const { login, signup } = useAuth()
  const notify = useToast()

  const [mode, setMode] = useState('login') // 'login' or 'signup'

  // Form Fields
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const [loading, setLoading] = useState(false)

  // Switch between Login and Signup modes cleanly
  const handleModeSwitch = (newMode) => {
    setMode(newMode)
  }

  // Handle Form Submission
  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      if (mode === 'login') {
        // --- LOG IN FLOW ---
        await login(email, password)
        notify('Logged in successfully!')
      } else {
        // --- SIGN UP FLOW ---
        await signup(email, password, { full_name: fullName })
        notify('Account created successfully! Please check your email to verify.')
      }
    } catch (err) {
      notify(err.message || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-sand-100 p-4">
      <div className="max-w-md w-full bg-white/80 backdrop-blur-md p-8 rounded-2xl shadow-xl border border-ink/10">
        
        {/* Toggle Login / Sign Up */}
        <div className="flex bg-ink/5 p-1 rounded-xl mb-6">
          <button
            type="button"
            onClick={() => handleModeSwitch('login')}
            className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${
              mode === 'login' ? 'bg-white shadow-sm text-ink' : 'text-ink/60 hover:text-ink'
            }`}
          >
            Log In
          </button>
          <button
            type="button"
            onClick={() => handleModeSwitch('signup')}
            className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${
              mode === 'signup' ? 'bg-white shadow-sm text-ink' : 'text-ink/60 hover:text-ink'
            }`}
          >
            Sign Up
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          
          {/* SIGN UP FULL NAME FIELD */}
          {mode === 'signup' && (
            <div>
              <label className="block text-xs font-semibold text-ink/70 mb-1">Full Name</label>
              <input
                type="text"
                placeholder="Jane Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                className="w-full p-3 border border-ink/15 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-accent"
              />
            </div>
          )}

          {/* EMAIL FIELD */}
          <div>
            <label className="block text-xs font-semibold text-ink/70 mb-1">Email</label>
            <input
              type="email"
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full p-3 border border-ink/15 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>

          {/* PASSWORD FIELD */}
          <div>
            <label className="block text-xs font-semibold text-ink/70 mb-1">Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              className="w-full p-3 border border-ink/15 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>

          {/* LOGIN EXTRA OPTIONS */}
          {mode === 'login' && (
            <div className="flex items-center justify-between text-xs mt-1">
              <label className="flex items-center gap-2 text-ink/70 cursor-pointer">
                <input type="checkbox" className="rounded border-ink/20 accent-accent" />
                Remember me
              </label>
              
              <Link 
                to="/forgot-password" 
                className="text-accent hover:underline font-medium"
              >
                Forgot password?
              </Link>
            </div>
          )}

          {/* SUBMIT BUTTON */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 mt-2 bg-blue-600 text-white font-medium rounded-xl hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Processing...' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  )
}