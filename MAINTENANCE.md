# SideQuest MVP Development & Maintenance Guide

This guide describes how to run the project locally, make changes, and push updates to your production environment (Render + Vercel).

---

## 1. Local Development Setup

To run and test changes on your own computer before pushing them to production:

### Prerequisites
- Node.js (version 20.x is recommended)
- Python 3.10+
- A local MongoDB instance OR use your MongoDB Atlas connection string.

### Running the Backend Locally
1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the `backend` directory:
   ```env
   MONGO_URL=mongodb+srv://sidequest_Plan_b_Admin:<password>@cluster0.nyu7aw8.mongodb.net/sidequest?retryWrites=true&w=majority&appName=Cluster0
   DB_NAME=sidequest
   ADMIN_EMAILS=niteshk582@gmail.com
   CORS_ORIGINS=http://localhost:3000
   APP_BASE_URL=http://localhost:3000
   ```
5. Start the server:
   ```bash
   uvicorn server:app --reload --port 8000
   ```
   The API will be available at `http://localhost:8000`.

### Running the Frontend Locally
1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env` file in the `frontend` directory:
   ```env
   REACT_APP_BACKEND_URL=http://localhost:8000
   ```
4. Start the development server:
   ```bash
   npm start
   ```
   The React app will open automatically at `http://localhost:3000`.

---

## 2. Making Changes & Updating Production

Because your Render and Vercel services are linked directly to your GitHub repository, **any changes you push to the `main` branch will automatically deploy to production.**

### Step 1: Make your changes locally
Edit frontend or backend files as needed.

### Step 2: Commit and push to GitHub
Open your terminal at the root of the repository and run:
```bash
# Add all modified files
git add .

# Commit your changes
git commit -m "feat: described your changes here"

# Push to your repository
git push origin main
```

### Step 3: Monitor Deployments
- **Backend changes**: Render will detect the commit and automatically rebuild and redeploy. Monitor this on your [Render Dashboard](https://dashboard.render.com).
- **Frontend changes**: Vercel will detect the commit and automatically build and deploy. Monitor this on your [Vercel Dashboard](https://vercel.com).

---

## 3. Adding New Dependencies (Packages)

If you need to install new packages or libraries for the app:

### Adding Backend Packages (Python)
1. Install the package locally:
   ```bash
   pip install <package_name>
   ```
2. Update the `requirements.txt` file so Render knows to install it:
   ```bash
   pip freeze > requirements.txt
   ```
   *(Or manually add `<package_name>==<version>` to `backend/requirements.txt`)*.
3. Commit and push the updated `backend/requirements.txt`.

### Adding Frontend Packages (React)
1. Install the package in the `frontend` folder:
   ```bash
   cd frontend
   npm install <package_name>
   ```
   This will automatically update `frontend/package.json`.
2. Commit and push the updated `frontend/package.json`.

---

## 4. Resetting or Re-Seeding the Database

If you want to clear your test data and restore the clean 50 tasks + 30 submissions demo set:
1. Log in to [plan-b-nine.vercel.app](https://plan-b-nine.vercel.app) as the admin (`niteshk582@gmail.com`).
2. Go to the Admin dashboard.
3. You can trigger a database re-seed from there, or trigger it directly by making a POST request:
   ```bash
   curl -X POST "https://sidequest-api-o08u.onrender.com/api/seed?force=true" -H "Authorization: Bearer <your_session_token>"
   ```
