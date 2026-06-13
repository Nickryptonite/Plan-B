# SideQuest MVP Deployment Guide

This guide describes how to deploy the SideQuest MVP (React frontend + FastAPI backend + MongoDB database) using free-tier services.

---

## Step 1: MongoDB Atlas Setup (Free Database)

1. **Sign Up / Log In**:
   - Go to [mongodb.com/atlas](https://www.mongodb.com/atlas) and sign up for a free account.
2. **Create a Database Cluster**:
   - Click **Create** to deploy a new database.
   - Choose the **M0** (Free) tier.
   - Select AWS (or any provider) and choose a region close to your users (e.g., Mumbai `ap-south-1` or N. Virginia `us-east-1`).
   - Click **Create**.
3. **Configure Database Access (Username/Password)**:
   - Create a database user. Give it a username (e.g., `sidequest_admin`) and generate a secure password.
   - Save the username and password in a safe place.
   - Click **Create User**.
4. **Configure Network Access**:
   - In the "IP Access List", choose **Allow Access from Anywhere** (adds `0.0.0.0/0`).
   - *Note: This is necessary because Render's free instances do not have static IP addresses.*
   - Click **Add IP Address**.
5. **Get Connection String**:
   - Once the cluster is deployed, click **Connect**.
   - Select **Drivers** under "Connect to your application".
   - Copy the connection string. It will look like this:
     ```
     mongodb+srv://sidequest_admin:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
     ```
   - Replace `<password>` with the database user's password you created earlier. (Also replace database name if requested, or keep it default; the backend will use the connection string + `DB_NAME` variable).

---

## Step 2: Render Backend Deployment (FastAPI)

1. **Sign Up / Log In**:
   - Go to [render.com](https://render.com) and sign up using your GitHub account.
2. **Deploy the Web Service**:
   - Click **New +** in the dashboard and select **Web Service**.
   - Connect your GitHub repository containing the SideQuest code.
3. **Configure the Service**:
   - **Name**: `sidequest-api`
   - **Environment**: `Python3` (or it will auto-detect)
   - **Root Directory**: (leave empty)
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
4. **Configure Environment Variables**:
   - Click the **Environment** tab on the left menu and add:
     - `MONGO_URL` = (your full MongoDB Atlas connection string from Step 1)
     - `DB_NAME` = `sidequest`
     - `ADMIN_EMAILS` = `niteshk582@gmail.com`
     - `CORS_ORIGINS` = `*` (We will restrict this to your Vercel URL once the frontend is deployed).
     - `APP_BASE_URL` = (We will set this to your Vercel URL once the frontend is deployed).
5. **Deploy**:
   - Click **Create Web Service**.
   - Wait for the build and deployment to complete. Render will display a URL like `https://sidequest-api.onrender.com`.
   - Test it by visiting `https://your-backend-url.onrender.com/api/`. You should see `{"message": "SideQuest API", "version": "1.0"}`.

---

## Step 3: Vercel Frontend Deployment (React)

1. **Sign Up / Log In**:
   - Go to [vercel.com](https://vercel.com) and sign up using your GitHub account.
2. **Import Project**:
   - Click **Add New** -> **Project**.
   - Import your GitHub repository.
3. **Configure the Build Settings**:
   - **Framework Preset**: `Create React App`
   - **Root Directory**: Select `frontend` (crucial!)
   - **Build Command**: `npm run build` or `yarn build`
   - **Output Directory**: `build`
4. **Configure Environment Variables**:
   - Expand the **Environment Variables** section and add:
     - `REACT_APP_BACKEND_URL` = `https://your-backend-url.onrender.com` (use the URL you got from Render in Step 2, without a trailing slash).
5. **Deploy**:
   - Click **Deploy**.
   - Vercel will build and deploy the React frontend. You will get a URL like `https://sidequest-frontend.vercel.app`.

---

## Step 4: Final Connection & Seeding

1. **Update Render Environment Variables**:
   - Go back to your Render Dashboard -> your `sidequest-api` service -> **Environment**.
   - Update `CORS_ORIGINS` = `https://your-vercel-app.vercel.app` (your Vercel frontend URL, no trailing slash).
   - Update `APP_BASE_URL` = `https://your-vercel-app.vercel.app`
   - Save changes. Render will automatically re-deploy the backend with the new configurations.
2. **Seed Data**:
   - The backend is configured to automatically seed the database on first boot if it is empty.
   - If you want to force a re-seed at any point, you can log in as `niteshk582@gmail.com` (the Admin email you provided), navigate to the Admin Dashboard, and click the seed options, OR send a POST request:
     ```bash
     curl -X POST "https://your-backend-url.onrender.com/api/seed?force=true" -H "Authorization: Bearer <session_token>"
     ```

---

## Step 5: Verification Checklist

1. **Waitlist Signup**: Try joining the waitlist on the landing page. It should succeed and return a referral link.
2. **Login**: Click "Login" on the top right. This redirects to the Google OAuth page. Complete sign-in.
3. **Role Selection**: You will be redirected to the role selection page. Pick `worker` or `client`.
4. **Client flow**:
   - Log in as a client (or admin).
   - Click **Post Quest**. Create a task.
   - Verify it appears on the public landing page / browse tab.
5. **Worker flow**:
   - Log in as a worker.
   - Apply to the task.
   - Go to **Active Quests**, write a submission text/url, and click submit.
6. **Admin Dashboard**:
   - Log in with `niteshk582@gmail.com`.
   - Go to `/admin`.
   - Verify that analytics, user tables, tasks, and waitlist tables load.
