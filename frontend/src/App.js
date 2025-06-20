import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import MainMenu from './pages/MainMenu';
import GamesList from './pages/GamesList';
import ComingSoon from './pages/ComingSoon';
import AuthMenu from './pages/auth/AuthMenu';
import CreateGame from './pages/CreateGame';
import AuthGuest from 'pages/auth/AuthGuest';
import AuthRequiredRoute from 'utils/authMiddleware';
import Game from './pages/Game';
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={
            <AuthRequiredRoute>
              <MainMenu />
            </ AuthRequiredRoute>
          } 
        />
        <Route path="/games" element={
          <AuthRequiredRoute>
            <GamesList />
          </ AuthRequiredRoute>
          } />
          
        <Route path="/create-game" element={
          <AuthRequiredRoute>
            <CreateGame />
          </ AuthRequiredRoute>
        } />
        <Route path="/game/:game_id" element={
          <AuthRequiredRoute>
            <Game />
          </ AuthRequiredRoute>
        } /> 
        <Route path="/coming-soon" element={<ComingSoon />} />
        <Route path="/auth" element={ <AuthMenu /> } />
        <Route path="/auth-guest/" element={<AuthGuest />} />
        {/* public routes */}
        {/* <Route path="/auth_telegramm" element={<ComingSoon />} /> */}
      </Routes>
    </Router>
  );
}

export default App;
