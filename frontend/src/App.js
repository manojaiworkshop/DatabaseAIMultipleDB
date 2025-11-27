import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ConnectionPage from './pages/ConnectionPage';
import ChatPage from './pages/ChatPage';
import './index.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<ConnectionPage />} />
        <Route path="/chat" element={<ChatPage />} />
      </Routes>
    </Router>
  );
}

export default App;
