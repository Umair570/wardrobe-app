import { useEffect, useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import { ToastProvider, useToast } from './components/ToastProvider'
import ProfilePage from './pages/ProfilePage'
import AuthPage from './pages/AuthPage'
import ForgotPasswordForm from './components/ForgotPasswordForm'
import UpdatePasswordPage from './pages/UpdatePasswordPage'

import Nav from './components/Nav'
import SidebarNav from './components/SidebarNav'
import BottomNav from './components/BottomNav'
import ChatbotDock from './components/ChatbotDock'
import HomePage from './pages/HomePage'
import UploadPage from './pages/UploadPage'
import WardrobePage from './pages/WardrobePage'
import ItemDetailsPage from './pages/ItemDetailsPage'
import OutfitVisualizationPage from './pages/OutfitVisualizationPage'
import StylistPage from './pages/StylistPage'
import RecommendedOutfitsPage from './pages/RecommendedOutfitsPage'

import { fetchWardrobe, removeItem } from './api/wardrobeApi'
import { postVisualization } from './api/stylistApi'


function WardrobeApp() {
  const notify = useToast()
  const [page, setPage] = useState('home')
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [activeItem, setActiveItem] = useState(null)
  const [activeOutfit, setActiveOutfit] = useState(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    fetchWardrobe()
      .then(setItems)
      .finally(() => setLoading(false))
  }, [])

  const navigate = (target) => {
    setPage(target)
    window.scrollTo({ top: 0 })
  }

  const handleUploaded = (item) => {
    setItems((prev) => [item, ...prev])
    notify('Item added successfully')
  }

  const openItem = (item) => {
    setActiveItem(item)
    navigate('details')
  }

  const visualizeItem = async (item) => {
    try {
      const layout = await postVisualization([item.id])
      setActiveOutfit(layout)
    } catch {
      setActiveOutfit({ mode: 'offline', items: [], slots: [], tags: [], description: `Could not load visualization for ${item.name || item.type}. Is the backend running?` })
    }
    navigate('visualize')
  }

  const visualizeItemById = async (itemId) => {
    const item = items.find((i) => i.id === itemId)
    if (!item) {
      try {
        const layout = await postVisualization([itemId])
        setActiveOutfit(layout)
        navigate('visualize')
      } catch (err) {
        notify(err.message || 'Could not visualize this item.')
      }
      return
    }
    await visualizeItem(item)
  }

  const visualizeMultipleItems = async (itemIds) => {
    if (!itemIds || itemIds.length === 0) return
    try {
      const layout = await postVisualization(itemIds)
      setActiveOutfit(layout)
    } catch (err) {
      notify(err.message || 'Could not visualize selected items.')
    }
    navigate('visualize')
  }

  const visualizeRecommendation = async (outfit) => {
    if (outfit.item_ids && outfit.item_ids.length > 0) {
      try {
        const layout = await postVisualization(outfit.item_ids)
        setActiveOutfit(layout)
      } catch {
        setActiveOutfit({ mode: 'offline', items: [], slots: [], tags: [], description: 'Could not load visualization. Is the backend running?' })
      }
    } else {
      setActiveOutfit(outfit)
    }
    navigate('visualize')
  }


  const handleRemove = async (item) => {
    await removeItem(item.id)
    setItems((prev) => prev.filter((i) => i.id !== item.id))
    notify(`${item.name} removed from your wardrobe`)
    navigate('wardrobe')
  }

  const [userBodyPhoto, setUserBodyPhoto] = useState(() => localStorage.getItem('user_body_photo') || '')

  const handleSaveUserBodyPhoto = (photoDataUrl) => {
    setUserBodyPhoto(photoDataUrl)
    if (photoDataUrl) {
      localStorage.setItem('user_body_photo', photoDataUrl)
      notify('Body photo template saved')
    } else {
      localStorage.removeItem('user_body_photo')
      notify('Body photo template removed')
    }
  }

  return (
    <div className="min-h-full flex flex-col">
      {/* 1. Pass onNavigate to Nav so the profile dropdown can switch pages */}
      <Nav onOpenSidebar={() => setSidebarOpen(true)} onNavigate={navigate} />

      <SidebarNav open={sidebarOpen} page={page} onNavigate={navigate} onClose={() => setSidebarOpen(false)} />

      <main className="flex-1 pb-20 md:pb-0">
        {page === 'home' && <HomePage onNavigate={navigate} items={items} />}

        {/* 2. Render Profile Page when requested */}
        {page === 'profile' && <ProfilePage onBack={() => navigate('home')} />}

        {page === 'upload' && <UploadPage onUploaded={handleUploaded} onNavigate={navigate} />}

        {page === 'wardrobe' && (
          <WardrobePage
            items={items}
            loading={loading}
            onOpenItem={openItem}
            onGoToUpload={() => navigate('upload')}
            onVisualizeMultiple={visualizeMultipleItems}
          />
        )}

        {page === 'details' && (
          <ItemDetailsPage
            item={activeItem}
            onBack={() => navigate('wardrobe')}
            onVisualize={visualizeItem}
            onAskStylist={() => navigate('stylist')}
            onRemove={handleRemove}
          />
        )}

        {page === 'visualize' && (
          <OutfitVisualizationPage
            outfit={activeOutfit}
            userBodyPhoto={userBodyPhoto}
            onSaveUserBodyPhoto={handleSaveUserBodyPhoto}
            onBack={() => navigate('wardrobe')}
            onChangeClothing={() => navigate('wardrobe')}
            onGenerateAnother={() => navigate('recommended')}
          />
        )}


        {page === 'stylist' && (
          <StylistPage
            items={items}
            onViewRecommended={() => navigate('recommended')}
            onVisualizeItem={visualizeItemById}
            onVisualizeOutfit={visualizeMultipleItems}
          />
        )}


        {page === 'recommended' && (
          <RecommendedOutfitsPage items={items} onBack={() => navigate('stylist')} onVisualize={visualizeRecommendation} />
        )}
      </main>

      <BottomNav page={page} onNavigate={navigate} onAdd={() => navigate('upload')} onOpenSidebar={() => setSidebarOpen(true)} />

      <ChatbotDock
        items={items}
        onExpand={() => navigate('stylist')}
        onVisualizeItem={visualizeItemById}
        onVisualizeOutfit={visualizeMultipleItems}
      />
    </div>
  )
}

function AuthGate() {
  const { user, ready } = useAuth()
  if (!ready) return null
  if (!user) return <AuthPage />
  return <WardrobeApp />
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            {/* Unprotected Auth Routes */}
            <Route path="/forgot-password" element={<ForgotPasswordForm />} />
            <Route path="/update-password" element={<UpdatePasswordPage />} />
            
            {/* Main Application Gate */}
            <Route path="/" element={<AuthGate />} />
            
            {/* Catch-all redirect to home */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  )
}