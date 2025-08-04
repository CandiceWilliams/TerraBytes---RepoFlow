// ChatPage.jsx

import { useState, useEffect } from 'react';
import axios from 'axios';
import 'bootstrap/dist/css/bootstrap.min.css';

const API_BASE_URL = 'http://127.0.0.1:8000'; // Replace with your FastAPI backend URL

function ChatPage() {
    const [isRagReady, setIsRagReady] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [query, setQuery] = useState('');
    const [response, setResponse] = useState('');

    useEffect(() => {
        let intervalId = null;

        const checkRagReady = async () => {
            try {
                const res = await axios.get(`${API_BASE_URL}/api/check-rag-ready`);
                if (res.data.isReady) {
                    setIsRagReady(true);
                    setIsLoading(false);
                    clearInterval(intervalId);
                }
            } catch (error) {
                console.error("Error checking RAG status:", error);
            }
        };

        checkRagReady();
        intervalId = setInterval(checkRagReady, 3000);

        return () => clearInterval(intervalId);
    }, []);

    const handleQuerySubmit = async (event) => {
        event.preventDefault();
        setResponse("Thinking...");

        try {
            const res = await axios.post(`${API_BASE_URL}/api/chat`, { query });
            setResponse(res.data.response);
        } catch (error) {
            console.error("Error during chat:", error);
            setResponse("Error: Could not get a response from the RAG model.");
        }
    };

    return (
        <div className="container-fluid vh-100 bg-dark text-white d-flex flex-column p-4">
            <h1 className="text-center text-info mb-4">💬 RepoFlow Chat</h1>

            {isLoading && (
                <div className="text-center my-auto">
                    <div className="spinner-border text-info" role="status">
                        <span className="visually-hidden">Loading...</span>
                    </div>
                    <p className="mt-3">Loading RAG model into memory. This may take a moment...</p>
                </div>
            )}

            {!isLoading && !isRagReady && (
                <div className="alert alert-danger text-center my-auto" role="alert">
                    The RAG model is not ready. Please select a workspace first.
                </div>
            )}

            {!isLoading && isRagReady && (
                <>
                    <div className="flex-grow-1 overflow-auto mb-3 p-3 bg-secondary rounded border border-info" style={{ minHeight: '120px' }}>
                        {query && (
                            <div className="mb-2">
                                <span className="fw-bold text-info">You:</span>
                                <div className="bg-dark text-white p-2 rounded border border-info mt-1">
                                    {query}
                                </div>
                            </div>
                        )}
                        {response && (
                            <div>
                                <span className="fw-bold text-success">AI:</span>
                                <div className="bg-dark text-white p-2 rounded border border-success mt-1">
                                    {response}
                                </div>
                            </div>
                        )}
                    </div>

                    <form onSubmit={handleQuerySubmit} className="d-flex">
                        <input
                            type="text"
                            className="form-control me-2 bg-dark text-white border-info"
                            placeholder="Enter your query..."
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                        />
                        <button type="submit" className="btn btn-info text-white">
                            Send
                        </button>
                    </form>
                </>
            )}
        </div>
    );
}

export default ChatPage;
