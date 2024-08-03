import { useState } from 'react'
import HandGesture from './components/HandGesture'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <HandGesture/>
    </>
  )
}

export default App
