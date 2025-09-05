import { Navigate } from "react-router-dom";
import { getToken } from "../lib/api";   // adjust your import

export default function Protected({ children }: { children: React.ReactNode }) {
  return getToken() ? children : <Navigate to="/login" replace />;
}
