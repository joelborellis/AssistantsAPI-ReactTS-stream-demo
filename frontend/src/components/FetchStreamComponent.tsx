import React, { useEffect, useState } from 'react';

interface StreamData {
  message: string;
}

const FetchStreamComponent: React.FC = () => {
  const [data, setData] = useState<StreamData[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // Update with your Flask streaming endpoint
        const streamUrl = 'http://localhost:5000/stream';
        const response = await fetch(streamUrl, {
          headers: {
            'Content-Type': 'application/json',
            Accept: 'application/stream+json',
          },
        });

        // Check if the response is ok (status in the range 200-299)
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }

        const reader = response.body?.getReader();
        const decoder = new TextDecoder();

        const read = async () => {
          if (!reader) return;
          const { value, done } = await reader.read();
          if (done) {
            console.log('Stream completed');
            return;
          }
          const str = decoder.decode(value);
          try {
            const json = JSON.parse(str);
            setData((prevData) => [...prevData, json]);
          } catch (e) {
            console.error('Error parsing JSON:', e);
          }
          read(); // Read the next chunk
        };

        read();
      } catch (e) {
        console.error('Fetch error:', e);
        setError('Failed to fetch data.');
      }
    };

    fetchData();
  }, []);

  if (error) return <div>Error: {error}</div>;

  //const messagesString = data.map(message => JSON.stringify(message)).join(' ');
  const messagesString = data.map(message => message.message).join('');

  return (
    <div>
      <h2>Streamed Data</h2>
      <div>{messagesString}</div>
    </div>
  );
};

export default FetchStreamComponent;