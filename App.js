import { BrowserRouter as Router, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import { AuthProvider } from './context/AuthContext';

function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="App">
          <Route exact path="/" component={Dashboard} />
        </div>
      </AuthProvider>
    </Router>
  );
}

export default App; 