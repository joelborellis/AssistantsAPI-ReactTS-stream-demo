import React from "react";
import FetchStreamComponent from "./components/FetchStreamComponent";
import InputComponent from "./components/InputComponent";

const App: React.FC = () => {
  const getData = (input: string) => {
    console.log("Input received:", input);
    // Add your logic here
  };

  return (
    <div className="App">
      <header className="App-header">
        <p>
          "What are different strategies I should be considering when
          approaching a new prospect where we are unfamiliar and they are in the
          early stages of demand?"
        </p>
      </header>
      <main>
        <div>
          <InputComponent getData={getData} />
        </div>
        <FetchStreamComponent />
      </main>
    </div>
  );
};

export default App;
