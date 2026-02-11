import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [nodeData, setNodeData] = useState(null)
  const [fastApiData, setFastApiData] = useState(null)
  const [fastApiNodeData, setFastApiNodeData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const callNode = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${import.meta.env.VITE_NODE_API_URL}/data`);
      setNodeData(response.data);
    } catch (err) {
      setError('Error calling Node.js: ' + err.message);
    } finally {
      setLoading(false);
    }
  }

  const callFastApi = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${import.meta.env.VITE_FASTAPI_URL}/data`);
      setFastApiData(response.data);
    } catch (err) {
      setError('Error calling FastAPI: ' + err.message);
    } finally {
      setLoading(false);
    }
  }

  const callFastApiToNode = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${import.meta.env.VITE_FASTAPI_URL}/call-node`);
      setFastApiNodeData(response.data);
    } catch (err) {
      setError('Error calling FastAPI -> Node: ' + err.message);
    } finally {
      setLoading(false);
    }
  }

  // Redis State
  const [redisKey, setRedisKey] = useState('')
  const [redisValue, setRedisValue] = useState('')
  const [redisData, setRedisData] = useState(null)

  const saveToRedis = async () => {
    setLoading(true);
    setError(null);
    try {
      await axios.post(`${import.meta.env.VITE_FASTAPI_URL}/redis`, {
        key: redisKey,
        value: redisValue
      });
      setRedisKey('');
      setRedisValue('');
      // Refresh list
      getFromRedis();
    } catch (err) {
      setError('Error saving to Redis: ' + err.message);
    } finally {
      setLoading(false);
    }
  }

  const getFromRedis = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${import.meta.env.VITE_FASTAPI_URL}/redis`);
      setRedisData(response.data);
    } catch (err) {
      setError('Error reading from Redis: ' + err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <h1>Microservices Communication Demo</h1>
      
      <div className="card">
        <h2>Direct to Node.js</h2>
        <button onClick={callNode} disabled={loading}>Call Node Service</button>
        {nodeData && <pre>{JSON.stringify(nodeData, null, 2)}</pre>}
      </div>

      <div className="card">
        <h2>Direct to FastAPI</h2>
        <button onClick={callFastApi} disabled={loading}>Call FastAPI Service</button>
        {fastApiData && <pre>{JSON.stringify(fastApiData, null, 2)}</pre>}
      </div>

      <div className="card">
        <h2>FastAPI calls Node.js</h2>
        <button onClick={callFastApiToNode} disabled={loading}>Call FastAPI &rarr; Node</button>
        {fastApiNodeData && <pre>{JSON.stringify(fastApiNodeData, null, 2)}</pre>}
      </div>

      <div className="card">
        <h2>Redis Store (FastAPI &rarr; Redis)</h2>
        <div className="input-group">
          <input 
            type="text" 
            placeholder="Key" 
            value={redisKey} 
            onChange={(e) => setRedisKey(e.target.value)}
          />
          <input 
            type="text" 
            placeholder="Value" 
            value={redisValue} 
            onChange={(e) => setRedisValue(e.target.value)}
          />
          <button onClick={saveToRedis} disabled={loading || !redisKey || !redisValue}>Save to Redis</button>
        </div>
        <div style={{marginTop: '1rem'}}>
          <button onClick={getFromRedis} disabled={loading} style={{backgroundColor: '#2ecc71'}}>Read All from Redis</button>
        </div>
        {redisData && <pre>{JSON.stringify(redisData, null, 2)}</pre>}
      </div>

      {error && <div className="error">{error}</div>}
    </div>
  )
}

export default App
