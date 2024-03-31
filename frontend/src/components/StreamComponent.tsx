import React, { useEffect, useState } from 'react';

type JsonMessage = any; // Define your JSON message type here, e.g., { id: number; content: string; }

const StreamComponent: React.FC = () => {
  const [messages, setMessages] = useState<JsonMessage[]>([]);
  
  useEffect(() => {
    let isCancelled = false;
    
    async function consumeStream() {
      const response = await fetch('/stream');
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      let buffer = '';
      async function read() {
        const { value, done } = await reader?.read() ?? { value: undefined, done: true };
        if (done || isCancelled) {
          reader?.cancel();
          return;
        }

        buffer += decoder.decode(value, { stream: true });
        let lines = buffer.split('\n');
        buffer = lines.pop() || ''; // In case the last line is incomplete

        const newMessages = lines
          .filter(line => line.trim().length > 0)
          .map(line => JSON.parse(line));

        setMessages(prevMessages => [...prevMessages, ...newMessages]);

        // Recursively read the next chunk
        read();
      }

      await read();
    }

    consumeStream().catch(console.error);

    // Cleanup function to stop reading if the component is unmounted
    return () => {
      isCancelled = true;
    };
  }, []); // Empty dependency array means this effect runs once on mount

  return (
    <div>
      <h2>Streamed Messages</h2>
        {messages.map((message, index) => (
          <li key={index}>{JSON.stringify(message)}</li> // Customize how you render each message
        ))}
    </div>
  );
};

export default StreamComponent;