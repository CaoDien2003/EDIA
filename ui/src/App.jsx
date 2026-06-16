import { Routes, Route } from 'react-router-dom'
import Chat from './pages/Chat'
import Admin from './pages/Admin'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Chat />} />
      <Route path="/admin" element={<Admin />} />
    </Routes>
  )
}
