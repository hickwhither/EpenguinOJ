import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastContainer, Bounce } from 'react-toastify'

// Configs & Contexts
import { APP_NAME } from './Config'
import { AuthProvider } from './context/AuthContext'

// Guis
import Navbar from './components/layout/Navbar'
import Footer from './components/layout/Footer'
import LoginModal from './components/auth/LoginModal'
import RequireAuth from './components/auth/RequireAuth'

// Pages
import Home from './pages/Home'
import DiscordConfirm from './pages/DiscordConfirm'
import ProblemList from './pages/ProblemList'
import ProblemDisplay from './pages/ProblemDisplay'
import ContestList from './pages/ContestList'
import About from './pages/About'
import NotFound from './pages/NotFound'
import ContestDisplay from './pages/ContestDisplay'

const queryClient = new QueryClient()

function App() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <ToastContainer position="bottom-right" autoClose={5000} theme="dark" transition={Bounce} />
      
      <Navbar />

      <section className="section mt-5" style={{ flex: 1 }}>
        <Routes>
          <Route path="" element={<Home app={APP_NAME} />} />
          <Route path="/discord" element={<DiscordConfirm />} />
          <Route path="/about" element={<About />} />

          <Route path="/problems" element={<RequireAuth><ProblemList /></RequireAuth>} />
          <Route path="/p/:problem_id" element={<RequireAuth><ProblemDisplay /></RequireAuth>} />
          <Route path="/c/:contest_id" element={<RequireAuth><ContestDisplay /></RequireAuth>} />
          <Route path="/c/:contest_id/:problem_id" element={<RequireAuth><ProblemDisplay /></RequireAuth>} />
          <Route path="/contests" element={<RequireAuth><ContestList /></RequireAuth>} />
          

          <Route path="*" element={<NotFound />} />
        </Routes>
      </section>

      <Footer />
    </div>
  )
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <App />
          <LoginModal />
        </AuthProvider>
      </QueryClientProvider>
    </BrowserRouter>
  </StrictMode>
)