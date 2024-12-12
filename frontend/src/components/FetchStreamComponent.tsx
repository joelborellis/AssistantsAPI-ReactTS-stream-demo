import React, { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import "github-markdown-css/github-markdown.css";
import styles from "../App.module.css";

interface StreamData {
  message: string;
}

interface FetchStreamProps {
  inputValue: string;
  assistantValue: string;
}

const FetchStreamComponent: React.FC<FetchStreamProps> = ({ inputValue, assistantValue }) => {
  const [data, setData] = useState<StreamData[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!inputValue || !assistantValue) {
      // If there's no input, don't fetch yet or fetch a default
      return;
    }

    const fetchData = async () => {
      try {
        // You can include the user input in the request URL or body.
        // For example, if your server accepts a query parameter:
        const streamUrl = `/shadow?query=${encodeURIComponent(inputValue)}&assistantId=${encodeURIComponent(assistantValue)}`;

        const response = await fetch(streamUrl, {
          headers: {
            "Content-Type": "application/json",
            Accept: "application/stream+json",
          },
        });

        if (!response.ok) {
          throw new Error("Network response was not ok");
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        const read = async () => {
          if (!reader) return;
          const { value, done } = await reader.read();
          if (done) {
            console.log("Stream completed");
            return;
          }
          const str = decoder.decode(value);
          try {
            const trimmedStr = str.trim();
            const json = JSON.parse(trimmedStr);
            setData((prevData) => [...prevData, json]);
          } catch (e) {
            console.error("Error parsing JSON:", e);
          }
          read();
        };

        read();
      } catch (e) {
        console.error("Fetch error:", e);
        setError("Failed to fetch data.");
      }
    };

    fetchData();
  }, [inputValue, assistantValue]); // re-run whenever inputValue changes

  if (error) return <div>Error: {error}</div>;

  const messagesString = data.map((message) => message.message).join("");

  return (
    <div>
      <div className={styles.container}>
        <h2>Streamed Data</h2>
        <div className={styles.box}>
          <div className={styles.markdown}>
            <ReactMarkdown>{messagesString}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FetchStreamComponent;
