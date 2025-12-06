import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/auth'

// Pages
import Login from './pages/auth/Login'
import Register from './pages/auth/Register'
import FacultyDashboard from './pages/faculty/Dashboard'
import CourseBuilder from './pages/faculty/CourseBuilder'
import StudentView from './pages/faculty/StudentView'
import Analytics from './pages/faculty/Analytics'
import TutorSession from './pages/student/TutorSession'
import StudentProgress from './pages/student/Progress'
import StudentHistory from './pages/student/History'

// Components
import { Toaster } from './components/ui/toaster'

function ProtectedRoute({
  children,
  allowedRoles
}: {
  children: React.ReactNode
  allowedRoles?: string[]
}) {
  const { user, isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

function App() {
  const { user, isAuthenticated } = useAuthStore()

  return (
    <div className="min-h-screen bg-background">
      <Routes>
        {/* Auth routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Faculty routes */}
        <Route
          path="/faculty"
          element={
            <ProtectedRoute allowedRoles={['faculty', 'admin']}>
              <FacultyDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/faculty/course/:courseId"
          element={
            <ProtectedRoute allowedRoles={['faculty', 'admin']}>
              <CourseBuilder />
            </ProtectedRoute>
          }
        />
        <Route
          path="/faculty/course/:courseId/student/:studentId"
          element={
            <ProtectedRoute allowedRoles={['faculty', 'admin']}>
              <StudentView />
            </ProtectedRoute>
          }
        />
        <Route
          path="/faculty/course/:courseId/analytics"
          element={
            <ProtectedRoute allowedRoles={['faculty', 'admin']}>
              <Analytics />
            </ProtectedRoute>
          }
        />

        {/* Student routes */}
        <Route
          path="/tutor/:courseId"
          element={
            <ProtectedRoute allowedRoles={['student']}>
              <TutorSession />
            </ProtectedRoute>
          }
        />
        <Route
          path="/progress"
          element={
            <ProtectedRoute allowedRoles={['student']}>
              <StudentProgress />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute allowedRoles={['student']}>
              <StudentHistory />
            </ProtectedRoute>
          }
        />

        {/* Default redirect */}
        <Route
          path="/"
          element={
            isAuthenticated ? (
              user?.role === 'faculty' || user?.role === 'admin' ? (
                <Navigate to="/faculty" replace />
              ) : (
                <Navigate to="/progress" replace />
              )
            ) : (
              <Navigate to="/login" replace />
            )
          }
        />
      </Routes>
      <Toaster />
    </div>
  )
}

export default App
