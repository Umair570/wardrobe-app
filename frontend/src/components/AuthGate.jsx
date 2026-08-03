// src/components/AuthGate.jsx
import React from 'react'
import { useAuth } from '../context/AuthContext'
import AuthPage from '../pages/AuthPage'
import WardrobeInsights from './WardrobeInsights' // Put the import here

export default function AuthGate() {
  const { user } = useAuth()

  // 1. If not logged in, render the AuthPage form
  if (!user) {
    return <AuthPage />
  }

  // 2. If logged in, render your Dashboard with WardrobeInsights!
  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <WardrobeInsights />
      
      {/* Rest of your wardrobe app UI */}
    </div>
  )
}