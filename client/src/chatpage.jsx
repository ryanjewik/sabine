import React, { useState, useRef, useEffect } from "react";
import "./chatpagestyle.css";
import { ReactComponent as UserPFP } from "./img/user-profile-pic.svg";
import { ReactComponent as ViperPFP } from "./img/viper-profile-pic.svg";
import { ReactComponent as SettingsBtn } from "./img/settings-btn.svg";


//demo messages to simulate a chat history
const demoMessages = [
  { sender: "bot", text: "If you can clone KangKang, the best player in the world then create a team of 5 Kang Kangs. If not, consider Riehns, Valyn, Aspas, Nats, and Shanks.", time: "1:45AM 9/16/2024" },
  { sender: "user", text: "You’re delusional.", time: "1:54AM 9/16/2024" },
  { sender: "bot", text: "UUUHHHHHH you’re braindead", time: "1:57AM 9/16/2024" },
  { sender: "bot", text: "track by track baby", time: "1:58AM 9/16/2024" },
];

export const ChatPage = () => {
  const [messages, setMessages] = useState(demoMessages);
  const [input, setInput] = useState("");
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    const date = new Date();
    setMessages([...messages, { sender: "user", text: input, time: date.toLocaleString('en-US') }]);
    setInput("");
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
        <form className="chat-input-bar" onSubmit={handleSend}>
          <input
            className="chat-input"
            type="text"
            placeholder="Type your message..."
            value={input}
            onChange={e => setInput(e.target.value)}
            autoFocus
          />
          <button className="send-btn" type="submit">Send</button>
        </form>
      </main>
    </div>
  );
};

export default ChatPage;
