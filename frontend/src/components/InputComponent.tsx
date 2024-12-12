import React, { useState } from "react";
import styles from "./Component.module.css";

interface InputComponentProps {
  getData: (input: string,assistantValue: string) => void;
}

const InputComponent: React.FC<InputComponentProps> = ({ getData }) => {
  const [inputValue, setInputValue] = useState("");
  const [assistantValue, setAssistantValue] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // You can incorporate `mode` into your getData logic if needed.
    // For now, we just pass the inputValue.
    getData(inputValue, assistantValue);
    setInputValue(""); // Clear the input after sending
  };

  return (
    <div className={styles.container}>
      <form onSubmit={handleSubmit} className={styles.form}>
        <select
          className={styles.select}
          value={assistantValue}
          onChange={(e) => setAssistantValue(e.target.value)}
        >
          <option value="asst_mjyck1jtUVq3A182NSO2rdcu">Get Insights</option>
          <option value="">Create MEG</option>
        </select>

        <textarea
          className={styles.textarea}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Ask Shadow..."
        />

        <button type="submit" className={styles.button}>
          Send
        </button>
      </form>
    </div>
  );
};

export default InputComponent;
