# 🐍 Sabine: A VALORANT Champions Tour Chatbot

Welcome to **Sabine**, a chatbot built for the **VALORANT Champions Tour**!  
Named after the agent **Viper** (my personal favorite), Sabine’s design and aesthetic draw inspiration from her toxic, techy flair.

I'm **Ryan Jewik**, a Computer Science and Data Science graduate from Chapman University. This project blends my interests in coding, data, and esports—particularly competitive VALORANT—into a full-stack application I'm proud to share.

---

## 🧠 What is Sabine?

Sabine is powered by **Retrieval-Augmented Generation (RAG)** to provide more accurate and context-aware responses than typical language models. The system reduces hallucinations by grounding its answers in curated data sources.

Data sources include:
- The **RIOT Games Hackathon S3 Bucket** (official VCT data)
- Web-scraped data from sites like **VLR.gg**

This information was cleaned, transformed, and turned into documents summarizing matches, players, and stats.  
We also use **Parental Document Retrieval** to improve context depth—though this occasionally causes token limit errors. To mitigate this, I implemented a summarization function to reduce prompt size when needed (though the issue may still occur at times).

---

## ⚙️ Tech Stack

- 🧑‍💻 **Frontend**: React  
- 🐍 **Backend**: Python (Flask)  
- 🧠 **LLMs**: OpenAI (used for both chatbot and embeddings)  
- 🧵 **Persistence**: MongoDB (messages, threads, vector store)  
- 🧾 **User Accounts**: PostgreSQL with passwords hashed using Argon2  

---

## 🚀 Getting Started

To run Sabine locally:

### 1. Start the Backend
```bash
cd flask-server
venv\Scripts\activate      # On Windows
python server.py
```

### 2. Start the Frontend
```bash
cd client
npm start
```

---

## 📚 Resources

- **Figma Prototype**:  
  [🎨 View on Figma](https://www.figma.com/design/FbJGgsLIaidxzPkjHDsrwv/valorant-chatbot-app?node-id=0-1&m=de)

- **Official S3 Bucket (VCT Data)**:  
  [📁 S3 Data](https://vcthackathon-data.s3.us-west-2.amazonaws.com)

- **Player Stats from VLR.gg**:  
  [📊 VLR Player Stats](https://www.vlr.gg/stats/?event_group_id=74&region=all&min_rounds=10&min_rating=1550&agent=all&map_id=all&timespan=60d)

---

## 🙏 Thanks

I hope you enjoy exploring Sabine as much as I enjoyed building it!  
Combining my passions for software development and competitive VALORANT has been a rewarding experience—thank you for checking it out.
