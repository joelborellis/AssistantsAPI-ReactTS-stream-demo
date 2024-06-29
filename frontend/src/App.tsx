import React from 'react';
import FetchStreamComponent from './components/FetchStreamComponent';


const App: React.FC = () => {
  return (
    <div className="App">
      <header className="App-header">
        <p>
        "What are different strategies I should be considering when approaching a new prospect where we are unfamiliar and they are in the early stages of demand?"
        </p>
      </header>
      <main>
        <FetchStreamComponent />
      </main>
    </div>
  );
}

export default App;
