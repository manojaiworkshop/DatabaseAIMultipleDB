# DatabaseAI - Full Stack Application

A modern full-stack application that allows users to interact with PostgreSQL databases using natural language queries. Built with React, Tailwind CSS, FastAPI, and multiple LLM providers (OpenAI, vLLM, Ollama).

## 🌟 Features

- **🔌 Database Connection**: Easy-to-use interface for connecting to PostgreSQL databases
- **💬 Natural Language Chat**: Ask questions in plain English and get SQL queries automatically
- **🤖 Multiple LLM Providers**: Switch between OpenAI, vLLM, and Ollama
- **📊 Interactive Results**: View query results in beautiful, responsive tables
- **🎨 Modern UI**: Responsive design that works on desktop and mobile
- **⚡ Real-time Processing**: Fast query generation and execution
- **🔒 Secure**: Database credentials handled securely

## 📁 Project Structure

```
DATABASEAI/
├── backend/                  # FastAPI backend
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── models/          # Pydantic models
│   │   │   └── schemas.py
│   │   ├── routes/          # API routes
│   │   │   └── api.py
│   │   └── services/        # Business logic
│   │       ├── database.py  # Database service
│   │       └── llm.py       # LLM service
│   └── requirements.txt
├── frontend/                 # React frontend
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── ConnectionPage.js
│   │   │   └── ChatPage.js
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.js
│   │   ├── index.js
│   │   └── index.css
│   ├── package.json
│   └── tailwind.config.js
├── app_config.yml           # Backend configuration
└── config.yml               # Database import/export config
```

## 🚀 Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL database
- (Optional) Docker if using containerized database

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure LLM providers in `app_config.yml`:**
   - Set your OpenAI API key if using OpenAI
   - Configure vLLM API URL if using vLLM
   - Configure Ollama API URL if using Ollama
   - Choose default provider

5. **Run the backend:**
```bash
cd ..
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8088
```

The API will be available at `http://localhost:8088`

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Create environment file (`.env`):**
```env
REACT_APP_API_URL=http://localhost:8088/api/v1
```

4. **Run the development server:**
```bash
npm start
```

The application will open at `http://localhost:3000`

## 🎯 Usage

### 1. Connect to Database

1. Open the application at `http://localhost:3000`
2. Fill in your database connection details:
   - Host (e.g., `localhost`)
   - Port (default: `5432`)
   - Database name
   - Username
   - Password
3. (Optional) Check "Use Docker Container" if your database is in Docker
4. Click "Connect to Database"

### 2. Chat with Your Database

Once connected, you'll be taken to the chat interface where you can:

- Ask questions in natural language
- View generated SQL queries
- See results in formatted tables
- Switch between LLM providers (OpenAI, vLLM, Ollama)

**Example Questions:**
```
- Show me all users
- What are the top 10 products by sales?
- Find customers who made purchases last month
- Count the number of orders by status
- Show me the average order value by customer
```

### 3. Switch LLM Providers

Click the Settings icon in the header to switch between:
- **OpenAI**: GPT models (requires API key)
- **vLLM**: Self-hosted LLM inference
- **Ollama**: Local LLM models

## ⚙️ Configuration

### Backend Configuration (`app_config.yml`)

```yaml
# Server settings
server:
  port: 8088
  workers: 1
  host: "0.0.0.0"

# LLM Provider
llm:
  provider: "vllm"  # openai, vllm, or ollama

# OpenAI Configuration
openai:
  api_key: "your-api-key"
  model: "gpt-4o-mini-2024-07-18"
  temperature: 1.0
  max_tokens: 2048

# vLLM Configuration
vllm:
  api_url: "http://your-vllm-server:8000/v1/chat/completions"
  model: "/models"
  max_tokens: 2048
  temperature: 0.7

# Ollama Configuration
ollama:
  api_url: "http://localhost:11434/api/chat"
  model: "llama3.2"
  max_tokens: 2048
  temperature: 0.7

# CORS settings
cors:
  allow_origins: ["*"]
```

## 📡 API Endpoints

### Health Check
```
GET /api/v1/health
```

### Connect to Database
```
POST /api/v1/database/connect
Body: {
  "host": "localhost",
  "port": 5432,
  "database": "mydb",
  "username": "postgres",
  "password": "password",
  "use_docker": false,
  "docker_container": null
}
```

### Get Database Snapshot
```
GET /api/v1/database/snapshot
```

### Query Database
```
POST /api/v1/query
Body: {
  "question": "Show me all users",
  "conversation_history": []
}
```

### Configure LLM
```
POST /api/v1/llm/configure
Body: {
  "provider": "vllm"
}
```

## 🐳 Docker Support

The application supports connecting to PostgreSQL databases running in Docker containers. Simply check the "Use Docker Container" option and provide the container name.

## 🛠️ Development

### Backend Development

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8088
```

### Frontend Development

```bash
cd frontend
npm start
```

### Build for Production

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8088
```

**Frontend:**
```bash
cd frontend
npm run build
```

## 🧪 Testing

Test the API using curl:

```bash
# Health check
curl http://localhost:8088/api/v1/health

# Connect to database
curl -X POST http://localhost:8088/api/v1/database/connect \
  -H "Content-Type: application/json" \
  -d '{
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "username": "postgres",
    "password": "password"
  }'
```

## 🔒 Security Notes

- Database credentials are stored in memory only
- Use environment variables for API keys in production
- Enable authentication for production deployments
- Configure CORS properly for production
- Use HTTPS in production

## 📝 License

MIT License

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Support

For issues and questions, please open an issue on the project repository.

---

**Built with ❤️ using React, FastAPI, and modern LLMs**
