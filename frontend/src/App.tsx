import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'

import Dashboard from './routes/Dashboard'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50 text-gray-900">
        <div className="mx-auto max-w-6xl p-6">
          <header className="mb-6 flex items-center justify-between">
            <h1 className="text-2xl font-bold">Codingal AI Course Coach</h1>
            <nav className="text-sm">
              <Link to="/" className="underline">
                Dashboard
              </Link>
            </nav>
          </header>
          <Routes>
            <Route path="/" element={<Dashboard />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  )
}
