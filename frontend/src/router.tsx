import { createBrowserRouter, Navigate } from "react-router-dom";
import AppLayout from "./layouts/AppLayout";
import Home from "./pages/Home";
import Accounts from "./pages/Accounts";
import Transactions from "./pages/Transactions";
import Budget from "./pages/Budget";
import Insights from "./pages/Insights";
import Profile from "./pages/Profile";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Protected from "./routes/Protected"; // if you already have this wrapper

export const router = createBrowserRouter([
  { path: "/login", element: <Login /> },
  { path: "/register", element: <Register /> },

  {
    element: (
      <Protected>
        <AppLayout />
      </Protected>
    ),
    children: [
      { index: true, element: <Navigate to="/home" replace /> },
      { path: "/home", element: <Home /> },
      { path: "/accounts", element: <Accounts /> },
      { path: "/transactions", element: <Transactions /> },
      { path: "/budget", element: <Budget /> },
      { path: "/insights", element: <Insights /> },
      { path: "/profile", element: <Profile /> },
    ],
  },

  { path: "*", element: <Navigate to="/home" replace /> },
]);
