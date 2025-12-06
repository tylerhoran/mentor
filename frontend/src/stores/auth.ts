import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { apiClient } from '../api/client'

interface User {
  id: string
  email: string
  full_name: string | null
  role: 'faculty' | 'student' | 'admin' | 'researcher'
  institution_id: string | null
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName: string, role: string) => Promise<void>
  logout: () => void
  fetchUser: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (email: string, password: string) => {
        set({ isLoading: true })
        try {
          const response = await apiClient.post<{
            access_token: string
            refresh_token: string
          }>('/auth/login', { email, password })

          apiClient.setToken(response.access_token)
          localStorage.setItem('refresh_token', response.refresh_token)

          // Fetch user info
          const user = await apiClient.get<User>('/auth/me')
          set({ user, isAuthenticated: true, isLoading: false })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      register: async (email: string, password: string, fullName: string, role: string) => {
        set({ isLoading: true })
        try {
          await apiClient.post('/auth/register', {
            email,
            password,
            full_name: fullName,
            role,
          })
          set({ isLoading: false })
        } catch (error) {
          set({ isLoading: false })
          throw error
        }
      },

      logout: () => {
        apiClient.setToken(null)
        localStorage.removeItem('refresh_token')
        set({ user: null, isAuthenticated: false })
      },

      fetchUser: async () => {
        try {
          const user = await apiClient.get<User>('/auth/me')
          set({ user, isAuthenticated: true })
        } catch {
          set({ user: null, isAuthenticated: false })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
)
