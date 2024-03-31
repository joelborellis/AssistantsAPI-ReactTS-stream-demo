import React from 'react';
import FetchStreamComponent from './components/FetchStreamComponent';


const App: React.FC = () => {
  return (
    <div className="App">
      <header className="App-header">
        <p>
          Stream Example
        </p>
      </header>
      <main>
        <FetchStreamComponent />
      </main>
    </div>
  );
}

export default App;