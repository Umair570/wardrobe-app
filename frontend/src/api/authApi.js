// authApi.js
//
// MOCK, INSECURE, FRONTEND-ONLY auth layer. Credentials are stored in
// plaintext in localStorage purely so the Login/Sign Up flow is fully
// clickable during development. This MUST be replaced with a real backend
// (hashed passwords, server-issued sessions/JWT) before this app ever
// touches a real user's data.

const USERS_KEY = 'wardrobe:users'
const SESSION_KEY = 'wardrobe:session'

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function readUsers() {
  try {
    return JSON.parse(localStorage.getItem(USERS_KEY)) || []
  } catch {
    return []
  }
}

function writeUsers(users) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

export async function signUp({ fullName, email, password }) {
  await delay(450)
  const users = readUsers()
  if (users.some((u) => u.email.toLowerCase() === email.toLowerCase())) {
    throw new Error('An account with that email already exists.')
  }
  const user = { id: `user_${Date.now()}`, fullName, email, password }
  writeUsers([...users, user])
  const session = { id: user.id, fullName: user.fullName, email: user.email }
  localStorage.setItem(SESSION_KEY, JSON.stringify(session))
  return session
}

export async function logIn({ email, password, rememberMe }) {
  await delay(450)
  const users = readUsers()
  const user = users.find((u) => u.email.toLowerCase() === email.toLowerCase() && u.password === password)
  if (!user) {
    throw new Error('Incorrect email or password.')
  }
  const session = { id: user.id, fullName: user.fullName, email: user.email }
  if (rememberMe) {
    localStorage.setItem(SESSION_KEY, JSON.stringify(session))
  } else {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(session))
  }
  return session
}

export function getSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY) || sessionStorage.getItem(SESSION_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function logOut() {
  localStorage.removeItem(SESSION_KEY)
  sessionStorage.removeItem(SESSION_KEY)
}
