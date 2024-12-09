import React, { useState } from "react";
import FetchStreamComponent from "./components/FetchStreamComponent";
import InputComponent from "./components/InputComponent";

const App: React.FC = () => {
  const [userInput, setUserInput] = useState<string>("");
  const [assistantId, setAssistantId] = useState<string>("");

  const getData = (input: string, assistantId: string) => {
    console.log("Input received in App:", input);
    setUserInput(input);
    setAssistantId(assistantId)
    // Add your logic here if needed.
  };

  return (
    <div className="App">
      <header className="App-header">
      </header>
      <main>
        <div>
          <InputComponent getData={getData} />
        </div>
        {/* Pass the userInput and assistantValue as a prop to FetchStreamComponent */}
        <FetchStreamComponent inputValue={userInput} assistantValue={assistantId} />
      </main>
    </div>
  );
};

export default App;
