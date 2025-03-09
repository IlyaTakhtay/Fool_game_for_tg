import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import MainMenu from './pages/MenuPage';
import GameList from './pages/OnlineRoomsPage';
import ComingSoon from './pages/ComingSoon';
import AuthMenu from './pages/AuthMenu';
import CreatingRoom from './pages/CreatingRoomPage';
import CardTable from './pages/CardTable';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainMenu />} />
        <Route path="/games" element={<GameList />} />
        <Route path="/coming-soon" element={<ComingSoon />} />
        <Route path="/auth" element={<AuthMenu />} />
        <Route path="/create-game" element={<CreatingRoom />} />
        <Route path="/card-table/:gameId/:userId" element={<CardTable />} /> 

        {/* <Route path="/auth_telegramm" element={<ComingSoon />} /> */}
        {/* <Route path="/auth_guest" element={<ComingSoon />} /> */}
      </Routes>
    </Router>
  );
}

export default App;
