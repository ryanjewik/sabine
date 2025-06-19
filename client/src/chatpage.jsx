import React, { useState, useRef, useEffect } from "react";
import "./chatpagestyle.css";
import { ReactComponent as UserPFP } from "./img/user-profile-pic.svg";
import { ReactComponent as ViperPFP } from "./img/viper-profile-pic.svg";
import { ReactComponent as SettingsBtn } from "./img/settings-btn.svg";
import axios from 'axios';

/*
//connect to mongoDB and fetch chat history
const { MongoClient, ServerApiVersion } = require("mongodb");
const uri = "mongodb+srv://ryanjewik:7Ku3pYQtCJerX59x@cluster0.0drkzoy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0";
const client = new MongoClient(uri,  {
        serverApi: {
            version: ServerApiVersion.v1,
            strict: true,
            deprecationErrors: true,
        }
    }
);
async function run() {
  try {
    // Connect the client to the server (optional starting in v4.7)
    await client.connect();
    // Send a ping to confirm a successful connection
    await client.db("admin").command({ ping: 1 });
    console.log("Pinged your deployment. You successfully connected to MongoDB!");
  } finally {
    // Ensures that the client will close when you finish/error
    await client.close();
  }
}
run().catch(console.dir);
*/



export const ChatPage = () => {
  const [messages, setMessages] = useState([]); // Start empty, will fetch from backend
  const [input, setInput] = useState("");
  const chatEndRef = useRef(null);

  // Fetch messages from backend on mount
  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const res = await axios.get('http://localhost:5000/get_messages');
        if (res.data && res.data.messages) {
          setMessages(res.data.messages);
        }
      } catch (err) {
        console.error('Failed to fetch messages:', err);
      }
    };
    fetchMessages();
  }, []);

  useEffect(() => {
    if (chatEndRef.current) {
      chatEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  const handleSend = async (event) => {
    console.log('handleSend called'); // Debug: function called
    if (event) event.preventDefault();
    if (!input.trim()) return;
    
    const date = new Date();
    try {
      await axios.post('http://localhost:5000/save_input', { input: input, sender: "user", timestamp: date.toLocaleString('en-US') });
      console.log('Message saved to backend:', input); // Success log
      setMessages([...messages, { sender: "user", text: input, timestamp: date.toLocaleString('en-US') }]);
      setInput("");
    } catch (error) {
      console.error("Error sending message:", error);
    }
  };

  const handleInputChange = (event) => {
    setInput(event.target.value);
    console.log('Input changed:', event.target.value); // Debug: input change
  };

  const handleInputKeyDown = (event) => {
    if (event.key === 'Enter') {
      handleSend(event);
    }
  };

  return (
    <div className="chat-gpt-layout">
      <aside className="sidebar">
        <div className="sidebar-header">
          <span>Chats</span>
        </div>
        <div className="sidebar-chats">
          <div className="sidebar-chat-item active">
            <span>who is the best initiator in NA?</span>
          </div>
          <div className="sidebar-chat-item">
            <span>is yay washed?</span>
          </div>
          <div className="sidebar-chat-item">
            <span>team builder</span>
          </div>
        </div>
        <div className="sidebar-settings">
          <SettingsBtn className="settings-icon" />
          <span>Settings</span>
        </div>
      </aside>
      <main className="chat-main">
        <div className="chat-messages">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`chat-message ${msg.sender === "user" ? "user" : "bot"}`}
            >
              {msg.sender === "bot" ? (
                <ViperPFP className="chat-avatar" />
              ) : (
                <UserPFP className="chat-avatar" />
              )}
              <div className="chat-bubble">
                <div className="chat-text">{msg.text}</div>
                <div className="chat-time">{msg.time}</div>
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
        <div className="chat-input-bar">
          <input
            className="chat-input"
            type="text"
            placeholder="Type your message..."
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleInputKeyDown}
            autoFocus
          />
          <button className="send-btn" type="button" onClick={handleSend}>Send</button>
        </div>
      </main>
    </div>
  );
};

export default ChatPage;
