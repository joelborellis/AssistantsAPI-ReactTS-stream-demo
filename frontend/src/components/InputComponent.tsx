import React, { useState } from 'react';

interface InputComponentProps {
  getData: (input: string) => void;
}

const InputComponent: React.FC<InputComponentProps> = ({ getData }) => {
  const [inputValue, setInputValue] = useState<string>('');

  const handleSubmit = () => {
    getData(inputValue);
    setInputValue(''); // Clear the input after submission
  };

  return (
    <div>
      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        placeholder="Enter text"
      />
      <button onClick={handleSubmit}>Submit</button>
    </div>
  );
};

export default InputComponent;