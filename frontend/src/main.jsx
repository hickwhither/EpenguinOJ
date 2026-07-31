import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ToastContainer, Bounce } from 'react-toastify'

import { AuthProvider } from './context/AuthProvider'
import LoginModal from './components/auth/LoginModal'
import App from './App'

const queryClient = new QueryClient()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <App />
          <LoginModal />
          <ToastContainer position="bottom-right" autoClose={5000} theme="dark" transition={Bounce} />
        </AuthProvider>
      </QueryClientProvider>
    </BrowserRouter>
  </StrictMode>
)
