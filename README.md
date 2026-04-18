Front
npm i
npm run dev

Backend

How to run 
1.cd backend
2.docker compose up -d 
3.source venv_backend/bin/activate
4. Run FastAPI
uvicorn main:app --host 0.0.0.0 --port 8000

Database
✔ Install Docker
sudo apt update
sudo apt install docker.io docker-compose-plugin -y


Enable docker:

sudo systemctl enable docker
sudo systemctl start docker


Add user to docker group:

sudo usermod -aG docker $USER


Logout/login once.

📦 Project Structure
project/
│
├── docker-compose.yml
├── init.sql
├── postgrest.conf
├── backend/
└── README.md

⚙️ First Run (Important)
1️⃣ Clone project
git clone <your-repo>
cd project

2️⃣ Start containers
docker compose up -d


First startup may take a few minutes.

3️⃣ Check running containers
docker ps


Expected:

pg_db
postgrest
backend (if included)

🗄 Database Access
Connect locally from Jetson
Host: localhost
Port: 5432
User: api_user
Password: api_password
Database: postgres
Schema: api
