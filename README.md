# 📚 LMS — Learning Management System

A modern Learning Management System built with AI-powered features for an enhanced learning experience.

## 🚀 Features

- User authentication and role-based access control (Admin, Instructor, Student)
- Course creation and management
- AI-assisted content recommendations
- Progress tracking and analytics dashboard
- Assignment submission and grading system
- RESTful API backend

## 🛠️ Tech Stack

| Layer       | Technology           |
| ----------- | -------------------- |
| Backend     | FastAPI (Python)     |
| Frontend    | React.js / Next.js   |
| Database    | PostgreSQL           |
| Auth        | Azure AD / JWT       |
| AI Features | OpenAI / HuggingFace |
| Deployment  | Docker, Azure / GCP  |

## 📦 Installation

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL
- Docker (optional)

### Backend Setup

```bash
git clone https://github.com/yazeedmshayekh2/LMS.git
cd LMS
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/lms_db
SECRET_KEY=your_secret_key
OPENAI_API_KEY=your_openai_api_key
AZURE_CLIENT_ID=your_azure_client_id
```

### Run the Application

```bash
# Backend
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## 🐳 Docker

```bash
docker-compose up --build
```

## 📁 Project Structure

```
LMS/
├── app/
│   ├── api/          # Route handlers
│   ├── models/       # Database models
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic
│   └── main.py
├── frontend/
├── tests/
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📄 API Documentation

Once running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Yazeed Mshayekh**  
AI Engineer | Full-Stack Developer  
[GitHub](https://github.com/yazeedmshayekh2)
