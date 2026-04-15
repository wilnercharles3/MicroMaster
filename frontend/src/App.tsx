// App shell: header with brand + progress strip, routed content area.

import { NavLink, Route, Routes } from 'react-router-dom'

import { ProgressHeader } from './components/ProgressHeader'
import { ToastHost } from './components/Toast'
import { ChapterPage } from './pages/Chapter'
import { HomePage } from './pages/Home'
import { MicroDosePage } from './pages/MicroDose'
import { ProgressProvider } from './state'

function Shell() {
  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <NavLink to="/">Micro<span className="brand-accent">Master</span></NavLink>
        </div>
        <nav>
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'active' : '')}>Roadmap</NavLink>
        </nav>
        <ProgressHeader />
      </header>
      <main className="main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/chapters/:number" element={<ChapterPage />} />
          <Route path="/doses/:id" element={<MicroDosePage />} />
          <Route path="*" element={<div className="loading">Not found.</div>} />
        </Routes>
      </main>
      <ToastHost />
    </div>
  )
}

export default function App() {
  return (
    <ProgressProvider>
      <Shell />
    </ProgressProvider>
  )
}
